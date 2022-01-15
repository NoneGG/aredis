import asyncio

from coredis.commands.cluster import ClusterCommandMixin
from coredis.commands.connection import (
    ClusterConnectionCommandMixin,
    ConnectionCommandMixin,
)
from coredis.commands.extra import ExtraCommandMixin
from coredis.commands.geo import GeoCommandMixin
from coredis.commands.hash import ClusterHashCommandMixin, HashCommandMixin
from coredis.commands.hyperlog import ClusterHyperLogCommandMixin, HyperLogCommandMixin
from coredis.commands.iter import ClusterIterCommandMixin, IterCommandMixin
from coredis.commands.keys import ClusterKeysCommandMixin, KeysCommandMixin
from coredis.commands.lists import ClusterListsCommandMixin, ListsCommandMixin
from coredis.commands.pubsub import CLusterPubSubCommandMixin, PubSubCommandMixin
from coredis.commands.scripting import (
    ClusterScriptingCommandMixin,
    ScriptingCommandMixin,
)
from coredis.commands.sentinel import ClusterSentinelCommands, SentinelCommandMixin
from coredis.commands.server import ClusterServerCommandMixin, ServerCommandMixin
from coredis.commands.sets import ClusterSetsCommandMixin, SetsCommandMixin
from coredis.commands.sorted_set import (
    ClusterSortedSetCommandMixin,
    SortedSetCommandMixin,
)
from coredis.commands.streams import StreamsCommandMixin
from coredis.commands.strings import ClusterStringsCommandMixin, StringsCommandMixin
from coredis.commands.transaction import (
    ClusterTransactionCommandMixin,
    TransactionCommandMixin,
)
from coredis.connection import RedisSSLContext, UnixDomainSocketConnection
from coredis.exceptions import (
    AskError,
    BusyLoadingError,
    ClusterDownError,
    ClusterError,
    ConnectionError,
    MovedError,
    RedisClusterException,
    TimeoutError,
    TryAgainError,
)
from coredis.pool import ClusterConnectionPool, ConnectionPool
from coredis.utils import (
    NodeFlag,
    blocked_command,
    clusterdown_wrapper,
    dict_merge,
    first_key,
)

mixins = [
    ClusterCommandMixin,
    ConnectionCommandMixin,
    ExtraCommandMixin,
    GeoCommandMixin,
    HashCommandMixin,
    HyperLogCommandMixin,
    KeysCommandMixin,
    IterCommandMixin,
    ListsCommandMixin,
    PubSubCommandMixin,
    ScriptingCommandMixin,
    SentinelCommandMixin,
    ServerCommandMixin,
    SetsCommandMixin,
    SortedSetCommandMixin,
    StringsCommandMixin,
    TransactionCommandMixin,
    StreamsCommandMixin,
]

cluster_mixins = [
    ClusterCommandMixin,
    ClusterStringsCommandMixin,
    ClusterServerCommandMixin,
    ClusterConnectionCommandMixin,
    CLusterPubSubCommandMixin,
    ClusterSentinelCommands,
    ClusterKeysCommandMixin,
    ClusterScriptingCommandMixin,
    ClusterHashCommandMixin,
    ClusterIterCommandMixin,
    ClusterSetsCommandMixin,
    ClusterSortedSetCommandMixin,
    ClusterTransactionCommandMixin,
    ClusterListsCommandMixin,
    ClusterHyperLogCommandMixin,
]


