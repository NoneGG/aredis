# -*- coding: utf-8 -*-

# python std lib
from __future__ import with_statement

import asyncio
import uuid

# 3rd party imports
import pytest
from mock import Mock, patch

# rediscluster imports
from coredis import ConnectionError, RedisCluster, RedisClusterException
from coredis.client import Redis
from coredis.nodemanager import HASH_SLOTS, NodeManager


def test_set_node_name(s):
    """
    Test that method sets ["name"] correctly
    """
    n = {"host": "127.0.0.1", "port": 7000}
    s.connection_pool.nodes.set_node_name(n)
    assert "name" in n
    assert n["name"] == "127.0.0.1:7000"


def test_keyslot():
    """
    Test that method will compute correct key in all supported cases
    """
    n = NodeManager([{}])

    assert n.keyslot("foo") == 12182
    assert n.keyslot("{foo}bar") == 12182
    assert n.keyslot("{foo}") == 12182
    assert n.keyslot(1337) == 4314

    assert n.keyslot(125) == n.keyslot(b"125")
    assert n.keyslot(125) == n.keyslot("\x31\x32\x35")
    assert n.keyslot("大奖") == n.keyslot(b"\xe5\xa4\xa7\xe5\xa5\x96")
    assert n.keyslot("大奖") == n.keyslot(b"\xe5\xa4\xa7\xe5\xa5\x96")
    assert n.keyslot(1337.1234) == n.keyslot("1337.1234")
    assert n.keyslot(1337) == n.keyslot("1337")
    assert n.keyslot(b"abc") == n.keyslot("abc")
    assert n.keyslot("abc") == n.keyslot(str("abc"))
    assert n.keyslot(str("abc")) == n.keyslot(b"abc")


@pytest.mark.asyncio
async def test_init_slots_cache_not_all_slots(s, redis_cluster):
    """
    Test that if not all slots are covered it should raise an exception
    """

    with patch.object(NodeManager, "get_redis_link") as get_redis_link:
        cluster_slots_async = asyncio.Future()
        cluster_slots = {
            (0, 5459): [
                {
                    "host": "127.0.0.1",
                    "port": 7000,
                    "node_id": str(uuid.uuid4()),
                    "server_type": "master",
                },
                {
                    "host": "127.0.0.1",
                    "port": 7003,
                    "node_id": str(uuid.uuid4()),
                    "server_type": "slave",
                },
            ],
            (5461, 10922): [
                {
                    "host": "127.0.0.1",
                    "port": 7001,
                    "node_id": str(uuid.uuid4()),
                    "server_type": "master",
                },
                {
                    "host": "127.0.0.1",
                    "port": 7004,
                    "node_id": str(uuid.uuid4()),
                    "server_type": "slave",
                },
            ],
            (10923, 16383): [
                {
                    "host": "127.0.0.1",
                    "port": 7002,
                    "node_id": str(uuid.uuid4()),
                    "server_type": "master",
                },
                {
                    "host": "127.0.0.1",
                    "port": 7005,
                    "node_id": str(uuid.uuid4()),
                    "server_type": "slave",
                },
            ],
        }
        mock_redis = Mock()
        cluster_slots_async.set_result(cluster_slots)
        mock_redis.cluster_slots.return_value = cluster_slots_async

        config_get_async = asyncio.Future()
        config_get_async.set_result({"cluster-require-full-coverage": "yes"})

        mock_redis.config_get.return_value = config_get_async

        get_redis_link.return_value = mock_redis
        with pytest.raises(RedisClusterException) as ex:
            await s.connection_pool.initialize()

        assert str(ex.value).startswith(
            "Not all slots are covered after query all startup_nodes."
        )


