import pytest

import coredis


@pytest.fixture
def s(redis_cluster_server):
    cluster = coredis.StrictRedisCluster(
        startup_nodes=[{"host": "localhost", "port": 7000}]
    )
    assert cluster.connection_pool.nodes.slots == {}
    assert cluster.connection_pool.nodes.nodes == {}

    yield cluster

    cluster.connection_pool.disconnect()


@pytest.fixture
def sr(redis_cluster_server):
    cluster = coredis.StrictRedisCluster(
        startup_nodes=[{"host": "localhost", "port": 7000}], reinitialize_steps=1
    )
    yield cluster

    cluster.connection_pool.disconnect()


@pytest.fixture
def ro(redis_cluster_server):
    cluster = coredis.StrictRedisCluster(
        startup_nodes=[{"host": "localhost", "port": 7000}], readonly=True
    )
    yield cluster

    cluster.connection_pool.disconnect()
