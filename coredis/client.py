import asyncio
import contextlib
import inspect
from abc import ABCMeta
from ssl import SSLContext
from typing import (
    Any,
    AnyStr,
    AsyncGenerator,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from coredis.commands import ClusterCommandConfig, CommandGroup, redis_command
from coredis.commands.core import CoreCommands
from coredis.commands.extra import ExtraCommandMixin
from coredis.commands.sentinel import SentinelCommands
from coredis.commands.transaction import TransactionCommandMixin
from coredis.connection import Connection, RedisSSLContext, UnixDomainSocketConnection
from coredis.exceptions import (
    AskError,
    BusyLoadingError,
    ClusterDownError,
    ClusterError,
    ConnectionError,
    MovedError,
    RedisClusterException,
    ResponseError,
    TimeoutError,
    TryAgainError,
)
from coredis.pool import ClusterConnectionPool, ConnectionPool
from coredis.response.callbacks import SimpleStringCallback
from coredis.tokens import PureToken
from coredis.typing import (
    CommandArgList,
    KeyT,
    ParamSpec,
    SupportsWatch,
    ValueT,
    add_runtime_checks,
)
from coredis.utils import (
    NodeFlag,
    blocked_command,
    clusterdown_wrapper,
    first_key,
    iteritems,
    nativestr,
)
from coredis.validators import mutually_inclusive_parameters

P = ParamSpec("P")
R = TypeVar("R")


class ClusterMeta(ABCMeta):
    NODES_FLAGS: Dict[str, NodeFlag]
    RESPONSE_CALLBACKS: Dict[str, Callable]
    RESULT_CALLBACKS: Dict[str, Callable]

    def __new__(cls, name, bases, dct):
        kls = super(ClusterMeta, cls).__new__(cls, name, bases, dct)
        methods = dict(k for k in inspect.getmembers(kls) if inspect.isfunction(k[1]))

        for name, method in methods.items():
            if cmd := getattr(method, "__coredis_command", None):
                if cmd.cluster.flag:
                    kls.NODES_FLAGS[cmd.command] = cmd.cluster.flag

                if cmd.response_callback:
                    kls.RESPONSE_CALLBACKS[cmd.command] = cmd.response_callback
                if cmd.cluster.multi_node:
                    kls.RESULT_CALLBACKS[cmd.command] = cmd.cluster.combine or (
                        lambda r, **_: r
                    )
                else:
                    kls.RESULT_CALLBACKS[cmd.command] = lambda response, **_: list(
                        response.values()
                    ).pop()
                if cmd.readonly:
                    ConnectionPool.READONLY_COMMANDS.add(cmd.command)
        return kls


class RedisMeta(ABCMeta):
    RESPONSE_CALLBACKS: Dict

    def __new__(cls, name, bases, dct):
        kls = super(RedisMeta, cls).__new__(cls, name, bases, dct)
        methods = dict(k for k in inspect.getmembers(kls) if inspect.isfunction(k[1]))

        for name, method in methods.items():
            if cmd := getattr(method, "__coredis_command", None):
                if cmd.response_callback:
                    kls.RESPONSE_CALLBACKS[cmd.command] = cmd.response_callback
                setattr(kls, name, add_runtime_checks(method))
        return kls


class NodeProxy:
    class Capture:
        def __init__(self, method: str, nodes: List["Redis"]):
            self.method = method
            self.nodes = nodes

        async def __call__(self, *args, **kwargs):
            awaitables = []
            for node in self.nodes:
                awaitables.append(getattr(node, self.method)(*args, **kwargs))
            responses = await asyncio.gather(*awaitables)
            return dict(zip(self.nodes, responses))

    def __init__(self, nodes):
        self.nodes = nodes

    def __getattribute__(self, name):
        nodes = object.__getattribute__(self, "nodes")
        capture = object.__getattribute__(self, "Capture")
        return capture(name, nodes)


class RedisConnection:
    def __init__(
        self,
        host: Optional[str] = "localhost",
        port: Optional[int] = 6379,
        db: int = 0,
        username: Optional[str] = None,
        password: Optional[str] = None,
        stream_timeout: Optional[int] = None,
        connect_timeout: Optional[int] = None,
        connection_pool: Optional[ConnectionPool] = None,
        unix_socket_path: Optional[str] = None,
        encoding: str = "utf-8",
        decode_responses: bool = False,
        ssl: bool = False,
        ssl_context: Optional[SSLContext] = None,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_cert_reqs: Optional[str] = None,
        ssl_ca_certs: Optional[str] = None,
        max_connections: Optional[int] = None,
        retry_on_timeout: bool = False,
        max_idle_time: int = 0,
        idle_check_interval: int = 1,
        client_name: Optional[str] = None,
        **kwargs,
    ):
        if not connection_pool:
            kwargs = {
                "db": db,
                "username": username,
                "password": password,
                "encoding": encoding,
                "stream_timeout": stream_timeout,
                "connect_timeout": connect_timeout,
                "max_connections": max_connections,
                "retry_on_timeout": retry_on_timeout,
                "decode_responses": decode_responses,
                "max_idle_time": max_idle_time,
                "idle_check_interval": idle_check_interval,
                "client_name": client_name,
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

    def __await__(self):
        async def closure():
            await self.connection_pool.initialize()
            return self

        return closure().__await__()

    def __repr__(self):
        return "{}<{}>".format(type(self).__name__, repr(self.connection_pool))


class ResponseParser:
    RESPONSE_CALLBACKS: Dict = {}

    def __init__(self, **kwargs):
        self.response_callbacks: Dict[
            str, Callable
        ] = self.__class__.RESPONSE_CALLBACKS.copy()
        super(ResponseParser, self).__init__(**kwargs)

    async def parse_response(
        self, connection: Connection, command_name: str, **options: Any
    ) -> Any:
        """Parses a response from the Redis server"""
        response = await connection.read_response(decode=options.get("decode"))

        if command_name in self.response_callbacks:
            callback = self.response_callbacks[command_name]

            return callback(response, **options)

        return response


class AbstractRedis(
    Generic[AnyStr],
    CoreCommands[AnyStr],
    ExtraCommandMixin,
    SentinelCommands[AnyStr],
    TransactionCommandMixin[AnyStr],
):
    """
    Async Redis client
    """

    async def scan_iter(
        self, match: Optional[ValueT] = None, count: Optional[int] = None
    ):
        """
        Make an iterator using the SCAN command so that the client doesn't
        need to remember the cursor position.
        """
        cursor = None

        while cursor != 0:
            cursor, data = await self.scan(cursor=cursor, match=match, count=count)

            for item in data:
                yield item

    async def sscan_iter(
        self,
        key: KeyT,
        match: Optional[ValueT] = None,
        count: Optional[int] = None,
    ):
        """
        Make an iterator using the SSCAN command so that the client doesn't
        need to remember the cursor position.
        """
        cursor = None

        while cursor != 0:
            cursor, data = await self.sscan(
                key, cursor=cursor, match=match, count=count
            )

            for item in data:
                yield item

    async def hscan_iter(
        self,
        key: KeyT,
        match: Optional[ValueT] = None,
        count: Optional[int] = None,
    ) -> AsyncGenerator[Tuple[AnyStr, AnyStr], None]:
        """
        Make an iterator using the HSCAN command so that the client doesn't
        need to remember the cursor position.
        """
        cursor = None

        while cursor != 0:
            cursor, data = await self.hscan(
                key, cursor=cursor, match=match, count=count
            )

            for item in data.items():
                yield item

    async def zscan_iter(
        self,
        key: KeyT,
        match: Optional[ValueT] = None,
        count: Optional[int] = None,
    ):
        """
        Make an iterator using the ZSCAN command so that the client doesn't
        need to remember the cursor position.
        """
        cursor = None

        while cursor != 0:
            cursor, data = await self.zscan(
                key,
                cursor=cursor,
                match=match,
                count=count,
            )

            for item in data:
                yield item


class AbstractRedisCluster(AbstractRedis[AnyStr]):
    @redis_command(
        "RENAME",
        group=CommandGroup.GENERIC,
        response_callback=SimpleStringCallback(),
    )
    async def rename(self, key: KeyT, newkey: KeyT) -> bool:
        """
        Rename key ``src`` to ``dst``

        Cluster impl:
            This operation is no longer atomic because each key must be querried
            then set in separate calls because they maybe will change cluster node
        """

        if key == newkey:
            raise ResponseError("source and destination objects are the same")

        data = await self.dump(key)

        if data is None:
            raise ResponseError("no such key")

        ttl = await self.pttl(key)

        if ttl is None or ttl < 1:
            ttl = 0

        await self.delete([newkey])
        await self.restore(newkey, ttl, data)
        await self.delete([key])

        return True

    @redis_command("DEL", group=CommandGroup.GENERIC)
    async def delete(self, keys: Iterable[KeyT]) -> int:
        """
        "Delete one or more keys specified by ``keys``"
        """
        count = 0

        for arg in keys:
            count += await self.execute_command("DEL", arg)

        return count

    @redis_command(
        "RENAMENX",
        group=CommandGroup.GENERIC,
    )
    async def renamenx(self, key: KeyT, newkey: KeyT) -> bool:
        """
        Rekeys key ``key`` to ``newkey`` if ``newkey`` doesn't already exist

        :return: False when ``newkey`` already exists.
        """

        if not await self.exists([newkey]) == 1:
            return await self.rename(key, newkey)

        return False

    @mutually_inclusive_parameters("offset", "count")
    @redis_command(
        "SORT", group=CommandGroup.GENERIC, cluster=ClusterCommandConfig(pipeline=False)
    )
    async def sort(
        self,
        key: KeyT,
        gets: Iterable[ValueT] = [],
        by: Optional[ValueT] = None,
        offset: Optional[int] = None,
        count: Optional[int] = None,
        order: Optional[Literal[PureToken.ASC, PureToken.DESC]] = None,
        alpha: Optional[bool] = None,
        store: Optional[KeyT] = None,
    ) -> Union[Tuple[AnyStr, ...], int]:
        """
        Sort the elements in a list, set or sorted set

        :return: sorted elements.

         When the ``store`` option is specified the command returns the number of sorted elements
         in the destination list.
        """

        try:
            data_type = nativestr(await self.type(key))

            if data_type == "none":
                return ()
            elif data_type == "set":
                data = list(await self.smembers(key))[:]
            elif data_type == "list":
                data = await self.lrange(key, 0, -1)
            else:
                raise RedisClusterException(f"Unable to sort data type : {data_type}")

            if by is not None:
                # _sort_using_by_arg mutates data so we don't
                # need need a return value.
                data = await self._sort_using_by_arg(data, by, alpha)
            elif not alpha:
                data.sort(key=self._strtod_key_func)
            else:
                data.sort()

            if order == PureToken.DESC:
                data = data[::-1]

            if not (offset is None or count is None):
                data = data[offset : offset + count]

            if gets:
                data = await self._retrive_data_from_sort(data, gets)

            if store is not None:
                if data_type == "set":
                    await self.delete([store])
                    await self.rpush(store, data)
                elif data_type == "list":
                    await self.delete([store])
                    await self.rpush(store, data)
                else:
                    raise RedisClusterException(
                        f"Unable to store sorted data for data type : {data_type}"
                    )

                return len(data)

            return tuple(data)
        except KeyError:
            return ()

    async def _retrive_data_from_sort(self, data, gets) -> List[AnyStr]:
        """
        Used by sort()
        """

        if gets:
            new_data: List[AnyStr] = []

            for k in data:
                for g in gets:
                    single_item = await self._get_single_item(k, g)
                    if single_item:
                        new_data.append(single_item)
            data = new_data

        return data

    async def _get_single_item(self, k, g) -> Optional[AnyStr]:
        """
        Used by sort()
        """

        if "*" in g:
            g = g.replace("*", k)

            if "->" in g:
                key, hash_key = g.split("->")
                single_item = (await self.hgetall(key) or {}).get(hash_key)
            else:
                single_item = await self.get(g)
        elif "#" in g:
            single_item = k
        else:
            single_item = None

        return single_item

    def _strtod_key_func(self, arg):
        """
        Used by sort()
        """

        return float(arg)

    async def _sort_using_by_arg(self, data, by, alpha):
        """
        Used by sort()
        """

        async def _by_key(arg):
            key = by.replace("*", arg)

            if "->" in by:
                key, hash_key = key.split("->")
                v = await self.hget(key, hash_key)

                if v is not None:
                    if alpha:
                        return v
                    else:
                        return float(v)
            else:
                return await self.get(key)

        sorted_data = []

        for d in data:
            sorted_data.append((d, await _by_key(d)))

        return [x[0] for x in sorted(sorted_data, key=lambda x: x[1])]

    @redis_command("MGET", readonly=True, group=CommandGroup.STRING)
    async def mget(self, keys: Iterable[KeyT]) -> Tuple[Optional[AnyStr], ...]:
        """
        Returns values ordered identically to ``keys``

        Cluster impl:
            Itterate all keys and send GET for each key.
            This will go alot slower than a normal mget call in Redis.

            Operation is no longer atomic.
        """
        res = list()

        for arg in keys:
            res.append(await self.get(arg))

        return tuple(res)

    @redis_command(
        "MSET", group=CommandGroup.STRING, cluster=ClusterCommandConfig(pipeline=False)
    )
    async def mset(self, key_values: Dict[KeyT, ValueT]) -> bool:
        """
        Sets key/values based on a mapping. Mapping can be supplied as a single
        dictionary argument or as kwargs.

        Cluster impl:
            Itterate over all items and do SET on each (k,v) pair

            Operation is no longer atomic.
        """

        for pair in iteritems(key_values):
            await self.set(pair[0], pair[1])

        return True

    @redis_command(
        "MSETNX",
        group=CommandGroup.STRING,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def msetnx(self, key_values: Dict[KeyT, ValueT]) -> bool:
        """
        Sets key/values based on a mapping if none of the keys are already set.
        Mapping can be supplied as a single dictionary argument or as kwargs.
        Returns a boolean indicating if the operation was successful.

        Clutser impl:
            Itterate over all items and do GET to determine if all keys do not exists.

            If true then call mset() on all keys.
        """

        for k, _ in key_values.items():
            if await self.get(k):
                return False

        return await self.mset(key_values)

    @redis_command(
        "SDIFF",
        readonly=True,
        group=CommandGroup.SET,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def sdiff(self, keys: Iterable[KeyT]) -> Set[AnyStr]:
        """
        Returns the difference of sets specified by ``keys``

        Cluster impl:
            Query all keys and diff all sets and return result
        """
        _keys = list(keys)
        res = await self.smembers(_keys[0])

        for arg in _keys[1:]:
            res -= await self.smembers(arg)

        return res

    @redis_command(
        "SDIFFSTORE",
        group=CommandGroup.SET,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def sdiffstore(self, keys: Iterable[KeyT], destination: KeyT) -> int:
        """
        Stores the difference of sets specified by ``keys`` into a new
        set named ``destination``.  Returns the number of keys in the new set.
        Overwrites dest key if it exists.

        Cluster impl:
            Use sdiff() --> Delete dest key --> store result in dest key
        """
        res = await self.sdiff(keys)
        await self.delete([destination])

        if not res:
            return 0

        return await self.sadd(destination, res)

    @redis_command(
        "SINTER",
        readonly=True,
        group=CommandGroup.SET,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def sinter(self, keys: Iterable[KeyT]) -> Set[AnyStr]:
        """
        Returns the intersection of sets specified by ``keys``

        Cluster impl:
            Query all keys, intersection and return result
        """
        _keys = list(keys)
        res = await self.smembers(_keys[0])

        for arg in _keys[1:]:
            res &= await self.smembers(arg)

        return res

    @redis_command(
        "SINTERSTORE",
        group=CommandGroup.SET,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def sinterstore(self, keys: Iterable[KeyT], destination: KeyT) -> int:
        """
        Stores the intersection of sets specified by ``keys`` into a new
        set named ``destination``.  Returns the number of keys in the new set.

        Cluster impl:
            Use sinter() --> Delete dest key --> store result in dest key
        """
        res = await self.sinter(keys)
        await self.delete([destination])

        if res:
            await self.sadd(destination, res)

            return len(res)
        else:
            return 0

    @redis_command(
        "SMOVE", group=CommandGroup.SET, cluster=ClusterCommandConfig(pipeline=False)
    )
    async def smove(self, source: KeyT, destination: KeyT, member: ValueT) -> bool:
        """
        Moves ``member`` from set ``source`` to set ``destination`` atomically

        Cluster impl:
            SMEMBERS --> SREM --> SADD. Function is no longer atomic.
        """
        res = await self.srem(source, [member])

        # Only add the element if existed in src set

        if res == 1:
            await self.sadd(destination, [member])

        return bool(res)

    @redis_command(
        "SUNION",
        readonly=True,
        group=CommandGroup.SET,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def sunion(self, keys: Iterable[KeyT]) -> Set[AnyStr]:
        """
        Returns the union of sets specified by ``keys``

        Cluster impl:
            Query all keys, union and return result

            Operation is no longer atomic.
        """
        _keys = list(keys)
        res = await self.smembers(_keys[0])

        for arg in _keys[1:]:
            res |= await self.smembers(arg)

        return res

    @redis_command(
        "SUNIONSTORE",
        group=CommandGroup.SET,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def sunionstore(self, keys: Iterable[KeyT], destination: KeyT) -> int:
        """
        Stores the union of sets specified by ``keys`` into a new
        set named ``destination``.  Returns the number of keys in the new set.

        Cluster impl:
            Use sunion() --> Dlete dest key --> store result in dest key

            Operation is no longer atomic.
        """
        res = await self.sunion(keys)
        await self.delete([destination])

        return await self.sadd(destination, res)

    @redis_command(
        "BRPOPLPUSH",
        version_deprecated="6.2.0",
        group=CommandGroup.LIST,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def brpoplpush(
        self, source: KeyT, destination: KeyT, timeout: Union[int, float]
    ) -> Optional[AnyStr]:
        """
        Pops a value off the tail of ``source``, push it on the head of ``destination``
        and then return it.

        This command blocks until a value is in ``source`` or until ``timeout``
        seconds elapse, whichever is first. A ``timeout`` value of 0 blocks
        forever.

        Cluster impl:
            Call brpop() then send the result into lpush()

            Operation is no longer atomic.
        """
        try:
            values = await self.brpop([source], timeout=timeout)

            if not values:
                return None
        except TimeoutError:
            return None
        await self.lpush(destination, [values[1]])

        return values[1]

    @redis_command(
        "RPOPLPUSH",
        version_deprecated="6.2.0",
        group=CommandGroup.LIST,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def rpoplpush(self, source: KeyT, destination: KeyT) -> Optional[AnyStr]:
        """
        RPOP a value off of the ``source`` list and atomically LPUSH it
        on to the ``destination`` list.  Returns the value.

        Cluster impl:
            Call rpop() then send the result into lpush()

            Operation is no longer atomic.
        """
        value = await self.rpop(source)

        if value:
            await self.lpush(destination, [value])
            return value
        return None


class Redis(
    AbstractRedis[AnyStr],
    Generic[AnyStr],
    ResponseParser,
    RedisConnection,
    metaclass=RedisMeta,
):
    @overload
    def __init__(
        self: "Redis[bytes]",
        host: Optional[str] = ...,
        port: Optional[int] = ...,
        db: int = ...,
        *,
        username: Optional[str] = ...,
        password: Optional[str] = ...,
        stream_timeout: Optional[int] = ...,
        connect_timeout: Optional[int] = ...,
        connection_pool: Optional[ConnectionPool] = ...,
        unix_socket_path: Optional[str] = ...,
        encoding: str = ...,
        decode_responses: Literal[False] = ...,
        ssl: bool = ...,
        ssl_context: Optional[SSLContext] = ...,
        ssl_keyfile: Optional[str] = ...,
        ssl_certfile: Optional[str] = ...,
        ssl_cert_reqs: Optional[str] = ...,
        ssl_ca_certs: Optional[str] = ...,
        max_connections: Optional[int] = ...,
        retry_on_timeout: bool = ...,
        max_idle_time: int = ...,
        idle_check_interval: int = ...,
        client_name: Optional[str] = ...,
        **kwargs,
    ):
        ...

    @overload
    def __init__(
        self: "Redis[str]",
        host: Optional[str] = ...,
        port: Optional[int] = ...,
        db: int = ...,
        *,
        username: Optional[str] = ...,
        password: Optional[str] = ...,
        stream_timeout: Optional[int] = ...,
        connect_timeout: Optional[int] = ...,
        connection_pool: Optional[ConnectionPool] = ...,
        unix_socket_path: Optional[str] = ...,
        encoding: str = ...,
        decode_responses: Literal[True],
        ssl: bool = ...,
        ssl_context: Optional[SSLContext] = ...,
        ssl_keyfile: Optional[str] = ...,
        ssl_certfile: Optional[str] = ...,
        ssl_cert_reqs: Optional[str] = ...,
        ssl_ca_certs: Optional[str] = ...,
        max_connections: Optional[int] = ...,
        retry_on_timeout: bool = ...,
        max_idle_time: int = ...,
        idle_check_interval: int = ...,
        client_name: Optional[str] = ...,
        **kwargs,
    ):
        ...

    def __init__(
        self,
        host: Optional[str] = "localhost",
        port: Optional[int] = 6379,
        db: int = 0,
        *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        stream_timeout: Optional[int] = None,
        connect_timeout: Optional[int] = None,
        connection_pool: Optional[ConnectionPool] = None,
        unix_socket_path: Optional[str] = None,
        encoding: str = "utf-8",
        decode_responses: bool = False,
        ssl: bool = False,
        ssl_context: Optional[SSLContext] = None,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_cert_reqs: Optional[str] = None,
        ssl_ca_certs: Optional[str] = None,
        max_connections: Optional[int] = None,
        retry_on_timeout: bool = False,
        max_idle_time: int = 0,
        idle_check_interval: int = 1,
        client_name: Optional[str] = None,
        **kwargs,
    ):
        super(Redis, self).__init__(
            host=host,
            port=port,
            db=db,
            username=username,
            password=password,
            stream_timeout=stream_timeout,
            connect_timeout=connect_timeout,
            connection_pool=connection_pool,
            unix_socket_path=unix_socket_path,
            encoding=encoding,
            decode_responses=decode_responses,
            ssl=ssl,
            ssl_context=ssl_context,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            ssl_cert_reqs=ssl_cert_reqs,
            ssl_ca_certs=ssl_ca_certs,
            max_connections=max_connections,
            retry_on_timeout=retry_on_timeout,
            max_idle_time=max_idle_time,
            idle_check_interval=idle_check_interval,
            client_name=client_name,
        )
        self._use_lua_lock = None

    @classmethod
    @overload
    def from_url(
        cls,
        url: str,
        db: Optional[int] = ...,
        *,
        decode_responses: Literal[False] = ...,
        **kwargs,
    ) -> "Redis[bytes]":
        ...

    @classmethod
    @overload
    def from_url(
        cls,
        url: str,
        db: Optional[int] = ...,
        *,
        decode_responses: Literal[True],
        **kwargs,
    ) -> "Redis[str]":
        ...

    @classmethod
    def from_url(
        cls,
        url: str,
        db: Optional[int] = None,
        *,
        decode_responses: bool = False,
        **kwargs,
    ):
        """
        Return a Redis client object configured from the given URL, which must
        use either the `redis:// scheme
        <http://www.iana.org/assignments/uri-schemes/prov/redis>`_ for RESP
        connections or the ``unix://`` scheme for Unix domain sockets.

        For example:

        - ``redis://[:password]@localhost:6379/0``
        - ``unix://[:password]@/path/to/socket.sock?db=0``

        There are several ways to specify a database number. The parse function
        will return the first specified option:

            1. A ``db`` querystring option, e.g. ``redis://localhost?db=0``
            2. If using the redis:// scheme, the path argument of the url, e.g.
               ``redis://localhost/0``
            3. The ``db`` argument to this function.

        If none of these options are specified, db=0 is used.


        Any additional querystring arguments and keyword arguments will be
        passed along to the :class:`ConnectionPool` class's initializer. In the case
        of conflicting arguments, querystring arguments always win.
        """
        connection_pool: ConnectionPool = ConnectionPool.from_url(
            url, db=db, decode_responses=decode_responses, **kwargs
        )

        if decode_responses:
            return Redis[str](decode_responses=True, connection_pool=connection_pool)
        else:
            return Redis[bytes](decode_responses=False, connection_pool=connection_pool)

    def set_response_callback(self, command, callback):
        """Sets a custom Response Callback"""
        self.response_callbacks[command] = callback

    # COMMAND EXECUTION AND PROTOCOL PARSING
    async def execute_command(self, command: Any, *args: Any, **options: Any) -> Any:
        """Executes a command and returns a parsed response"""
        pool = self.connection_pool
        connection = await pool.get_connection()
        try:
            await connection.send_command(command, *args)

            return await self.parse_response(connection, command, **options)
        except asyncio.CancelledError:
            # do not retry when coroutine is cancelled
            connection.disconnect()
            raise
        except (ConnectionError, TimeoutError) as e:
            connection.disconnect()

            if not connection.retry_on_timeout and isinstance(e, TimeoutError):
                raise
            await connection.send_command(command, *args)

            return await self.parse_response(connection, command, **options)
        finally:
            pool.release(connection)

    def pubsub(self, **kwargs):
        """
        Return a Publish/Subscribe object. With this object, you can
        subscribe to channels and listen for messages that get published to
        them.
        """
        from coredis.commands.builders.pubsub import PubSub

        return PubSub(self.connection_pool, **kwargs)

    async def pipeline(
        self,
        transaction: Optional[bool] = True,
        watches: Optional[Iterable[ValueT]] = None,
    ) -> SupportsWatch:
        """
        Returns a new pipeline object that can queue multiple commands for
        later execution. ``transaction`` indicates whether all commands
        should be executed atomically. Apart from making a group of operations
        atomic, pipelines are useful for reducing the back-and-forth overhead
        between the client and server.
        """
        from coredis.commands.builders.pipeline import Pipeline

        pipeline = Pipeline(self.connection_pool, self.response_callbacks, transaction)
        await pipeline.reset()

        return pipeline


class RedisCluster(
    AbstractRedisCluster[AnyStr], ResponseParser, RedisConnection, metaclass=ClusterMeta
):

    RedisClusterRequestTTL = 16
    NODES_FLAGS: Dict[str, NodeFlag] = {}
    RESPONSE_CALLBACKS: Dict[str, Callable] = {}
    RESULT_CALLBACKS: Dict[str, Callable] = {}

    connection_pool: ClusterConnectionPool

    @overload
    def __init__(
        self: "RedisCluster[bytes]",
        host: Optional[str] = ...,
        port: Optional[int] = ...,
        *,
        startup_nodes: Optional[Iterable[Dict]] = ...,
        max_connections: int = ...,
        max_connections_per_node: bool = ...,
        readonly: bool = ...,
        reinitialize_steps: Optional[int] = ...,
        skip_full_coverage_check: bool = ...,
        nodemanager_follow_cluster: bool = ...,
        decode_responses: Literal[False] = ...,
        connection_pool: Optional[ClusterConnectionPool] = ...,
        **kwargs,
    ):
        ...

    @overload
    def __init__(
        self: "RedisCluster[str]",
        host: Optional[str] = ...,
        port: Optional[int] = ...,
        *,
        startup_nodes: Optional[Iterable[Dict]] = ...,
        max_connections: int = ...,
        max_connections_per_node: bool = ...,
        readonly: bool = ...,
        reinitialize_steps: Optional[int] = ...,
        skip_full_coverage_check: bool = ...,
        nodemanager_follow_cluster: bool = ...,
        decode_responses: Literal[True],
        connection_pool: Optional[ClusterConnectionPool] = ...,
        **kwargs,
    ):
        ...

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        startup_nodes: Optional[Iterable[Dict]] = None,
        max_connections: int = 32,
        max_connections_per_node: bool = False,
        readonly: bool = False,
        reinitialize_steps: Optional[int] = None,
        skip_full_coverage_check: bool = False,
        nodemanager_follow_cluster: bool = False,
        decode_responses: bool = False,
        connection_pool: Optional[ClusterConnectionPool] = None,
        **kwargs,
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
        # Tweaks to Redis client arguments when running in cluster mode

        if "db" in kwargs:
            raise RedisClusterException(
                "Argument 'db' is not possible to use in cluster mode"
            )

        if connection_pool:
            pool = connection_pool
        else:
            startup_nodes = [] if startup_nodes is None else list(startup_nodes)

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
                decode_responses=decode_responses,
                **kwargs,
            )

        super(RedisCluster, self).__init__(
            connection_pool=pool, decode_responses=decode_responses, **kwargs
        )

        self.refresh_table_asap: bool = False
        self.nodes_flags: Dict[str, NodeFlag] = self.__class__.NODES_FLAGS.copy()
        self.result_callbacks: Dict[
            str, Callable
        ] = self.__class__.RESULT_CALLBACKS.copy()
        self.response_callbacks: Dict[
            str, Callable
        ] = self.__class__.RESPONSE_CALLBACKS.copy()

    @classmethod
    @overload
    def from_url(
        cls,
        url: str,
        *,
        db: Optional[int] = ...,
        skip_full_coverage_check: bool = ...,
        decode_responses: Literal[False] = ...,
        **kwargs,
    ) -> "RedisCluster[bytes]":
        ...

    @classmethod
    @overload
    def from_url(
        cls,
        url: str,
        *,
        db: Optional[int] = ...,
        skip_full_coverage_check: bool = ...,
        decode_responses: Literal[True],
        **kwargs,
    ) -> "RedisCluster[str]":
        ...

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        db: Optional[int] = None,
        skip_full_coverage_check: bool = False,
        decode_responses: bool = False,
        **kwargs,
    ):
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
        passed along to the :class:`ConnectionPool` class's initializer. In the case
        of conflicting arguments, querystring arguments always win.
        """
        connection_pool = ClusterConnectionPool.from_url(
            url,
            db=db,
            skip_full_coverage_check=skip_full_coverage_check,
            decode_responses=decode_responses,
            **kwargs,
        )
        if decode_responses:
            return RedisCluster[str](
                decode_responses=True, connection_pool=connection_pool
            )
        else:
            return RedisCluster[bytes](
                decode_responses=False, connection_pool=connection_pool
            )

    def __repr__(self):
        servers = list(
            {
                "{0}:{1}".format(info["host"], info["port"])
                for info in self.connection_pool.nodes.startup_nodes
            }
        )
        servers.sort()

        return "{0}<{1}>".format(type(self).__name__, ", ".join(servers))

    @property
    def all_nodes(self) -> Iterator[Redis]:
        """ """
        for node in self.connection_pool.nodes.all_nodes():
            yield self.connection_pool.nodes.get_redis_link(node["host"], node["port"])

    @property
    def primaries(self) -> Iterator[Redis]:
        """ """
        for master in self.connection_pool.nodes.all_primaries():
            yield self.connection_pool.nodes.get_redis_link(
                master["host"], master["port"]
            )

    @property
    def replicas(self) -> Iterator[Redis]:
        """ """
        for replica in self.connection_pool.nodes.all_replicas():
            yield self.connection_pool.nodes.get_redis_link(
                replica["host"], replica["port"]
            )

    def set_result_callback(self, command, callback):
        "Sets a custom Result Callback"
        self.result_callbacks[command] = callback

    def _determine_slot(self, *args):
        """Figures out what slot based on command and args"""

        if len(args) <= 1:
            raise RedisClusterException(
                f"No way to dispatch this command:{args} to Redis Cluster. Missing key."
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
        elif command in ("ZINTER", "ZDIFF", "ZUNION"):
            keys = args[2 : args[1] + 1]
            slots = {self.connection_pool.nodes.keyslot(key) for key in keys}

            return slots.pop()
        elif command in ("ZINTERSTORE", "ZDIFFSTORE", "ZUNIONSTORE"):
            keys = args[3 : args[2] + 3]
            slots = {self.connection_pool.nodes.keyslot(key) for key in keys}

            return slots.pop()
        elif command == "OBJECT":
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
        elif node_flag == NodeFlag.PRIMARIES:
            return self.connection_pool.nodes.all_primaries()
        elif node_flag == NodeFlag.ALL:
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
                    node = self.connection_pool.get_node_by_slot(slot, command)
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

    async def execute_command_on_nodes(
        self, nodes: Iterable[Any], *args: Any, **kwargs: Any
    ) -> Any:
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

    def pubsub(self, **kwargs):
        from coredis.commands.builders.pubsub import ClusterPubSub

        return ClusterPubSub(self.connection_pool, **kwargs)

    async def pipeline(
        self,
        transaction: Optional[bool] = None,
        watches: Optional[Iterable[ValueT]] = None,
    ) -> SupportsWatch:
        """
        Pipelines do not work in cluster mode the same way they do in normal mode.
        Create a clone of this object so that simulating pipelines will work correctly.

        Each command will be called directly when used and when calling execute() will only
        return the result stack. Cluster transaction can only be run with commands in the same
        node, otherwise error will be raised.
        """
        await self.connection_pool.initialize()

        from coredis.commands.builders.pipeline import ClusterPipeline

        return ClusterPipeline(
            connection_pool=self.connection_pool,
            startup_nodes=self.connection_pool.nodes.startup_nodes,
            result_callbacks=self.result_callbacks,
            response_callbacks=self.response_callbacks,
            transaction=transaction,
            watches=watches,
        )

    async def scan_iter(
        self, match: Optional[ValueT] = None, count: Optional[int] = None
    ):
        for node in self.primaries:
            cursor = "0"

            while cursor != 0:
                pieces: CommandArgList = [cursor]

                if match is not None:
                    pieces.extend(["MATCH", match])

                if count is not None:
                    pieces.extend(["COUNT", count])
                response = await node.execute_command("SCAN", *pieces)
                cursor, data = response

                for item in data:
                    yield item

    @contextlib.contextmanager
    def all(
        self,
        flag: Literal[NodeFlag.ALL, NodeFlag.PRIMARIES, NodeFlag.REPLICAS],
    ):

        if flag == NodeFlag.ALL:
            nodes = self.all_nodes
        elif flag == NodeFlag.PRIMARIES:
            nodes = self.primaries
        else:
            nodes = self.replicas
        proxy = NodeProxy(list(nodes))
        yield proxy
