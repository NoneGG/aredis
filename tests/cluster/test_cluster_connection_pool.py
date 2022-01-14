# -*- coding: utf-8 -*-


# python std lib
from __future__ import with_statement

import asyncio
import os

# 3rd party imports
import pytest
from mock import Mock, patch

# rediscluster imports
from coredis import StrictRedis
from coredis.connection import ClusterConnection, Connection, UnixDomainSocketConnection
from coredis.exceptions import RedisClusterException
from coredis.pool import ClusterConnectionPool, ConnectionPool

try:
    pass

    ssl_available = True
except ImportError:
    ssl_available = False


class DummyConnection:
    description_format = "DummyConnection<>"

    def __init__(self, host="localhost", port=7000, socket_timeout=None, **kwargs):
        self.kwargs = kwargs
        self.pid = os.getpid()
        self.host = host
        self.port = port
        self.socket_timeout = socket_timeout
        self.awaiting_response = False


class TestConnectionPool:
    async def get_pool(
        self,
        connection_kwargs=None,
        max_connections=None,
        max_connections_per_node=None,
        connection_class=DummyConnection,
    ):
        connection_kwargs = connection_kwargs or {}
        pool = ClusterConnectionPool(
            connection_class=connection_class,
            max_connections=max_connections,
            max_connections_per_node=max_connections_per_node,
            startup_nodes=[{"host": "127.0.0.1", "port": 7000}],
            **connection_kwargs
        )
        await pool.initialize()
        return pool

    @pytest.mark.asyncio()
    async def test_in_use_not_exists(self):
        """
        Test that if for some reason, the node that it tries to get the connectino for
        do not exists in the _in_use_connection variable.
        """
        pool = await self.get_pool()
        pool._in_use_connections = {}
        pool.get_connection("pubsub", channel="foobar")

    @pytest.mark.asyncio()
    async def test_connection_creation(self):
        connection_kwargs = {"foo": "bar", "biz": "baz"}
        pool = await self.get_pool(connection_kwargs=connection_kwargs)
        connection = pool.get_connection_by_node({"host": "127.0.0.1", "port": 7000})
        assert isinstance(connection, DummyConnection)
        for key in connection_kwargs:
            assert connection.kwargs[key] == connection_kwargs[key]

    @pytest.mark.asyncio()
    async def test_multiple_connections(self):
        pool = await self.get_pool()
        c1 = pool.get_connection_by_node({"host": "127.0.0.1", "port": 7000})
        c2 = pool.get_connection_by_node({"host": "127.0.0.1", "port": 7001})
        assert c1 != c2

    @pytest.mark.asyncio()
    async def test_max_connections(self):
        pool = await self.get_pool(max_connections=2)
        pool.get_connection_by_node({"host": "127.0.0.1", "port": 7000})
        pool.get_connection_by_node({"host": "127.0.0.1", "port": 7001})
        with pytest.raises(RedisClusterException):
            pool.get_connection_by_node({"host": "127.0.0.1", "port": 7000})

    @pytest.mark.asyncio()
    async def test_max_connections_per_node(self):
        pool = await self.get_pool(max_connections=2, max_connections_per_node=True)
        pool.get_connection_by_node({"host": "127.0.0.1", "port": 7000})
        pool.get_connection_by_node({"host": "127.0.0.1", "port": 7001})
        pool.get_connection_by_node({"host": "127.0.0.1", "port": 7000})
        pool.get_connection_by_node({"host": "127.0.0.1", "port": 7001})
        with pytest.raises(RedisClusterException):
            pool.get_connection_by_node({"host": "127.0.0.1", "port": 7000})

    @pytest.mark.asyncio()
    async def test_max_connections_default_setting(self):
        pool = await self.get_pool(max_connections=None)
        assert pool.max_connections == 2 ** 31

    @pytest.mark.asyncio()
    async def test_reuse_previously_released_connection(self):
        pool = await self.get_pool()
        c1 = pool.get_connection_by_node({"host": "127.0.0.1", "port": 7000})
        pool.release(c1)
        c2 = pool.get_connection_by_node({"host": "127.0.0.1", "port": 7000})
        assert c1 == c2

    @pytest.mark.asyncio()
    async def test_repr_contains_db_info_tcp(self):
        """
        Note: init_slot_cache muts be set to false otherwise it will try to
              query the test server for data and then it can't be predicted reliably
        """
        connection_kwargs = {"host": "127.0.0.1", "port": 7000}
        pool = await self.get_pool(
            connection_kwargs=connection_kwargs, connection_class=ClusterConnection
        )
        expected = "ClusterConnectionPool<ClusterConnection<host=127.0.0.1,port=7000>>"
        assert repr(pool) == expected

    @pytest.mark.asyncio()
    async def test_get_connection_by_key(self):
        """
        This test assumes that when hashing key 'foo' will be sent to server with port 7002
        """
        pool = await self.get_pool(connection_kwargs={})

        # Patch the call that is made inside the method to allow control of the returned
        # connection object
        with patch.object(
            ClusterConnectionPool, "get_connection_by_slot", autospec=True
        ) as pool_mock:

            def side_effect(self, *args, **kwargs):
                return DummyConnection(port=1337)

            pool_mock.side_effect = side_effect

            connection = pool.get_connection_by_key("foo")
            assert connection.port == 1337

        with pytest.raises(RedisClusterException) as ex:
            pool.get_connection_by_key(None)
        assert str(ex.value).startswith(
            "No way to dispatch this command to Redis Cluster."
        ), True

    @pytest.mark.asyncio()
    async def test_get_connection_by_slot(self):
        """
        This test assumes that when doing keyslot operation on "foo" it will return 12182
        """
        pool = await self.get_pool(connection_kwargs={})

        # Patch the call that is made inside the method to allow control of the returned
        # connection object
        with patch.object(
            ClusterConnectionPool, "get_connection_by_node", autospec=True
        ) as pool_mock:

            def side_effect(self, *args, **kwargs):
                return DummyConnection(port=1337)

            pool_mock.side_effect = side_effect

            connection = pool.get_connection_by_slot(12182)
            assert connection.port == 1337

        m = Mock()
        pool.get_random_connection = m

        # If None value is provided then a random node should be tried/returned
        pool.get_connection_by_slot(None)
        m.assert_called_once_with()

    @pytest.mark.asyncio()
    async def test_get_connection_blocked(self):
        """
        Currently get_connection() should only be used by pubsub command.
        All other commands should be blocked and exception raised.
        """
        pool = await self.get_pool()

        with pytest.raises(RedisClusterException) as ex:
            pool.get_connection("GET")
        assert str(ex.value).startswith(
            "Only 'pubsub' commands can use get_connection()"
        )

    @pytest.mark.asyncio()
    async def test_master_node_by_slot(self):
        pool = await self.get_pool(connection_kwargs={})
        node = pool.get_master_node_by_slot(0)
        node["port"] = 7000
        node = pool.get_master_node_by_slot(12182)
        node["port"] = 7002

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_connection_idle_check(self, event_loop):
        pool = ClusterConnectionPool(
            startup_nodes=[dict(host="127.0.0.1", port=7000)],
            max_idle_time=0.2,
            idle_check_interval=0.1,
        )
        conn = pool.get_connection_by_node(
            {
                "name": "127.0.0.1:7000",
                "host": "127.0.0.1",
                "port": 7000,
                "server_type": "master",
            }
        )
        name = conn.node["name"]
        assert len(pool._in_use_connections[name]) == 1
        # not ket could be found in dict for now
        assert not pool._available_connections
        pool.release(conn)
        assert len(pool._in_use_connections[name]) == 0
        assert len(pool._available_connections[name]) == 1
        await asyncio.sleep(0.21)
        assert len(pool._in_use_connections[name]) == 0
        assert len(pool._available_connections[name]) == 0
        last_active_at = conn.last_active_at
        assert last_active_at == conn.last_active_at
        assert conn._writer is None and conn._reader is None


