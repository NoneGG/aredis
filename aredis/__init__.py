from aredis.client import Redis, StrictRedis
from aredis.connection import (
    Connection,
    UnixDomainSocketConnection
)
from aredis.pool import ConnectionPool
from redis.exceptions import (
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
    'Redis', 'StrictRedis', 'ConnectionPool',
    'Connection', 'UnixDomainSocketConnection',
    'AuthenticationError', 'BusyLoadingError', 'ConnectionError', 'DataError',
    'InvalidResponse', 'PubSubError', 'ReadOnlyError', 'RedisError',
    'ResponseError', 'TimeoutError', 'WatchError'
]
