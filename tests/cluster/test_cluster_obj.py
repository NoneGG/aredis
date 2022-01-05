# -*- coding: utf-8 -*-

# python std lib
from __future__ import with_statement
import asyncio
import re
import time

# rediscluster imports
from coredis import StrictRedisCluster, StrictRedis
from coredis.pool import ClusterConnectionPool
from coredis.exceptions import (
    RedisClusterException,
    MovedError,
    AskError,
    ClusterDownError,
)
from coredis.utils import b
from coredis.nodemanager import NodeManager
from tests.cluster.conftest import _get_client, skip_if_not_password_protected_nodes

# 3rd party imports
from mock import patch, Mock, MagicMock
import pytest


class DummyConnectionPool(ClusterConnectionPool):
    pass


class DummyConnection:
    pass


# def test_representation(r):
#     assert re.search('^StrictRedisCluster<[0-9\.\:\,].+>$', str(r))
#
#
# def test_blocked_strict_redis_args():
#     """
#     Some arguments should explicitly be blocked because they will not work in a cluster setup
#     """
#     params = {'startup_nodes': [{'host': '127.0.0.1', 'port': 7000}]}
#     c = StrictRedisCluster(**params)
#     assert c.connection_pool.connection_kwargs["stream_timeout"] == ClusterConnectionPool.RedisClusterDefaultTimeout
#
#     with pytest.raises(RedisClusterException) as ex:
#         _get_client(db=1)
#     assert str(ex.value).startswith("Argument 'db' is not possible to use in cluster mode")
#
#
# @skip_if_not_password_protected_nodes()
# def test_password_procted_nodes():
#     """
#     Test that it is possible to connect to password protected nodes
#     """
#     startup_nodes = [{"host": "127.0.0.1", "port": "7000"}]
#     password_protected_startup_nodes = [{"host": "127.0.0.1", "port": "7100"}]
#     with pytest.raises(RedisClusterException) as ex:
#         _get_client(startup_nodes=password_protected_startup_nodes)
#     assert str(ex.value).startswith("ERROR sending 'cluster slots' command to redis server:")
#     _get_client(startup_nodes=password_protected_startup_nodes, password='password_is_protected')
#
#     with pytest.raises(RedisClusterException) as ex:
#         _get_client(startup_nodes=startup_nodes, password='password_is_protected')
#     assert str(ex.value).startswith("ERROR sending 'cluster slots' command to redis server:")
#     _get_client(startup_nodes=startup_nodes)
#
#
# def test_host_port_startup_node():
#     """
#     Test that it is possible to use host & port arguments as startup node args
#     """
#     h = "192.168.0.1"
#     p = 7000
#     c = StrictRedisCluster(host=h, port=p)
#     assert {"host": h, "port": p} in c.connection_pool.nodes.startup_nodes
#
#
# def test_empty_startup_nodes():
#     """
#     Test that exception is raised when empty providing empty startup_nodes
#     """
#     with pytest.raises(RedisClusterException) as ex:
#         _get_client(init_slot_cache=False, startup_nodes=[])
#
#     assert str(ex.value).startswith("No startup nodes provided"), str(ex.value)
#
#
# def test_readonly_instance(ro):
#     """
#     Test that readonly_mode=True instance has ClusterReadOnlyConnectionPool
#     """
#     assert ro.connection_pool.readonly is True
#
#
# def test_custom_connectionpool():
#     """
#     Test that a custom connection pool will be used by StrictRedisCluster
#     """
#     h = "192.168.0.1"
#     p = 7001
#     pool = DummyConnectionPool(host=h, port=p, connection_class=DummyConnection,
#                                startup_nodes=[{'host': h, 'port': p}])
#     c = StrictRedisCluster(connection_pool=pool)
#     assert c.connection_pool is pool
#     assert c.connection_pool.connection_class == DummyConnection
#     assert {"host": h, "port": p} in c.connection_pool.nodes.startup_nodes
#
#
# @patch('coredis.StrictRedis', new=MagicMock())
# def test_skip_full_coverage_check():
#     """
#     Test if the cluster_require_full_coverage NodeManager method was not called with the flag activated
#     """
#     c = StrictRedisCluster("192.168.0.1", 7001, skip_full_coverage_check=True)
#     c.connection_pool.nodes.cluster_require_full_coverage = MagicMock()
#     c.connection_pool.nodes.initialize()
#     assert not c.connection_pool.nodes.cluster_require_full_coverage.called
#
#
# @pytest.mark.asyncio
# async def test_blocked_commands(r):
#     """
#     These commands should be blocked and raise RedisClusterException
#     """
#     blocked_commands = [
#         "CLIENT SETNAME", "SENTINEL GET-MASTER-ADDR-BY-NAME", 'SENTINEL MASTER', 'SENTINEL MASTERS',
#         'SENTINEL MONITOR', 'SENTINEL REMOVE', 'SENTINEL SENTINELS', 'SENTINEL SET',
#         'SENTINEL SLAVES', 'SHUTDOWN', 'SLAVEOF', 'SCRIPT KILL', 'MOVE', 'BITOP',
#     ]
#
#     for command in blocked_commands:
#         try:
#             await r.execute_command(command)
#         except RedisClusterException:
#             pass
#         else:
#             raise AssertionError("'RedisClusterException' not raised for method : {0}".format(command))
#
# @pytest.mark.asyncio
# async def test_blocked_transaction(r):
#     """
#     Method transaction is blocked/NYI and should raise exception on use
#     """
#     with pytest.raises(RedisClusterException) as ex:
#         await r.transaction(None)
#     assert str(ex.value).startswith("method StrictRedisCluster.transaction() is not implemented"), str(ex.value)
#
#
# @pytest.mark.asyncio
# async def test_cluster_of_one_instance():
#     """
#     Test a cluster that starts with only one redis server and ends up with
#     one server.
#
#     There is another redis server joining the cluster, hold slot 0, and
#     eventually quit the cluster. The StrictRedisCluster instance may get confused
#     when slots mapping and nodes change during the test.
#     """
#     with patch.object(StrictRedisCluster, 'parse_response') as parse_response_mock:
#         with patch.object(NodeManager, 'initialize', autospec=True) as init_mock:
#             async def side_effect(self, *args, **kwargs):
#                 async def ok_call(self, *args, **kwargs):
#                     assert self.port == 7007
#                     return "OK"
#                 parse_response_mock.side_effect = ok_call
#
#                 raise ClusterDownError('CLUSTERDOWN The cluster is down. Use CLUSTER INFO for more information')
#
#             async def side_effect_rebuild_slots_cache(self):
#                 # make new node cache that points to 7007 instead of 7006
#                 self.nodes = [{'host': '127.0.0.1', 'server_type': 'master', 'port': 7006, 'name': '127.0.0.1:7006'}]
#                 self.slots = {}
#
#                 for i in range(0, 16383):
#                     self.slots[i] = [{
#                         'host': '127.0.0.1',
#                         'server_type': 'master',
#                         'port': 7006,
#                         'name': '127.0.0.1:7006',
#                     }]
#
#                 # Second call should map all to 7007
#                 async def map_7007(self):
#                     self.nodes = [{'host': '127.0.0.1', 'server_type': 'master', 'port': 7007, 'name': '127.0.0.1:7007'}]
#                     self.slots = {}
#
#                     for i in range(0, 16383):
#                         self.slots[i] = [{
#                             'host': '127.0.0.1',
#                             'server_type': 'master',
#                             'port': 7007,
#                             'name': '127.0.0.1:7007',
#                         }]
#
#                 # First call should map all to 7006
#                 init_mock.side_effect = map_7007
#
#             parse_response_mock.side_effect = side_effect
#             init_mock.side_effect = side_effect_rebuild_slots_cache
#
#             rc = StrictRedisCluster(host='127.0.0.1', port=7006)
#             await rc.set('bar', 'foo')
#
#
# @pytest.mark.asyncio
# async def test_execute_command_errors(r):
#     """
#     If no command is given to `_determine_nodes` then exception
#     should be raised.
#
#     Test that if no key is provided then exception should be raised.
#     """
#     with pytest.raises(RedisClusterException) as ex:
#         await r.execute_command()
#     assert str(ex.value).startswith("Unable to determine command to use")
#
#     with pytest.raises(RedisClusterException) as ex:
#         await r.execute_command("GET")
#     assert str(ex.value).startswith("No way to dispatch this command to Redis Cluster. Missing key.")
#
#
# @pytest.mark.asyncio
# async def test_refresh_table_asap(monkeypatch):
#     """
#     If this variable is set externally, initialize() should be called.
#     """
#     async def return_none(*args, **kwargs):
#         return None
#     monkeypatch.setattr(ClusterConnectionPool, 'initialize', return_none)
#     monkeypatch.setattr(StrictRedisCluster, 'parse_response', return_none)
#     r = StrictRedisCluster(host="127.0.0.1", port=7000)
#     r.connection_pool.nodes.slots[12182] = [{
#         "host": "127.0.0.1",
#         "port": 7002,
#         "name": "127.0.0.1:7002",
#         "server_type": "master",
#     }]
#     r.refresh_table_asap = True
#
#     await r.set("foo", "bar")
#     assert r.refresh_table_asap is False
#     await r.flushdb()
#
#
# def find_node_ip_based_on_port(cluster_client, port):
#     for node_name, node_data in cluster_client.connection_pool.nodes.nodes.items():
#         if node_name.endswith(port):
#             return node_data['host']
#
# @pytest.mark.asyncio
# async def test_ask_redirection():
#     """
#     Test that the server handles ASK response.
#
#     At first call it should return a ASK ResponseError that will point
#     the client to the next server it should talk to.
#
#     Important thing to verify is that it tries to talk to the second node.
#     """
#     r = StrictRedisCluster(host="127.0.0.1", port=7000)
#     await r.connection_pool.initialize()
#     r.connection_pool.nodes.nodes['127.0.0.1:7001'] = {
#         'host': u'127.0.0.1',
#         'server_type': 'master',
#         'port': 7001,
#         'name': '127.0.0.1:7001'
#     }
#     with patch.object(StrictRedisCluster,
#                       'parse_response') as parse_response:
#
#         host_ip = find_node_ip_based_on_port(r, '7001')
#
#         async def ask_redirect_effect(connection, *args, **options):
#             async def ok_response(connection, *args, **options):
#                 assert connection.host == host_ip
#                 assert connection.port == 7001
#
#                 return "MOCK_OK"
#             parse_response.side_effect = ok_response
#             raise AskError("1337 {0}:7001".format(host_ip))
#
#         parse_response.side_effect = ask_redirect_effect
#         assert await r.set("foo", "bar") == "MOCK_OK"