class TestReadOnlyConnectionPool:
    async def get_pool(
        self, connection_kwargs=None, max_connections=None, startup_nodes=None
    ):
        startup_nodes = startup_nodes or [{"host": "127.0.0.1", "port": 7000}]
        connection_kwargs = connection_kwargs or {}
        pool = ClusterConnectionPool(
            max_connections=max_connections,
            startup_nodes=startup_nodes,
            readonly=True,
            **connection_kwargs
        )
        await pool.initialize()
        return pool

    @pytest.mark.asyncio()
    async def test_repr_contains_db_info_readonly(self):
        """
        Note: init_slot_cache must be set to false otherwise it will try to
              query the test server for data and then it can't be predicted reliably
        """
        pool = await self.get_pool(
            startup_nodes=[
                {"host": "127.0.0.1", "port": 7000},
                {"host": "127.0.0.2", "port": 7001},
            ],
        )
        assert "ClusterConnection<host=127.0.0.2,port=7001>" in repr(pool)
        assert "ClusterConnection<host=127.0.0.1,port=7000>" in repr(pool)

    @pytest.mark.asyncio()
    async def test_max_connections(self):
        pool = await self.get_pool(max_connections=2)
        pool.get_connection_by_node({"host": "127.0.0.1", "port": 7000})
        pool.get_connection_by_node({"host": "127.0.0.1", "port": 7001})
        with pytest.raises(RedisClusterException):
            pool.get_connection_by_node({"host": "127.0.0.1", "port": 7000})

    @pytest.mark.asyncio()
    async def test_get_node_by_slot(self):
        """
        We can randomly get all nodes in readonly mode.
        """
        pool = await self.get_pool(connection_kwargs={})

        expected_ports = set(range(7000, 7006))
        actual_ports = set()
        for i in range(0, 16383):
            node = pool.get_node_by_slot(i)
            actual_ports.add(node["port"])
        assert actual_ports == expected_ports


