#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest
import asyncio
import json
from aredis.cache import Cache, HerdCache

__author__ = 'chenming@bilibili.com'


class TestCache(object):

    app = 'test_cache'
    key = 'test_key'
    data = {str(i): i for i in range(3)}

    @pytest.mark.asyncio
    async def test_set(self, r):
        await r.flushdb()
        cache = Cache(r, self.app)
        res = await cache.set(self.key, self.data)
        assert res
        identity = cache._gen_identity(self.key, self.data)
        content = await r.get(identity)
        content = cache._unpack(content)
        assert content == self.data

    @pytest.mark.asyncio
    async def test_set_timeout(self, r):
        await r.flushdb()
        cache = Cache(r, self.app)
        res = await cache.set(self.key, self.data, expire_time=1)
        assert res
        identity = cache._gen_identity(self.key, self.data)
        content = await r.get(identity)
        content = cache._unpack(content)
        assert content == self.data
        await asyncio.sleep(1)
        content = await r.get(identity)
        assert content is None

    @pytest.mark.asyncio
    async def test_set_with_plain_key(self, r):
        await r.flushdb()
        cache = Cache(r, self.app, identity_generator_class=None)
        res = await cache.set(self.key, self.data, expire_time=1)
        assert res
        identity = cache._gen_identity(self.key, self.data)
        assert identity == self.key
        content = await r.get(identity)
        content = cache._unpack(content)
        assert content == self.data

    @pytest.mark.asyncio
    async def test_get(self, r):
        await r.flushdb()
        cache = Cache(r, self.app)
        res = await cache.set(self.key, self.data)
        assert res
        content = await cache.get(self.key, self.data)
        assert content == self.data

    @pytest.mark.asyncio
    async def test_set_many(self, r):
        await r.flushdb()
        cache = Cache(r, self.app)
        res = await cache.set_many(self.data)
        assert res
        for key, value in self.data.items():
            assert await cache.get(key, value) == value


