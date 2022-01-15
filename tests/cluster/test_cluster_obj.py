# -*- coding: utf-8 -*-

# python std lib
from __future__ import with_statement

import asyncio

import pytest

# 3rd party imports
from mock import patch

# rediscluster imports
from coredis import StrictRedisCluster
from coredis.exceptions import AskError
from coredis.pool import ClusterConnectionPool
from coredis.utils import b


class DummyConnectionPool(ClusterConnectionPool):
    pass


class DummyConnection:
    pass


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
    """ """
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
        ):
            readonly_client = StrictRedisCluster(
                host="127.0.0.1", port=7000, readonly=True
            )
            assert b("foo") == await readonly_client.get("foo16706")
            readonly_client = StrictRedisCluster.from_url(
                url="redis://127.0.0.1:7000/0", readonly=True
            )
            assert b("foo") == await readonly_client.get("foo16706")
