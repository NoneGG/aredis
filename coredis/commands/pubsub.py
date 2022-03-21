import asyncio
import threading
from asyncio import CancelledError
from concurrent.futures import Future
from typing import TYPE_CHECKING, Dict, Optional, Union

from coredis.exceptions import ConnectionError, PubSubError, TimeoutError
from coredis.utils import iteritems, iterkeys, list_or_args, nativestr

if TYPE_CHECKING:
    import coredis.client
    import coredis.connection
    import coredis.pool


class PubSub:
    """
    PubSub provides publish, subscribe and listen support to Redis channels.

    After subscribing to one or more channels, the listen() method will block
    until a message arrives on one of the subscribed channels. That message
    will be returned and it's safe to start listening again.
    """

    PUBLISH_MESSAGE_TYPES = ("message", "pmessage")
    UNSUBSCRIBE_MESSAGE_TYPES = ("unsubscribe", "punsubscribe")

    def __init__(
        self,
        connection_pool: "coredis.pool.ConnectionPool",
        ignore_subscribe_messages=False,
    ):
        self.connection_pool = connection_pool
        self.ignore_subscribe_messages = ignore_subscribe_messages
        self.connection: Optional["coredis.connection.Connection"] = None
        self.reset()

    async def _ensure_encoding(self):
        if hasattr(self, "encoding"):
            return

        conn = await self.connection_pool.get_connection("pubsub")
        try:
            self.encoding = conn.encoding
            self.decode_responses = conn.decode_responses
        finally:
            self.connection_pool.release(conn)

    def __del__(self):
        try:
            # if this object went out of scope prior to shutting down
            # subscriptions, close the connection manually before
            # returning it to the connection pool
            self.reset()
        except Exception:
            pass

    def reset(self):
        if self.connection:
            self.connection.disconnect()
            self.connection.clear_connect_callbacks()
            self.connection_pool.release(self.connection)
            self.connection = None
        self.channels = {}
        self.patterns = {}

    def close(self):
        self.reset()

    async def on_connect(self, _):
        """Re-subscribe to any channels and patterns previously subscribed to"""

        if self.channels:
            channels = {}

            for k, v in iteritems(self.channels):
                if not self.decode_responses:
                    k = k.decode(self.encoding)
                channels[k] = v
            await self.subscribe(**channels)

        if self.patterns:
            patterns = {}

            for k, v in iteritems(self.patterns):
                if not self.decode_responses:
                    k = k.decode(self.encoding)
                patterns[k] = v
            await self.psubscribe(**patterns)

    def encode(self, value):
        """
        Encodes the value so that it's identical to what we'll read off the
        connection
        """

        if self.decode_responses and isinstance(value, bytes):
            value = value.decode(self.encoding)
        elif not self.decode_responses and isinstance(value, str):
            value = value.encode(self.encoding)

        return value

    @property
    def subscribed(self) -> bool:
        """Indicates if there are subscriptions to any channels or patterns"""

        return bool(self.channels or self.patterns)

    async def execute_command(self, *args, **kwargs):
        """Executes a publish/subscribe command"""

        # NOTE: don't parse the response in this function -- it could pull a
        # legitimate message off the stack if the connection is already
        # subscribed to one or more channels

        await self._ensure_encoding()

        if self.connection is None:
            self.connection = await self.connection_pool.get_connection()
            self.connection.register_connect_callback(self.on_connect)
        assert self.connection
        await self._execute(self.connection, self.connection.send_command, *args)

    async def _execute(self, connection, command, *args):
        try:
            return await command(*args)
        except asyncio.CancelledError:
            # do not retry if coroutine is cancelled

            if await connection.can_read():
                # disconnect if buffer is not empty in case of error
                # when connection is reused
                connection.disconnect()

            raise
        except (ConnectionError, TimeoutError) as e:
            connection.disconnect()

            if not connection.retry_on_timeout and isinstance(e, TimeoutError):
                raise
            # Connect manually here. If the Redis server is down, this will
            # fail and raise a ConnectionError as desired.
            await connection.connect()
            # the ``on_connect`` callback should haven been called by the
            # connection to resubscribe us to any channels and patterns we were
            # previously listening to

            return await command(*args)

    async def parse_response(self, block=True, timeout: Union[int, float] = 0):
        """Parses the response from a publish/subscribe command"""
        connection = self.connection

        if connection is None:
            raise RuntimeError(
                "pubsub connection not set: "
                "did you forget to call subscribe() or psubscribe()?"
            )
        coro = self._execute(connection, connection.read_response)

        if not block and timeout > 0:
            try:
                return await asyncio.wait_for(coro, timeout)
            except Exception:
                return None

        return await coro

    async def psubscribe(self, *args, **kwargs):
        """
        Subscribes to channel patterns. Patterns supplied as keyword arguments
        expect a pattern name as the key and a callable as the value. A
        pattern's callable will be invoked automatically when a message is
        received on that pattern rather than producing a message via
        ``listen()``.
        """
        await self._ensure_encoding()

        if args:
            args = list_or_args(args[0], args[1:])
        new_patterns = {}
        new_patterns.update(dict.fromkeys(map(self.encode, args)))

        for pattern, handler in iteritems(kwargs):
            new_patterns[self.encode(pattern)] = handler
        ret_val = await self.execute_command("PSUBSCRIBE", *iterkeys(new_patterns))
        # update the patterns dict AFTER we send the command. we don't want to
        # subscribe twice to these patterns, once for the command and again
        # for the reconnection.
        self.patterns.update(new_patterns)

        return ret_val

    async def punsubscribe(self, *args):
        """
        Unsubscribes from the supplied patterns. If empy, unsubscribe from
        all patterns.
        """
        await self._ensure_encoding()

        if args:
            args = list_or_args(args[0], args[1:])
        return await self.execute_command("PUNSUBSCRIBE", *args)

    async def subscribe(self, *args, **kwargs):
        """
        Subscribes to channels. Channels supplied as keyword arguments expect
        a channel name as the key and a callable as the value. A channel's
        callable will be invoked automatically when a message is received on
        that channel rather than producing a message via ``listen()`` or
        ``get_message()``.
        """

        await self._ensure_encoding()

        if args:
            args = list_or_args(args[0], args[1:])
        new_channels = {}
        new_channels.update(dict.fromkeys(map(self.encode, args)))

        for channel, handler in iteritems(kwargs):
            new_channels[self.encode(channel)] = handler
        ret_val = await self.execute_command("SUBSCRIBE", *iterkeys(new_channels))
        # update the channels dict AFTER we send the command. we don't want to
        # subscribe twice to these channels, once for the command and again
        # for the reconnection.
        self.channels.update(new_channels)

        return ret_val

    async def unsubscribe(self, *args):
        """
        Unsubscribes from the supplied channels. If empty, unsubscribe from
        all channels
        """

        await self._ensure_encoding()

        if args:
            args = list_or_args(args[0], args[1:])

        return await self.execute_command("UNSUBSCRIBE", *args)

    async def listen(self):
        """
        Listens for messages on channels this client has been subscribed to
        """

        if self.subscribed:
            return self.handle_message(await self.parse_response(block=True))

    async def get_message(
        self, ignore_subscribe_messages=False, timeout: Union[int, float] = 0
    ):
        """
        Gets the next message if one is available, otherwise None.

        If timeout is specified, the system will wait for `timeout` seconds
        before returning. Timeout should be specified as a floating point
        number.
        """
        response = await self.parse_response(block=False, timeout=timeout)

        if response:
            return self.handle_message(response, ignore_subscribe_messages)

        return None

    def handle_message(
        self, response, ignore_subscribe_messages=False
    ) -> Optional[Dict]:
        """
        Parses a pub/sub message. If the channel or pattern was subscribed to
        with a message handler, the handler is invoked instead of a parsed
        message being returned.
        """
        message_type = nativestr(response[0])

        if message_type == "pmessage":
            message = {
                "type": message_type,
                "pattern": response[1],
                "channel": response[2],
                "data": response[3],
            }
        else:
            message = {
                "type": message_type,
                "pattern": None,
                "channel": response[1],
                "data": response[2],
            }

        # if this is an unsubscribe message, remove it from memory
        if message_type in self.UNSUBSCRIBE_MESSAGE_TYPES:
            if message_type == "punsubscribe":
                subscribed_dict = self.patterns
            else:
                subscribed_dict = self.channels
            try:
                del subscribed_dict[message["channel"]]
            except KeyError:
                pass

        if message_type in self.PUBLISH_MESSAGE_TYPES:
            if message_type == "pmessage":
                handler = self.patterns.get(message["pattern"], None)
            else:
                handler = self.channels.get(message["channel"], None)

            if handler:
                handler(message)
                return None
        else:
            # this is a subscribe/unsubscribe message. ignore if we don't
            # want them

            if ignore_subscribe_messages or self.ignore_subscribe_messages:
                return None

        return message

    def run_in_thread(self, poll_timeout=1.0) -> "PubSubWorkerThread":
        """
        Run the listeners in a thread. For each message received on a
        subscribed channel or pattern the registered handlers will be invoked.

        To stop listening invoke :meth:`PubSubWorkerThread.stop` on the returned
        instead of :class:`PubSubWorkerThread`.
        """
        for channel, handler in iteritems(self.channels):
            if handler is None:
                raise PubSubError(
                    "Channel: '{}' has no handler registered".format(channel)
                )

        for pattern, handler in iteritems(self.patterns):
            if handler is None:
                raise PubSubError(
                    "Pattern: '{}' has no handler registered".format(pattern)
                )
        thread = PubSubWorkerThread(
            self, poll_timeout=poll_timeout, loop=asyncio.get_running_loop()
        )
        thread.start()

        return thread


