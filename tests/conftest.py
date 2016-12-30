#!/usr/bin/python
# -*- coding: utf-8 -*-
import aredis
import asyncio
import pytest
from distutils.version import StrictVersion

__author__ = 'chenming@bilibili.com'


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
    check = StrictVersion(loop.run_until_complete(get_version())) < StrictVersion(min_version)
    return pytest.mark.skipif(check, reason="")


@pytest.fixture()
def r():
    return aredis.StrictRedis()
