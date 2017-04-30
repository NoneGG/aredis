from __future__ import with_statement
import os
import pytest
import aredis
import re

from aredis.pool import to_bool
from aredis.exceptions import (ConnectionError, RedisError,
                               BusyLoadingError, ReadOnlyError)
from .conftest import skip_if_server_version_lt


class DummyConnection(object):
    description = "DummyConnection<>"

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.pid = os.getpid()


class TestConnectionPool(object):
    def get_pool(self, connection_kwargs=None, max_connections=None,
                 connection_class=DummyConnection):
        connection_kwargs = connection_kwargs or {}
        pool = aredis.ConnectionPool(
            connection_class=connection_class,
            max_connections=max_connections,
            **connection_kwargs)
        return pool

    def test_connection_creation(self):
        connection_kwargs = {'foo': 'bar', 'biz': 'baz'}
        pool = self.get_pool(connection_kwargs=connection_kwargs)
        connection = pool.get_connection()
        assert isinstance(connection, DummyConnection)
        assert connection.kwargs == connection_kwargs

    def test_multiple_connections(self):
        pool = self.get_pool()
        c1 = pool.get_connection()
        c2 = pool.get_connection()
        assert c1 != c2

    def test_max_connections(self):
        pool = self.get_pool(max_connections=2)
        pool.get_connection()
        pool.get_connection()
        with pytest.raises(ConnectionError):
            pool.get_connection()

    def test_reuse_previously_released_connection(self):
        pool = self.get_pool()
        c1 = pool.get_connection()
        pool.release(c1)
        c2 = pool.get_connection()
        assert c1 == c2

    def test_repr_contains_db_info_tcp(self):
        connection_kwargs = {'host': 'localhost', 'port': 6379, 'db': 1}
        pool = self.get_pool(connection_kwargs=connection_kwargs,
                             connection_class=aredis.Connection)
        expected = 'ConnectionPool<Connection<host=localhost,port=6379,db=1>>'
        assert repr(pool) == expected

    def test_repr_contains_db_info_unix(self):
        connection_kwargs = {'path': '/abc', 'db': 1}
        pool = self.get_pool(connection_kwargs=connection_kwargs,
                             connection_class=aredis.UnixDomainSocketConnection)
        expected = 'ConnectionPool<UnixDomainSocketConnection<path=/abc,db=1>>'
        assert repr(pool) == expected


class TestConnectionPoolURLParsing(object):
    def test_defaults(self):
        pool = aredis.ConnectionPool.from_url('redis://localhost')
        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None,
        }

    def test_hostname(self):
        pool = aredis.ConnectionPool.from_url('redis://myhost')
        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs == {
            'host': 'myhost',
            'port': 6379,
            'db': 0,
            'password': None,
        }

    def test_quoted_hostname(self):
        pool = aredis.ConnectionPool.from_url('redis://my %2F host %2B%3D+',
                                             decode_components=True)
        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs == {
            'host': 'my / host +=+',
            'port': 6379,
            'db': 0,
            'password': None,
        }

    def test_port(self):
        pool = aredis.ConnectionPool.from_url('redis://localhost:6380')
        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6380,
            'db': 0,
            'password': None,
        }

    def test_password(self):
        pool = aredis.ConnectionPool.from_url('redis://:mypassword@localhost')
        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': 'mypassword',
        }

    def test_quoted_password(self):
        pool = aredis.ConnectionPool.from_url(
            'redis://:%2Fmypass%2F%2B word%3D%24+@localhost',
            decode_components=True)
        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': '/mypass/+ word=$+',
        }

    def test_db_as_argument(self):
        pool = aredis.ConnectionPool.from_url('redis://localhost', db='1')
        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 1,
            'password': None,
        }

    def test_db_in_path(self):
        pool = aredis.ConnectionPool.from_url('redis://localhost/2', db='1')
        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 2,
            'password': None,
        }

    def test_db_in_querystring(self):
        pool = aredis.ConnectionPool.from_url('redis://localhost/2?db=3',
                                             db='1')
        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 3,
            'password': None,
        }

    def test_extra_typed_querystring_options(self):
        pool = aredis.ConnectionPool.from_url(
            'redis://localhost/2?stream_timeout=20&connect_timeout=10'
        )

        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 2,
            'stream_timeout': 20.0,
            'connect_timeout': 10.0,
            'password': None,
        }

    def test_boolean_parsing(self):
        for expected, value in (
                (None, None),
                (None, ''),
                (False, 0), (False, '0'),
                (False, 'f'), (False, 'F'), (False, 'False'),
                (False, 'n'), (False, 'N'), (False, 'No'),
                (True, 1), (True, '1'),
                (True, 'y'), (True, 'Y'), (True, 'Yes'),
        ):
            assert expected is to_bool(value)

    def test_invalid_extra_typed_querystring_options(self):
        import warnings
        with warnings.catch_warnings(record=True) as warning_log:
            aredis.ConnectionPool.from_url(
                'redis://localhost/2?stream_timeout=_&'
                'connect_timeout=abc'
            )
        # Compare the message values
        assert [
            str(m.message) for m in
            sorted(warning_log, key=lambda l: str(l.message))
        ] == [
            'Invalid value for `connect_timeout` in connection URL.',
            'Invalid value for `stream_timeout` in connection URL.',
        ]

    def test_extra_querystring_options(self):
        pool = aredis.ConnectionPool.from_url('redis://localhost?a=1&b=2')
        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None,
            'a': '1',
            'b': '2'
        }

    def test_client_creates_connection_pool(self):
        r = aredis.StrictRedis.from_url('redis://myhost')
        assert r.connection_pool.connection_class == aredis.Connection
        assert r.connection_pool.connection_kwargs == {
            'host': 'myhost',
            'port': 6379,
            'db': 0,
            'password': None,
        }


