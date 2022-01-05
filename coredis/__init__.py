from coredis.client import StrictRedis, StrictRedisCluster
from coredis.connection import Connection, UnixDomainSocketConnection, ClusterConnection
from coredis.pool import ConnectionPool, ClusterConnectionPool
from coredis.exceptions import (
    AuthenticationError,
    BusyLoadingError,
    ConnectionError,
    DataError,
    InvalidResponse,
    PubSubError,
    ReadOnlyError,
    RedisError,
    ResponseError,
    TimeoutError,
    WatchError,
    CompressError,
    ClusterDownException,
    ClusterCrossSlotError,
    CacheError,
    ClusterDownError,
    ClusterError,
    RedisClusterException,
    RedisClusterError,
    ExecAbortError,
    LockError,
    NoScriptError,
)


__version__ = "1.1.8"

VERSION = tuple(map(int, __version__.split(".")))


__all__ = [
    "StrictRedis",
    "StrictRedisCluster",
    "Connection",
    "UnixDomainSocketConnection",
    "ClusterConnection",
    "ConnectionPool",
    "ClusterConnectionPool",
    "AuthenticationError",
    "BusyLoadingError",
    "ConnectionError",
    "DataError",
    "InvalidResponse",
    "PubSubError",
    "ReadOnlyError",
    "RedisError",
    "ResponseError",
    "TimeoutError",
    "WatchError",
    "CompressError",
    "ClusterDownException",
    "ClusterCrossSlotError",
    "CacheError",
    "ClusterDownError",
    "ClusterError",
    "RedisClusterException",
    "RedisClusterError",
    "ExecAbortError",
    "LockError",
    "NoScriptError",
]

from . import _version

__version__ = _version.get_versions()["version"]
