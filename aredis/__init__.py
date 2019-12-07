import platform
from distutils.version import StrictVersion
from aredis.client import (StrictRedis, StrictRedisCluster)
from aredis.connection import (
    Connection,
    UnixDomainSocketConnection,
    ClusterConnection
)
from aredis.pool import ConnectionPool, ClusterConnectionPool
from aredis.exceptions import (
    AuthenticationError, BusyLoadingError, ConnectionError,
    DataError, InvalidResponse, PubSubError, ReadOnlyError,
    RedisError, ResponseError, TimeoutError, WatchError,
    CompressError, ClusterDownException, ClusterCrossSlotError,
    CacheError, ClusterDownError, ClusterError, RedisClusterException,
    RedisClusterError, ExecAbortError, LockError, NoScriptError
)


__version__ = '1.1.5'

VERSION = tuple(map(int, __version__.split('.')))

python_version = platform.python_version()
LOOP_DEPRECATED = StrictVersion(python_version) >= StrictVersion("3.8.0")

__all__ = [
    'StrictRedis', 'StrictRedisCluster',
    'Connection', 'UnixDomainSocketConnection', 'ClusterConnection',
    'ConnectionPool', 'ClusterConnectionPool',
    'AuthenticationError', 'BusyLoadingError', 'ConnectionError', 'DataError',
    'InvalidResponse', 'PubSubError', 'ReadOnlyError', 'RedisError',
    'ResponseError', 'TimeoutError', 'WatchError',
    'CompressError', 'ClusterDownException', 'ClusterCrossSlotError',
    'CacheError', 'ClusterDownError', 'ClusterError', 'RedisClusterException',
    'RedisClusterError', 'ExecAbortError', 'LockError', 'NoScriptError'
]