class TestConnectionPoolUnixSocketURLParsing(object):
    def test_defaults(self):
        pool = aredis.ConnectionPool.from_url('unix:///socket')
        assert pool.connection_class == aredis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/socket',
            'db': 0,
            'password': None,
        }

    def test_password(self):
        pool = aredis.ConnectionPool.from_url('unix://:mypassword@/socket')
        assert pool.connection_class == aredis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/socket',
            'db': 0,
            'password': 'mypassword',
        }

    def test_quoted_password(self):
        pool = aredis.ConnectionPool.from_url(
            'unix://:%2Fmypass%2F%2B word%3D%24+@/socket',
            decode_components=True)
        assert pool.connection_class == aredis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/socket',
            'db': 0,
            'password': '/mypass/+ word=$+',
        }

    def test_quoted_path(self):
        pool = aredis.ConnectionPool.from_url(
            'unix://:mypassword@/my%2Fpath%2Fto%2F..%2F+_%2B%3D%24ocket',
            decode_components=True)
        assert pool.connection_class == aredis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/my/path/to/../+_+=$ocket',
            'db': 0,
            'password': 'mypassword',
        }

    def test_db_as_argument(self):
        pool = aredis.ConnectionPool.from_url('unix:///socket', db=1)
        assert pool.connection_class == aredis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/socket',
            'db': 1,
            'password': None,
        }

    def test_db_in_querystring(self):
        pool = aredis.ConnectionPool.from_url('unix:///socket?db=2', db=1)
        assert pool.connection_class == aredis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/socket',
            'db': 2,
            'password': None,
        }

    def test_extra_querystring_options(self):
        pool = aredis.ConnectionPool.from_url('unix:///socket?a=1&b=2')
        assert pool.connection_class == aredis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/socket',
            'db': 0,
            'password': None,
            'a': '1',
            'b': '2'
        }


class TestSSLConnectionURLParsing(object):
    def test_defaults(self):
        pool = aredis.ConnectionPool.from_url('rediss://localhost')
        assert pool.connection_class == aredis.Connection
        assert pool.connection_kwargs.pop('ssl_context') is not None
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None,
        }

    def test_cert_reqs_options(self):
        import ssl
        with pytest.raises(TypeError) as e:
            pool = aredis.ConnectionPool.from_url(
                'rediss://?ssl_cert_reqs=none&ssl_keyfile=test')
            assert e.message == 'certfile should be a valid filesystem path'
            assert pool.get_connection().ssl_context.verify_mode == ssl.CERT_NONE

        with pytest.raises(TypeError) as e:
            pool = aredis.ConnectionPool.from_url(
                'rediss://?ssl_cert_reqs=optional&ssl_keyfile=test')
            assert e.message == 'certfile should be a valid filesystem path'
            assert pool.get_connection().ssl_context.verify_mode == ssl.CERT_OPTIONAL

        with pytest.raises(TypeError) as e:
            pool = aredis.ConnectionPool.from_url(
                'rediss://?ssl_cert_reqs=required&ssl_keyfile=test')
            assert e.message == 'certfile should be a valid filesystem path'
            assert pool.get_connection().ssl_context.verify_mode == ssl.CERT_REQUIRED