@pytest.mark.asyncio
async def test_pipeline_ask_redirection():
    """
    Test that the server handles ASK response when used in pipeline.

    At first call it should return a ASK ResponseError that will point
    the client to the next server it should talk to.

    Important thing to verify is that it tries to talk to the second node.
    """
    r = StrictRedisCluster(host="127.0.0.1", port=7000)
    with patch.object(StrictRedisCluster, "parse_response") as parse_response:

        async def response(connection, *args, **options):
            async def response(connection, *args, **options):
                async def response(connection, *args, **options):
                    assert connection.host == "127.0.0.1"
                    assert connection.port == 7001
                    return "MOCK_OK"

                parse_response.side_effect = response
                raise AskError("12182 127.0.0.1:7001")

            parse_response.side_effect = response
            raise AskError("12182 127.0.0.1:7001")

        parse_response.side_effect = response

        p = await r.pipeline()
        await p.connection_pool.initialize()
        p.connection_pool.nodes.nodes["127.0.0.1:7001"] = {
            "host": u"127.0.0.1",
            "server_type": "master",
            "port": 7001,
            "name": "127.0.0.1:7001",
        }
        await p.set("foo", "bar")
        assert await p.execute() == ["MOCK_OK"]


@pytest.mark.asyncio
async def test_moved_redirection():
    """
    Test that the client handles MOVED response.

    At first call it should return a MOVED ResponseError that will point
    the client to the next server it should talk to.

    Important thing to verify is that it tries to talk to the second node.
    """
    r0 = StrictRedisCluster(host="127.0.0.1", port=7000)
    r2 = StrictRedisCluster(host="127.0.0.1", port=7002)
    await r0.flushdb()
    await r2.flushdb()
    assert await r0.set("foo", "bar")
    assert await r2.get("foo") == b"bar"


