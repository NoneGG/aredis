"""
coredis
-------

coredis is an async redis client with support for redis server,
cluster & sentinel.
"""

from coredis.client import Redis, RedisCluster
from coredis.connection import ClusterConnection, Connection, UnixDomainSocketConnection
from coredis.exceptions import (
    AskError,
    AuthenticationError,
    AuthenticationFailureError,
    AuthenticationRequiredError,
    AuthorizationError,
    BusyLoadingError,
    ClusterCrossSlotError,
    ClusterDownError,
    ClusterError,
    ClusterTransactionError,
    CommandSyntaxError,
    ConnectionError,
    DataError,
    ExecAbortError,
    InvalidResponse,
    LockError,
    MovedError,
    NoScriptError,
    PubSubError,
    ReadOnlyError,
    RedisClusterException,
    RedisError,
    ResponseError,
    TimeoutError,
    TryAgainError,
    WatchError,
)
from coredis.pool import BlockingConnectionPool, ClusterConnectionPool, ConnectionPool
from coredis.tokens import PureToken
from coredis.utils import NodeFlag

from . import _version

__all__ = [
    "Redis",
    "RedisCluster",
    "Connection",
    "UnixDomainSocketConnection",
    "ClusterConnection",
    "BlockingConnectionPool",
    "ConnectionPool",
    "ClusterConnectionPool",
    "AskError",
    "AuthenticationError",
    "AuthenticationFailureError",
    "AuthenticationRequiredError",
    "AuthorizationError",
    "BusyLoadingError",
    "ClusterCrossSlotError",
    "ClusterDownError",
    "ClusterError",
    "ClusterTransactionError",
    "CommandSyntaxError",
    "ConnectionError",
    "DataError",
    "ExecAbortError",
    "InvalidResponse",
    "LockError",
    "MovedError",
    "NodeFlag",
    "NoScriptError",
    "PubSubError",
    "PureToken",
    "ReadOnlyError",
    "RedisClusterException",
    "RedisError",
    "ResponseError",
    "TimeoutError",
    "TryAgainError",
    "WatchError",
]

# For backward compatibility
StrictRedis = Redis
StrictRedisCluster = RedisCluster


__version__ = _version.get_versions()["version"]