class TestConnectionPoolURLParsing:
    def test_defaults(self):
        pool = ConnectionPool.from_url("redis://localhost")
        assert pool.connection_class == Connection
        assert pool.connection_kwargs == {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": None,
        }

    def test_hostname(self):
        pool = ConnectionPool.from_url("redis://myhost")
        assert pool.connection_class == Connection
        assert pool.connection_kwargs == {
            "host": "myhost",
            "port": 6379,
            "db": 0,
            "password": None,
        }

    def test_quoted_hostname(self):
        pool = ConnectionPool.from_url(
            "redis://my %2F host %2B%3D+", decode_components=True
        )
        assert pool.connection_class == Connection
        assert pool.connection_kwargs == {
            "host": "my / host +=+",
            "port": 6379,
            "db": 0,
            "password": None,
        }

    def test_port(self):
        pool = ConnectionPool.from_url("redis://localhost:6380")
        assert pool.connection_class == Connection
        assert pool.connection_kwargs == {
            "host": "localhost",
            "port": 6380,
            "db": 0,
            "password": None,
        }

    def test_password(self):
        pool = ConnectionPool.from_url("redis://:mypassword@localhost")
        assert pool.connection_class == Connection
        assert pool.connection_kwargs == {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": "mypassword",
        }

    def test_quoted_password(self):
        pool = ConnectionPool.from_url(
            "redis://:%2Fmypass%2F%2B word%3D%24+@localhost", decode_components=True
        )
        assert pool.connection_class == Connection
        assert pool.connection_kwargs == {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": "/mypass/+ word=$+",
        }

    def test_quoted_path(self):
        pool = ConnectionPool.from_url(
            "unix://:mypassword@/my%2Fpath%2Fto%2F..%2F+_%2B%3D%24ocket",
            decode_components=True,
        )
        assert pool.connection_class == UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            "path": "/my/path/to/../+_+=$ocket",
            "db": 0,
            "password": "mypassword",
        }

    def test_db_as_argument(self):
        pool = ConnectionPool.from_url("redis://localhost", db="1")
        assert pool.connection_class == Connection
        assert pool.connection_kwargs == {
            "host": "localhost",
            "port": 6379,
            "db": 1,
            "password": None,
        }

    def test_db_in_path(self):
        pool = ConnectionPool.from_url("redis://localhost/2", db="1")
        assert pool.connection_class == Connection
        assert pool.connection_kwargs == {
            "host": "localhost",
            "port": 6379,
            "db": 2,
            "password": None,
        }

    def test_db_in_querystring(self):
        pool = ConnectionPool.from_url("redis://localhost/2?db=3", db="1")
        assert pool.connection_class == Connection
        assert pool.connection_kwargs == {
            "host": "localhost",
            "port": 6379,
            "db": 3,
            "password": None,
        }

    def test_extra_querystring_options(self):
        pool = ConnectionPool.from_url("redis://localhost?a=1&b=2")
        assert pool.connection_class == Connection
        assert pool.connection_kwargs == {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": None,
            "a": "1",
            "b": "2",
        }

    def test_client_creates_connection_pool(self):
        r = StrictRedis.from_url("redis://myhost")
        assert r.connection_pool.connection_class == Connection
        assert r.connection_pool.connection_kwargs == {
            "host": "myhost",
            "port": 6379,
            "db": 0,
            "password": None,
        }


class TestConnectionPoolUnixSocketURLParsing:
    def test_defaults(self):
        pool = ConnectionPool.from_url("unix:///socket")
        assert pool.connection_class == UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            "path": "/socket",
            "db": 0,
            "password": None,
        }

    def test_password(self):
        pool = ConnectionPool.from_url("unix://:mypassword@/socket")
        assert pool.connection_class == UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            "path": "/socket",
            "db": 0,
            "password": "mypassword",
        }

    def test_db_as_argument(self):
        pool = ConnectionPool.from_url("unix:///socket", db=1)
        assert pool.connection_class == UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            "path": "/socket",
            "db": 1,
            "password": None,
        }

    def test_db_in_querystring(self):
        pool = ConnectionPool.from_url("unix:///socket?db=2", db=1)
        assert pool.connection_class == UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            "path": "/socket",
            "db": 2,
            "password": None,
        }

    def test_extra_querystring_options(self):
        pool = ConnectionPool.from_url("unix:///socket?a=1&b=2")
        assert pool.connection_class == UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            "path": "/socket",
            "db": 0,
            "password": None,
            "a": "1",
            "b": "2",
        }