class PubSubWorkerThread(threading.Thread):
    def __init__(
        self, pubsub: "PubSub", loop: asyncio.events.AbstractEventLoop, poll_timeout=1.0
    ):
        super(PubSubWorkerThread, self).__init__()
        self._pubsub = pubsub
        self._poll_timeout = poll_timeout
        self._running = False
        self._loop = loop or asyncio.get_running_loop()
        self._future: Optional[Future[None]] = None

    async def _run(self):
        pubsub = self._pubsub
        try:
            while pubsub.subscribed:
                await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=self._poll_timeout
                )
        except CancelledError:
            await asyncio.gather(pubsub.unsubscribe(), pubsub.punsubscribe())
            pubsub.close()
            self._running = False

    def run(self):
        if self._running:
            return
        self._running = True
        self._future = asyncio.run_coroutine_threadsafe(self._run(), self._loop)

    def stop(self):
        if self._future:
            self._future.cancel()


class ClusterPubSub(PubSub):
    """Wrappers for the PubSub class"""

    def __init__(self, *args, **kwargs):
        super(ClusterPubSub, self).__init__(*args, **kwargs)

    async def execute_command(self, *args, **kwargs):
        """
        Executes a publish/subscribe command.

        NOTE: The code was initially taken from redis-py and tweaked to make it work within a
        cluster.
        """
        # NOTE: don't parse the response in this function -- it could pull a
        # legitimate message off the stack if the connection is already
        # subscribed to one or more channels
        await self.connection_pool.initialize()

        if self.connection is None:
            self.connection = await self.connection_pool.get_connection(
                "pubsub",
                channel=args[1],
            )
            # register a callback that re-subscribes to any channels we
            # were listening to when we were disconnected
            self.connection.register_connect_callback(self.on_connect)

        assert self.connection
        await self._execute(self.connection, self.connection.send_command, *args)
