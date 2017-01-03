from aredis.client import StrictRedis
from aredis.connection import (
    Connection,
    UnixDomainSocketConnection
)
from aredis.pool import ConnectionPool
from aredis.exceptions import (
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
    WatchError
)


__version__ = '1.0.0'
VERSION = tuple(map(int, __version__.split('.')))

__all__ = [
    'StrictRedis', 'ConnectionPool',
    'Connection', 'UnixDomainSocketConnection',
    'AuthenticationError', 'BusyLoadingError', 'ConnectionError', 'DataError',
    'InvalidResponse', 'PubSubError', 'ReadOnlyError', 'RedisError',
    'ResponseError', 'TimeoutError', 'WatchError'
]