class TestConnection(object):

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_on_connect_error(self, event_loop):
        """
        An error in Connection.on_connect should disconnect from the server
        see for details: https://github.com/andymccurdy/redis-py/issues/368
        """
        # this assumes the Redis server being tested against doesn't have
        # 9999 databases ;)
        bad_connection = aredis.StrictRedis(db=9999, loop=event_loop)
        # an error should be raised on connect
        with pytest.raises(RedisError):
            await bad_connection.info()
        pool = bad_connection.connection_pool
        assert len(pool._available_connections) == 1
        assert pool._available_connections[0]._writer
        assert pool._available_connections[0]._reader

    @skip_if_server_version_lt('2.8.8')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_busy_loading_disconnects_socket(self, event_loop):
        """
        If Redis raises a LOADING error, the connection should be
        disconnected and a BusyLoadingError raised
        """
        client = aredis.StrictRedis(loop=event_loop)
        with pytest.raises(BusyLoadingError):
            await client.execute_command('DEBUG', 'ERROR', 'LOADING fake message')
        pool = client.connection_pool
        assert len(pool._available_connections) == 1
        assert pool._available_connections[0]._writer
        assert pool._available_connections[0]._reader

    @skip_if_server_version_lt('2.8.8')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_busy_loading_from_pipeline_immediate_command(self, event_loop):
        """
        BusyLoadingErrors should raise from Pipelines that execute a
        command immediately, like WATCH does.
        """
        client = aredis.StrictRedis(loop=event_loop)
        pipe = await client.pipeline()
        with pytest.raises(BusyLoadingError):
            await pipe.immediate_execute_command('DEBUG', 'ERROR', 'LOADING fake message')
        pool = client.connection_pool
        assert not pipe.connection
        assert len(pool._available_connections) == 1
        assert not pool._available_connections[0]._writer
        assert not pool._available_connections[0]._reader

    @skip_if_server_version_lt('2.8.8')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_busy_loading_from_pipeline(self, event_loop):
        """
        BusyLoadingErrors should be raised from a pipeline execution
        regardless of the raise_on_error flag.
        """
        client = aredis.StrictRedis(loop=event_loop)
        pipe = await client.pipeline()
        await pipe.execute_command('DEBUG', 'ERROR', 'LOADING fake message')
        with pytest.raises(RedisError):
            await pipe.execute()
        pool = client.connection_pool
        assert not pipe.connection
        assert len(pool._available_connections) == 1
        assert pool._available_connections[0]._writer
        assert pool._available_connections[0]._reader

    @skip_if_server_version_lt('2.8.8')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_read_only_error(self, event_loop):
        "READONLY errors get turned in ReadOnlyError exceptions"
        client = aredis.StrictRedis(loop=event_loop)
        with pytest.raises(ReadOnlyError):
            await client.execute_command('DEBUG', 'ERROR', 'READONLY blah blah')

    def test_connect_from_url_tcp(self):
        connection = aredis.StrictRedis.from_url('redis://localhost')
        pool = connection.connection_pool

        assert re.match('(.*)<(.*)<(.*)>>', repr(pool)).groups() == (
            'ConnectionPool',
            'Connection',
            'host=localhost,port=6379,db=0',
        )

    def test_connect_from_url_unix(self):
        connection = aredis.StrictRedis.from_url('unix:///path/to/socket')
        pool = connection.connection_pool

        assert re.match('(.*)<(.*)<(.*)>>', repr(pool)).groups() == (
            'ConnectionPool',
            'UnixDomainSocketConnection',
            'path=/path/to/socket,db=0',
        )
