#!/usr/bin/python
# -*- coding: utf-8 -*-
import aredis
import asyncio
import pytest
import sys
from unittest.mock import Mock
from distutils.version import StrictVersion


_REDIS_VERSIONS = {}


async def get_version(**kwargs):
    params = {'host': 'localhost', 'port': 6379, 'db': 0}
    params.update(kwargs)
    key = '%s:%s' % (params['host'], params['port'])
    if key not in _REDIS_VERSIONS:
        client = aredis.StrictRedis(**params)
        _REDIS_VERSIONS[key] = (await client.info())['redis_version']
        client.connection_pool.disconnect()
    return _REDIS_VERSIONS[key]


def skip_if_server_version_lt(min_version):
    loop = asyncio.get_event_loop()
    version = StrictVersion(loop.run_until_complete(get_version()))
    check = version < StrictVersion(min_version)
    return pytest.mark.skipif(check, reason="")


def skip_python_vsersion_lt(min_version):
    min_version = tuple(map(int, min_version.split('.')))
    check = sys.version_info[:2] < min_version
    return pytest.mark.skipif(check, reason="")


@pytest.fixture()
def r(event_loop):
    return aredis.StrictRedis(loop=event_loop)


class AsyncMock(Mock):

    def __init__(self, *args, **kwargs):
        super(AsyncMock, self).__init__(*args, **kwargs)

    def __await__(self):
        future = asyncio.Future(loop=self.loop)
        future.set_result(self)
        result = yield from future
        return result

    @staticmethod
    def pack_response(response, *, loop):
        future = asyncio.Future(loop=loop)
        future.set_result(response)
        return future


def _gen_cluster_mock_resp(r, response, *, loop):
    mock_connection_pool = AsyncMock(loop=loop)
    connection = AsyncMock(loop=loop)
    connection.read_response.return_value = AsyncMock.pack_response(response, loop=loop)
    mock_connection_pool.get_connection.return_value = connection
    r.connection_pool = mock_connection_pool
    return r


@pytest.fixture()
def mock_cluster_resp_ok(event_loop):
    r = aredis.StrictRedis(loop=event_loop)
    return _gen_cluster_mock_resp(r, b'OK', loop=event_loop)


@pytest.fixture()
def mock_cluster_resp_int(event_loop):
    r = aredis.StrictRedis(loop=event_loop)
    return _gen_cluster_mock_resp(r, b'2', loop=event_loop)


@pytest.fixture()
def mock_cluster_resp_info(event_loop):
    r = aredis.StrictRedis(loop=event_loop)
    response = (b'cluster_state:ok\r\ncluster_slots_assigned:16384\r\n'
                b'cluster_slots_ok:16384\r\ncluster_slots_pfail:0\r\n'
                b'cluster_slots_fail:0\r\ncluster_known_nodes:7\r\n'
                b'cluster_size:3\r\ncluster_current_epoch:7\r\n'
                b'cluster_my_epoch:2\r\ncluster_stats_messages_sent:170262\r\n'
                b'cluster_stats_messages_received:105653\r\n')
    return _gen_cluster_mock_resp(r, response, loop=event_loop)


@pytest.fixture()
def mock_cluster_resp_nodes(event_loop):
    r = aredis.StrictRedis(loop=event_loop)
    response = (b'c8253bae761cb1ecb2b61857d85dfe455a0fec8b 172.17.0.7:7006 '
                b'slave aa90da731f673a99617dfe930306549a09f83a6b 0 '
                b'1447836263059 5 connected\n'
                b'9bd595fe4821a0e8d6b99d70faa660638a7612b3 172.17.0.7:7008 '
                b'master - 0 1447836264065 0 connected\n'
                b'aa90da731f673a99617dfe930306549a09f83a6b 172.17.0.7:7003 '
                b'myself,master - 0 0 2 connected 5461-10922\n'
                b'1df047e5a594f945d82fc140be97a1452bcbf93e 172.17.0.7:7007 '
                b'slave 19efe5a631f3296fdf21a5441680f893e8cc96ec 0 '
                b'1447836262556 3 connected\n'
                b'4ad9a12e63e8f0207025eeba2354bcf4c85e5b22 172.17.0.7:7005 '
                b'master - 0 1447836262555 7 connected 0-5460\n'
                b'19efe5a631f3296fdf21a5441680f893e8cc96ec 172.17.0.7:7004 '
                b'master - 0 1447836263562 3 connected 10923-16383\n'
                b'fbb23ed8cfa23f17eaf27ff7d0c410492a1093d6 172.17.0.7:7002 '
                b'master,fail - 1447829446956 1447829444948 1 disconnected\n'
                )
    return _gen_cluster_mock_resp(r, response, loop=event_loop)


@pytest.fixture()
def mock_cluster_resp_slaves(event_loop):
    r = aredis.StrictRedis(loop=event_loop)
    response = (b"['1df047e5a594f945d82fc140be97a1452bcbf93e 172.17.0.7:7007 "
                b"slave 19efe5a631f3296fdf21a5441680f893e8cc96ec 0 "
                b"1447836789290 3 connected']")
    return _gen_cluster_mock_resp(r, response, loop=event_loop)


@pytest.fixture()
def mock_cluster_resp_slots(event_loop):
    r = aredis.StrictRedis(loop=event_loop)
    response = ([[0, 5460, [b'172.17.0.2', 7000, b'90406a8afa09afb6b4aa614edc32b5d1c0eb22aa'],
                  [b'172.17.0.2', 7003, b'0c8f3cd0baf30357fc2f6e871f68f7d423aac931']],
                 [10923, 16383, [b'172.17.0.2', 7002, b'cc8417fdb2fef950092d8e310f521d8296293e96'],
                  [b'172.17.0.2', 7005, b'da700b467f4931b4241024a74bb858695304012b']],
                 [5461, 10922, [b'172.17.0.2', 7001, b'cab54cba256f159c1400ee80e29c37f256f46580'],
                  [b'172.17.0.2', 7004, b'f0674d2b02c7c0432c9f2bf0108255aaf20179be']]])
    return _gen_cluster_mock_resp(r, response, loop=event_loop)