@pytest.mark.asyncio
async def test_init_slots_cache_not_all_slots_not_require_full_coverage(
    s, redis_cluster
):
    """
    Test that if not all slots are covered it should raise an exception
    """
    with patch.object(Redis, "cluster_slots") as mock_cluster_slots:
        with patch.object(Redis, "config_get") as mock_config_get:
            mock_config_get.return_value = {"cluster-require-full-coverage": "no"}
            mock_cluster_slots.return_value = {
                (0, 5459): [
                    {
                        "host": "127.0.0.1",
                        "port": 7000,
                        "node_id": str(uuid.uuid4()),
                        "server_type": "master",
                    },
                    {
                        "host": "127.0.0.1",
                        "port": 7003,
                        "node_id": str(uuid.uuid4()),
                        "server_type": "slave",
                    },
                ],
                (5461, 10922): [
                    {
                        "host": "127.0.0.1",
                        "port": 7001,
                        "node_id": str(uuid.uuid4()),
                        "server_type": "master",
                    },
                    {
                        "host": "127.0.0.1",
                        "port": 7004,
                        "node_id": str(uuid.uuid4()),
                        "server_type": "slave",
                    },
                ],
                (10923, 16383): [
                    {
                        "host": "127.0.0.1",
                        "port": 7002,
                        "node_id": str(uuid.uuid4()),
                        "server_type": "master",
                    },
                    {
                        "host": "127.0.0.1",
                        "port": 7005,
                        "node_id": str(uuid.uuid4()),
                        "server_type": "slave",
                    },
                ],
            }

            await s.connection_pool.nodes.initialize()
            assert 5460 not in s.connection_pool.nodes.slots


@pytest.mark.asyncio
async def test_init_slots_cache(s, redis_cluster):
    """
    Test that slots cache can in initialized and all slots are covered
    """
    good_slots_resp = {
        (0, 5460): [
            {
                "host": "127.0.0.1",
                "port": 7000,
                "node_id": str(uuid.uuid4()),
                "server_type": "master",
            },
            {
                "host": "127.0.0.1",
                "port": 7003,
                "node_id": str(uuid.uuid4()),
                "server_type": "slave",
            },
        ],
        (5461, 10922): [
            {
                "host": "127.0.0.1",
                "port": 7001,
                "node_id": str(uuid.uuid4()),
                "server_type": "master",
            },
            {
                "host": "127.0.0.1",
                "port": 7004,
                "node_id": str(uuid.uuid4()),
                "server_type": "slave",
            },
        ],
        (10923, 16383): [
            {
                "host": "127.0.0.1",
                "port": 7002,
                "node_id": str(uuid.uuid4()),
                "server_type": "master",
            },
            {
                "host": "127.0.0.1",
                "port": 7005,
                "node_id": str(uuid.uuid4()),
                "server_type": "slave",
            },
        ],
    }

    with patch.object(Redis, "config_get") as mock_config_get:
        with patch.object(Redis, "cluster_slots") as mock_cluster_slots:
            mock_cluster_slots.return_value = good_slots_resp
            mock_config_get.return_value = {"cluster-require-full-coverage": "yes"}

            await s.connection_pool.nodes.initialize()
            assert len(s.connection_pool.nodes.slots) == HASH_SLOTS

            for slot_info, node_info in good_slots_resp.items():
                all_hosts = ["127.0.0.1", "127.0.0.2"]
                all_ports = [7000, 7001, 7002, 7003, 7004, 7005]
                slot_start = slot_info[0]
                slot_end = slot_info[1]

                for i in range(slot_start, slot_end + 1):
                    assert len(s.connection_pool.nodes.slots[i]) == len(node_info)
                    assert s.connection_pool.nodes.slots[i][0]["host"] in all_hosts
                    assert s.connection_pool.nodes.slots[i][1]["host"] in all_hosts
                    assert s.connection_pool.nodes.slots[i][0]["port"] in all_ports
                    assert s.connection_pool.nodes.slots[i][1]["port"] in all_ports

        assert len(s.connection_pool.nodes.nodes) == 6


def test_empty_startup_nodes():
    """
    It should not be possible to create a node manager with no nodes specified
    """
    with pytest.raises(RedisClusterException):
        NodeManager()

    with pytest.raises(RedisClusterException):
        NodeManager([])


@pytest.mark.asyncio
async def test_all_nodes(redis_cluster):
    """
    Set a list of nodes and it should be possible to iterate over all
    """
    n = NodeManager(startup_nodes=[{"host": "127.0.0.1", "port": 7000}])
    await n.initialize()

    nodes = [node for node in n.nodes.values()]

    for i, node in enumerate(n.all_nodes()):
        assert node in nodes