@pytest.mark.asyncio
async def test_moved_redirection_pipeline(monkeypatch):
    """
    Test that the server handles MOVED response when used in pipeline.

    At first call it should return a MOVED ResponseError that will point
    the client to the next server it should talk to.

    Important thing to verify is that it tries to talk to the second node.
    """
    r0 = StrictRedisCluster(host="127.0.0.1", port=7000)
    r2 = StrictRedisCluster(host="127.0.0.1", port=7002)
    await r0.flushdb()
    await r2.flushdb()
    p = await r0.pipeline()
    await p.set("foo", "bar")
    assert await p.execute() == [True]
    assert await r2.get("foo") == b"bar"


async def assert_moved_redirection_on_slave(sr, connection_pool_cls, cluster_obj):
    """
    """
    # we assume this key is set on 127.0.0.1:7000(7003)
    await sr.set("foo16706", "foo")
    await asyncio.sleep(1)
    with patch.object(connection_pool_cls, "get_node_by_slot") as return_slave_mock:
        return_slave_mock.return_value = {
            "name": "127.0.0.1:7004",
            "host": "127.0.0.1",
            "port": 7004,
            "server_type": "slave",
        }

        master_value = {
            "host": "127.0.0.1",
            "name": "127.0.0.1:7000",
            "port": 7000,
            "server_type": "master",
        }
        with patch.object(
            ClusterConnectionPool, "get_master_node_by_slot"
        ) as return_master_mock:
            return_master_mock.return_value = master_value
            assert await cluster_obj.get("foo16706") == b("foo")
            assert return_slave_mock.call_count == 1