class StrictRedis(*mixins):
    """
    Implementation of the Redis protocol.

    This abstract class provides a Python interface to all Redis commands
    and an implementation of the Redis protocol.

    Connection and Pipeline derive from this, implementing how
    the commands are sent and received to the Redis server
    """

    RESPONSE_CALLBACKS = dict_merge(*[mixin.RESPONSE_CALLBACKS for mixin in mixins])

    @classmethod
    def from_url(cls, url, db=None, **kwargs):
        """
        Return a Redis client object configured from the given URL, which must
        use either `the ``redis://`` scheme
        <http://www.iana.org/assignments/uri-schemes/prov/redis>`_ for RESP
        connections or the ``unix://`` scheme for Unix domain sockets.

        For example:

        redis://[:password]@localhost:6379/0
        unix://[:password]@/path/to/socket.sock?db=0

        There are several ways to specify a database number. The parse function
        will return the first specified option:
        1. A ``db`` querystring option, e.g. redis://localhost?db=0
        2. If using the redis:// scheme, the path argument of the url, e.g.
        redis://localhost/0
        3. The ``db`` argument to this function.

        If none of these options are specified, db=0 is used.


        Any additional querystring arguments and keyword arguments will be
        passed along to the ConnectionPool class's initializer. In the case
        of conflicting arguments, querystring arguments always win.
        """
        connection_pool = ConnectionPool.from_url(url, db=db, **kwargs)

        return cls(connection_pool=connection_pool)

    def __init__(
        self,
        host="localhost",
        port=6379,
        db=0,
        password=None,
        stream_timeout=None,
        connect_timeout=None,
        connection_pool=None,
        unix_socket_path=None,
        encoding="utf-8",
        decode_responses=False,
        ssl=False,
        ssl_context=None,
        ssl_keyfile=None,
        ssl_certfile=None,
        ssl_cert_reqs=None,
        ssl_ca_certs=None,
        max_connections=None,
        retry_on_timeout=False,
        max_idle_time=0,
        idle_check_interval=1,
        loop=None,
        **kwargs
    ):
        if not connection_pool:
            kwargs = {
                "db": db,
                "password": password,
                "encoding": encoding,
                "stream_timeout": stream_timeout,
                "connect_timeout": connect_timeout,
                "max_connections": max_connections,
                "retry_on_timeout": retry_on_timeout,
                "decode_responses": decode_responses,
                "max_idle_time": max_idle_time,
                "idle_check_interval": idle_check_interval,
                "loop": loop,
            }
            # based on input, setup appropriate connection args

            if unix_socket_path is not None:
                kwargs.update(
                    {
                        "path": unix_socket_path,
                        "connection_class": UnixDomainSocketConnection,
                    }
                )
            else:
                # TCP specific options
                kwargs.update({"host": host, "port": port})

                if ssl_context is not None:
                    kwargs["ssl_context"] = ssl_context
                elif ssl:
                    ssl_context = RedisSSLContext(
                        ssl_keyfile, ssl_certfile, ssl_cert_reqs, ssl_ca_certs
                    ).get()
                    kwargs["ssl_context"] = ssl_context
            connection_pool = ConnectionPool(**kwargs)
        self.connection_pool = connection_pool
        self._use_lua_lock = None

        self.response_callbacks = self.__class__.RESPONSE_CALLBACKS.copy()

    def __repr__(self):
        return "{}<{}>".format(type(self).__name__, repr(self.connection_pool))

    def set_response_callback(self, command, callback):
        """Sets a custom Response Callback"""
        self.response_callbacks[command] = callback

    # COMMAND EXECUTION AND PROTOCOL PARSING
    async def execute_command(self, *args, **options):
        """Executes a command and returns a parsed response"""
        pool = self.connection_pool
        command_name = args[0]
        connection = pool.get_connection()
        try:
            await connection.send_command(*args)

            return await self.parse_response(connection, command_name, **options)
        except asyncio.CancelledError:
            # do not retry when coroutine is cancelled
            connection.disconnect()
            raise
        except (ConnectionError, TimeoutError) as e:
            connection.disconnect()

            if not connection.retry_on_timeout and isinstance(e, TimeoutError):
                raise
            await connection.send_command(*args)

            return await self.parse_response(connection, command_name, **options)
        finally:
            pool.release(connection)

    async def parse_response(self, connection, command_name, **options):
        """Parses a response from the Redis server"""
        response = await connection.read_response()

        if command_name in self.response_callbacks:
            callback = self.response_callbacks[command_name]

            return callback(response, **options)

        return response

    async def pipeline(self, transaction=True, shard_hint=None):
        """
        Returns a new pipeline object that can queue multiple commands for
        later execution. ``transaction`` indicates whether all commands
        should be executed atomically. Apart from making a group of operations
        atomic, pipelines are useful for reducing the back-and-forth overhead
        between the client and server.
        """
        from coredis.pipeline import StrictPipeline

        pipeline = StrictPipeline(
            self.connection_pool, self.response_callbacks, transaction, shard_hint
        )
        await pipeline.reset()

        return pipeline


