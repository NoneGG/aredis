# Lazy imports to reduce startup time and memory footprint
# Only import what's actually used when accessed

def __getattr__(name):
    """Lazy loading of module attributes"""
    if name in ('StrictRedis', 'StrictRedisCluster'):
        from aredis.client import StrictRedis, StrictRedisCluster
        globals()['StrictRedis'] = StrictRedis
        globals()['StrictRedisCluster'] = StrictRedisCluster
        return globals()[name]
    elif name in ('Connection', 'UnixDomainSocketConnection', 'ClusterConnection'):
        from aredis.connection import Connection, UnixDomainSocketConnection, ClusterConnection
        globals()['Connection'] = Connection
        globals()['UnixDomainSocketConnection'] = UnixDomainSocketConnection
        globals()['ClusterConnection'] = ClusterConnection
        return globals()[name]
    elif name in ('ConnectionPool', 'ClusterConnectionPool'):
        from aredis.pool import ConnectionPool, ClusterConnectionPool
        globals()['ConnectionPool'] = ConnectionPool
        globals()['ClusterConnectionPool'] = ClusterConnectionPool
        return globals()[name]
    elif name in ('AuthenticationError', 'BusyLoadingError', 'ConnectionError',
                  'DataError', 'InvalidResponse', 'PubSubError', 'ReadOnlyError',
                  'RedisError', 'ResponseError', 'TimeoutError', 'WatchError',
                  'CompressError', 'ClusterDownException', 'ClusterCrossSlotError',
                  'CacheError', 'ClusterDownError', 'ClusterError', 'RedisClusterException',
                  'RedisClusterError', 'ExecAbortError', 'LockError', 'NoScriptError'):
        from aredis.exceptions import (
            AuthenticationError, BusyLoadingError, ConnectionError,
            DataError, InvalidResponse, PubSubError, ReadOnlyError,
            RedisError, ResponseError, TimeoutError, WatchError,
            CompressError, ClusterDownException, ClusterCrossSlotError,
            CacheError, ClusterDownError, ClusterError, RedisClusterException,
            RedisClusterError, ExecAbortError, LockError, NoScriptError
        )
        for exc_name in ('AuthenticationError', 'BusyLoadingError', 'ConnectionError',
                         'DataError', 'InvalidResponse', 'PubSubError', 'ReadOnlyError',
                         'RedisError', 'ResponseError', 'TimeoutError', 'WatchError',
                         'CompressError', 'ClusterDownException', 'ClusterCrossSlotError',
                         'CacheError', 'ClusterDownError', 'ClusterError', 'RedisClusterException',
                         'RedisClusterError', 'ExecAbortError', 'LockError', 'NoScriptError'):
            globals()[exc_name] = locals()[exc_name]
        return globals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__version__ = '1.1.8'

VERSION = tuple(map(int, __version__.split('.')))


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