@pytest.mark.asyncio
async def test_moved_redirection_on_slave_with_default_client(sr):
    """
    Test that the client is redirected normally with default
    (readonly_mode=False) client even when we connect always to slave.
    """
    await assert_moved_redirection_on_slave(
        sr,
        ClusterConnectionPool,
        StrictRedisCluster(host="127.0.0.1", port=7000, reinitialize_steps=1),
    )


@pytest.mark.asyncio
async def test_moved_redirection_on_slave_with_readonly_mode_client(sr):
    """
    Ditto with READONLY mode.
    """
    await assert_moved_redirection_on_slave(
        sr,
        ClusterConnectionPool,
        StrictRedisCluster(
            host="127.0.0.1", port=7000, readonly=True, reinitialize_steps=1
        ),
    )


@pytest.mark.asyncio
async def test_access_correct_slave_with_readonly_mode_client(sr):
    """
    Test that the client can get value normally with readonly mode
    when we connect to correct slave.
    """

    # we assume this key is set on 127.0.0.1:7000(7003)
    await sr.set("foo16706", "foo")
    await asyncio.sleep(1)

    with patch.object(ClusterConnectionPool, "get_node_by_slot") as return_slave_mock:
        return_slave_mock.return_value = {
            "name": "127.0.0.1:7004",
            "host": "127.0.0.1",
            "port": 7004,
            "server_type": "slave",
        }

        master_value = {
            "host": "127.0.0.1",
            "name": "127.0.0.1:7000",
            "port": 7000,
            "server_type": "master",
        }
        with patch.object(
            ClusterConnectionPool, "get_master_node_by_slot", return_value=master_value
        ) as return_master_mock:
            readonly_client = StrictRedisCluster(
                host="127.0.0.1", port=7000, readonly=True
            )
            assert b("foo") == await readonly_client.get("foo16706")
            readonly_client = StrictRedisCluster.from_url(
                url="redis://127.0.0.1:7000/0", readonly=True
            )
            assert b("foo") == await readonly_client.get("foo16706")