@pytest.mark.asyncio
async def test_all_nodes_masters(redis_cluster):
    """
    Set a list of nodes with random masters/slaves config and it shold be possible
    to iterate over all of them.
    """
    n = NodeManager(
        startup_nodes=[
            {"host": "127.0.0.1", "port": 7000},
            {"host": "127.0.0.1", "port": 7001},
        ]
    )
    await n.initialize()

    nodes = [node for node in n.nodes.values() if node["server_type"] == "master"]

    for node in n.all_primaries():
        assert node in nodes


def test_random_startup_node(redis_cluster):
    """
    Hard to test reliable for a random
    """
    s = [{"1": 1}, {"2": 2}, {"3": 3}]
    n = NodeManager(startup_nodes=s)
    random_node = n.random_startup_node()

    for i in range(0, 5):
        assert random_node in s


@pytest.mark.asyncio
async def test_cluster_slots_error(redis_cluster):
    """
    Check that exception is raised if initialize can't execute
    'CLUSTER SLOTS' command.
    """
    with patch.object(RedisCluster, "execute_command") as execute_command_mock:
        execute_command_mock.side_effect = Exception("foobar")

        n = NodeManager(startup_nodes=[{}])

        with pytest.raises(RedisClusterException):
            await n.initialize()


def test_set_node():
    """
    Test to update data in a slot.
    """
    expected = {
        "host": "127.0.0.1",
        "name": "127.0.0.1:7000",
        "port": 7000,
        "server_type": "master",
    }

    n = NodeManager(startup_nodes=[{}])
    assert len(n.slots) == 0, "no slots should exist"
    res = n.set_node(host="127.0.0.1", port=7000, server_type="master")
    assert res == expected
    assert n.nodes == {expected["name"]: expected}


@pytest.mark.asyncio
async def test_reset(redis_cluster):
    """
    Test that reset method resets variables back to correct default values.
    """

    class AsyncMock(Mock):
        def __await__(self):
            future = asyncio.Future(loop=asyncio.get_event_loop())
            future.set_result(self)
            result = yield from future

            return result

    n = NodeManager(startup_nodes=[{}])
    n.initialize = AsyncMock()
    await n.reset()
    assert n.initialize.call_count == 1


@pytest.mark.asyncio
async def test_cluster_one_instance(redis_cluster):
    """
    If the cluster exists of only 1 node then there is some hacks that must
    be validated they work.
    """
    with patch.object(Redis, "cluster_slots") as mock_cluster_slots:
        with patch.object(Redis, "config_get") as mock_config_get:

            mock_config_get.return_value = {"cluster-require-full-coverage": "yes"}
            mock_cluster_slots.return_value = {
                (0, 16383): [
                    {
                        "host": "",
                        "port": 7006,
                        "node_id": str(uuid.uuid4()),
                        "server_type": "master",
                    }
                ],
            }

            n = NodeManager(startup_nodes=[{"host": "127.0.0.1", "port": 7006}])
            await n.initialize()

            del n.nodes["127.0.0.1:7006"]["node_id"]
            assert n.nodes == {
                "127.0.0.1:7006": {
                    "host": "127.0.0.1",
                    "name": "127.0.0.1:7006",
                    "port": 7006,
                    "server_type": "master",
                }
            }

            assert len(n.slots) == 16384

            for i in range(0, 16384):
                assert n.slots[i] == [
                    {
                        "host": "127.0.0.1",
                        "name": "127.0.0.1:7006",
                        "port": 7006,
                        "server_type": "master",
                    }
                ]


@pytest.mark.asyncio
async def test_initialize_follow_cluster(redis_cluster):
    n = NodeManager(
        nodemanager_follow_cluster=True,
        startup_nodes=[{"host": "127.0.0.1", "port": 7000}],
    )
    n.orig_startup_nodes = None
    await n.initialize()


@pytest.mark.asyncio
async def test_init_with_down_node(redis_cluster):
    """
    If I can't connect to one of the nodes, everything should still work.
    But if I can't connect to any of the nodes, exception should be thrown.
    """

    def get_redis_link(host, port, decode_responses=False):
        if port == 7000:
            raise ConnectionError("mock connection error for 7000")

        return Redis(host=host, port=port, decode_responses=decode_responses)

    with patch.object(NodeManager, "get_redis_link", side_effect=get_redis_link):
        n = NodeManager(startup_nodes=[{"host": "127.0.0.1", "port": 7000}])
        with pytest.raises(RedisClusterException) as e:
            await n.initialize()
        assert "Redis Cluster cannot be connected" in str(e.value)