class StrictRedisCluster(StrictRedis, *cluster_mixins):
    """
    Redis cluster client
    """

    RedisClusterRequestTTL = 16
    NODES_FLAGS = dict_merge(
        *[
            mixin.NODES_FLAGS
            for mixin in cluster_mixins
            if hasattr(mixin, "NODES_FLAGS")
        ]
    )
    RESULT_CALLBACKS = dict_merge(
        *[
            mixin.RESULT_CALLBACKS
            for mixin in cluster_mixins
            if hasattr(mixin, "RESULT_CALLBACKS")
        ]
    )

    def __init__(
        self,
        host=None,
        port=None,
        startup_nodes=None,
        max_connections=32,
        max_connections_per_node=False,
        readonly=False,
        reinitialize_steps=None,
        skip_full_coverage_check=False,
        nodemanager_follow_cluster=False,
        **kwargs
    ):
        """
        :param host: Can be used to point to a startup node
        :param port: Can be used to point to a startup node
        :param startup_nodes: List of nodes that initial bootstrapping can be done
         from
        :param max_connections: Maximum number of connections that should be kept open at one time
        :param readonly: enable READONLY mode. You can read possibly stale data from slave.
        :param skip_full_coverage_check: Skips the check of cluster-require-full-coverage config,
         useful for clusters without the CONFIG command (like aws)
        :param nodemanager_follow_cluster: The node manager will during initialization try the
         last set of nodes that it was operating on. This will allow the client to drift along
         side the cluster if the cluster nodes move around alot.
        """
        # Tweaks to StrictRedis client arguments when running in cluster mode

        if "db" in kwargs:
            raise RedisClusterException(
                "Argument 'db' is not possible to use in cluster mode"
            )

        if "connection_pool" in kwargs:
            pool = kwargs.pop("connection_pool")
        else:
            startup_nodes = [] if startup_nodes is None else startup_nodes

            # Support host/port as argument

            if host:
                startup_nodes.append({"host": host, "port": port if port else 7000})
            pool = ClusterConnectionPool(
                startup_nodes=startup_nodes,
                max_connections=max_connections,
                reinitialize_steps=reinitialize_steps,
                max_connections_per_node=max_connections_per_node,
                skip_full_coverage_check=skip_full_coverage_check,
                nodemanager_follow_cluster=nodemanager_follow_cluster,
                readonly=readonly,
                **kwargs
            )

        super(StrictRedisCluster, self).__init__(connection_pool=pool, **kwargs)

        self.refresh_table_asap = False
        self.nodes_flags = self.__class__.NODES_FLAGS.copy()
        self.result_callbacks = self.__class__.RESULT_CALLBACKS.copy()
        self.response_callbacks = self.__class__.RESPONSE_CALLBACKS.copy()

    @classmethod
    def from_url(cls, url, db=None, skip_full_coverage_check=False, **kwargs):
        """
        Return a Redis client object configured from the given URL, which must
        use either the ``redis://`` scheme
        `<http://www.iana.org/assignments/uri-schemes/prov/redis>`_ for RESP
        connections or the ``unix://`` scheme for Unix domain sockets.
        For example:

            - ``redis://[:password]@localhost:6379/0``
            - ``unix://[:password]@/path/to/socket.sock?db=0``

        There are several ways to specify a database number. The parse function
        will return the first specified option:

            #. A ``db`` querystring option, e.g. ``redis://localhost?db=0``
            #. If using the ``redis://`` scheme, the path argument of the url, e.g.
               ``redis://localhost/0``
            #. The ``db`` argument to this function.

        If none of these options are specified, db=0 is used.

        Any additional querystring arguments and keyword arguments will be
        passed along to the ConnectionPool class's initializer. In the case
        of conflicting arguments, querystring arguments always win.
        """
        connection_pool = ClusterConnectionPool.from_url(
            url, db=db, skip_full_coverage_check=skip_full_coverage_check, **kwargs
        )

        return cls(connection_pool=connection_pool)

    def __repr__(self):
        servers = list(
            {
                "{0}:{1}".format(info["host"], info["port"])
                for info in self.connection_pool.nodes.startup_nodes
            }
        )
        servers.sort()

        return "{0}<{1}>".format(type(self).__name__, ", ".join(servers))

    def set_result_callback(self, command, callback):
        "Sets a custom Result Callback"
        self.result_callbacks[command] = callback

    def _determine_slot(self, *args):
        """Figures out what slot based on command and args"""

        if len(args) <= 1:
            raise RedisClusterException(
                "No way to dispatch this command to Redis Cluster. Missing key."
            )
        command = args[0]

        if command in ["EVAL", "EVALSHA"]:
            numkeys = args[2]
            keys = args[3 : 3 + numkeys]
            slots = {self.connection_pool.nodes.keyslot(key) for key in keys}

            if len(slots) != 1:
                raise RedisClusterException(
                    "{0} - all keys must map to the same key slot".format(command)
                )

            return slots.pop()
        elif command in ("XREAD", "XREADGROUP"):
            try:
                idx = args.index("STREAMS") + 1
            except ValueError:
                raise RedisClusterException(
                    "{0} arguments do not contain STREAMS operand".format(command)
                )
            key = args[idx]
        elif command in ("XGROUP", "XINFO"):
            key = args[2]
        else:
            key = args[1]

        return self.connection_pool.nodes.keyslot(key)

    def _merge_result(self, command, res, **kwargs):
        """
        `res` is a dict with the following structure Dict(NodeName, CommandResult)
        """

        if command in self.result_callbacks:
            return self.result_callbacks[command](res, **kwargs)

        # Default way to handle result

        return first_key(res)

    def determine_node(self, *args, **kwargs):
        """
        TODO: document
        """
        command = args[0]
        node_flag = self.nodes_flags.get(command)

        if node_flag == NodeFlag.BLOCKED:
            return blocked_command(self, command)
        elif node_flag == NodeFlag.RANDOM:
            return [self.connection_pool.nodes.random_node()]
        elif node_flag == NodeFlag.ALL_MASTERS:
            return self.connection_pool.nodes.all_masters()
        elif node_flag == NodeFlag.ALL_NODES:
            return self.connection_pool.nodes.all_nodes()
        elif node_flag == NodeFlag.SLOT_ID:
            # if node flag of command is SLOT_ID
            # `slot_id` should is assumed in kwargs
            slot = kwargs.get("slot_id")

            if not slot:
                raise RedisClusterException(
                    "slot_id is needed to execute command {}".format(command)
                )

            return [self.connection_pool.nodes.node_from_slot(slot)]
        else:
            return None

    @clusterdown_wrapper
    async def execute_command(self, *args, **kwargs):
        """
        Sends a command to a node in the cluster
        """

        if not self.connection_pool.initialized:
            await self.connection_pool.initialize()

        if not args:
            raise RedisClusterException("Unable to determine command to use")

        command = args[0]

        node = self.determine_node(*args, **kwargs)

        if node:
            return await self.execute_command_on_nodes(node, *args, **kwargs)

        # If set externally we must update it before calling any commands

        if self.refresh_table_asap:
            await self.connection_pool.nodes.initialize()
            self.refresh_table_asap = False

        redirect_addr = None
        asking = False

        try_random_node = False
        slot = self._determine_slot(*args)
        ttl = int(self.RedisClusterRequestTTL)

        while ttl > 0:
            ttl -= 1

            if asking:
                node = self.connection_pool.nodes.nodes[redirect_addr]
                r = self.connection_pool.get_connection_by_node(node)
            elif try_random_node:
                r = self.connection_pool.get_random_connection()
                try_random_node = False
            else:
                if self.refresh_table_asap:
                    # MOVED
                    node = self.connection_pool.get_master_node_by_slot(slot)
                else:
                    node = self.connection_pool.get_node_by_slot(slot)
                r = self.connection_pool.get_connection_by_node(node)

            try:
                if asking:
                    await r.send_command("ASKING")
                    await self.parse_response(r, "ASKING", **kwargs)
                    asking = False

                await r.send_command(*args)

                return await self.parse_response(r, command, **kwargs)
            except (RedisClusterException, BusyLoadingError, asyncio.CancelledError):
                raise
            except (ConnectionError, TimeoutError):
                try_random_node = True

                if ttl < self.RedisClusterRequestTTL / 2:
                    await asyncio.sleep(0.1)
            except ClusterDownError as e:
                self.connection_pool.disconnect()
                self.connection_pool.reset()
                self.refresh_table_asap = True

                raise e
            except MovedError as e:
                # Reinitialize on ever x number of MovedError.
                # This counter will increase faster when the same client object
                # is shared between multiple threads. To reduce the frequency you
                # can set the variable 'reinitialize_steps' in the constructor.
                self.refresh_table_asap = True
                await self.connection_pool.nodes.increment_reinitialize_counter()

                node = self.connection_pool.nodes.set_node(
                    e.host, e.port, server_type="master"
                )
                self.connection_pool.nodes.slots[e.slot_id][0] = node
            except TryAgainError:
                if ttl < self.RedisClusterRequestTTL / 2:
                    await asyncio.sleep(0.05)
            except AskError as e:
                redirect_addr, asking = "{0}:{1}".format(e.host, e.port), True
            finally:
                self.connection_pool.release(r)

        raise ClusterError("TTL exhausted.")

    async def execute_command_on_nodes(self, nodes, *args, **kwargs):
        command = args[0]
        res = {}

        for node in nodes:
            connection = self.connection_pool.get_connection_by_node(node)

            # copy from redis-py
            try:
                await connection.send_command(*args)
                res[node["name"]] = await self.parse_response(
                    connection, command, **kwargs
                )
            except asyncio.CancelledError:
                # do not retry when coroutine is cancelled
                connection.disconnect()
                raise
            except (ConnectionError, TimeoutError) as e:
                connection.disconnect()

                if not connection.retry_on_timeout and isinstance(e, TimeoutError):
                    raise

                await connection.send_command(*args)
                res[node["name"]] = await self.parse_response(
                    connection, command, **kwargs
                )
            finally:
                self.connection_pool.release(connection)

        return self._merge_result(command, res, **kwargs)

    async def pipeline(self, transaction=None, shard_hint=None, watches=None):
        """
        Pipelines do not work in cluster mode the same way they do in normal mode.
        Create a clone of this object so that simulating pipelines will work correctly.

        Each command will be called directly when used and when calling execute() will only
        return the result stack. Cluster transaction can only be run with commands in the same
        node, otherwise error will be raised.
        """
        await self.connection_pool.initialize()

        if shard_hint:
            raise RedisClusterException("shard_hint is deprecated in cluster mode")

        from coredis.pipeline import StrictClusterPipeline

        return StrictClusterPipeline(
            connection_pool=self.connection_pool,
            startup_nodes=self.connection_pool.nodes.startup_nodes,
            result_callbacks=self.result_callbacks,
            response_callbacks=self.response_callbacks,
            transaction=transaction,
            watches=watches,
        )
