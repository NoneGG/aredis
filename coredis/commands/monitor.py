import asyncio
import threading
import weakref
from asyncio import CancelledError
from concurrent.futures import Future
from typing import TYPE_CHECKING, Callable, Optional

from coredis.exceptions import RedisError
from coredis.response.types import MonitorResult
from coredis.utils import nativestr

if TYPE_CHECKING:
    import coredis.client
    import coredis.connection


class Monitor:
    """
    Monitor is useful for handling the ``MONITOR`` command to the redis server.

    It can be used as an infinite async iterator::

        async for command in client.monitor():
            print(command.time, command.type, command.command, command.args)

    Alternatively, each command can be fetched explicitly::

        monitor = client.monitor()
        command1 = await monitor.get_command()
        command2 = await monitor.get_command()
        monitor.stop()

    """

    def __init__(self, client: "coredis.client.RedisConnection"):
        self._client: weakref.ReferenceType[
            "coredis.client.RedisConnection"
        ] = weakref.ref(client)
        self.encoding = client.encoding
        self.connection: Optional["coredis.connection.Connection"] = None
        self.monitoring = False

    @property
    def client(self) -> "coredis.client.RedisConnection":
        client = self._client()
        assert client
        return client

    def __aiter__(self) -> "Monitor":
        return self

    async def __anext__(self) -> MonitorResult:
        """
        Infinite iterator that streams back the next command processed by the
        monitored server.
        """
        return await self.get_command()

    async def get_command(self) -> MonitorResult:
        """
        Wait for the next command issued and return the details
        """
        await self.__start_monitor()
        assert self.connection
        response = await self.connection.read_response()
        if isinstance(response, bytes):
            response = response.decode(self.encoding)
        return MonitorResult.parse_response_string(response)

    async def stop(self):
        """
        Stop monitoring by issuing a ``RESET`` command
        and release the connection.
        """
        return await self.__stop_monitoring()

    def run_in_thread(
        self, response_handler=Callable[[MonitorResult], None], loop=None
    ) -> "MonitorThread":
        """
        Runs the monitor in a :class:`MonitorThread` and invokes :paramref:`response_handler`
        for every command received.

        To stop the processing call :meth:`MonitorThread.stop` on the instance
        returned by this method.

        """
        monitor_thread = MonitorThread(
            self, loop or asyncio.get_event_loop(), response_handler
        )
        monitor_thread.start()
        return monitor_thread

    async def __connect(self):
        if self.connection is None:
            self.connection = await self.client.connection_pool.get_connection()

    async def __start_monitor(self):
        if self.monitoring:
            return
        await self.__connect()
        assert self.connection
        await self.connection.send_command("MONITOR")
        response = nativestr(await self.connection.read_response())
        if not response == "OK":  # noqa
            raise RedisError(f"Failed to start MONITOR {response}")
        self.monitoring = True

    async def __stop_monitoring(self):
        if self.connection:
            await self.connection.send_command("RESET")
            response = await self.connection.read_response()
            if not nativestr(response) == "RESET":  # noqa
                raise RedisError("Failed to reset connection")
        self.__reset()

    def __reset(self):
        if self.connection:
            self.connection.disconnect()
            self.client.connection_pool.release(self.connection)
        self.monitoring = False
        self.connection = None


class MonitorThread(threading.Thread):
    """
    Thread to be used to run monitor
    """

    def __init__(
        self,
        monitor: "Monitor",
        loop: asyncio.events.AbstractEventLoop,
        response_handler: Callable[[MonitorResult], None],
    ):
        self._monitor = monitor
        self._loop = loop
        self._response_handler = response_handler
        self._future: Optional[Future[None]] = None
        super(MonitorThread, self).__init__()

    def run(self):
        self._future = asyncio.run_coroutine_threadsafe(self._run(), self._loop)

    async def _run(self):
        try:
            async for command in self._monitor:
                self._response_handler(command)
        except CancelledError:
            await self._monitor.stop()

    def stop(self):
        if self._future:
            self._future.cancel()
