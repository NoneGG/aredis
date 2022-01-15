#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
import time

import pytest

from coredis.cache import Cache, HerdCache


class TestCache:

    app = "test_cache"
    key = "test_key"
    data = {str(i): i for i in range(3)}

    def expensive_work(self, data):
        return data

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set(self, r):
        cache = Cache(r, self.app)
        res = await cache.set(self.key, self.expensive_work(self.data), self.data)
        assert res
        identity = cache._gen_identity(self.key, self.data)
        content = await r.get(identity)
        content = cache._unpack(content)
        assert content == self.data

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set_timeout(self, r, event_loop):
        cache = Cache(r, self.app)
        res = await cache.set(
            self.key, self.expensive_work(self.data), self.data, expire_time=1
        )
        assert res
        identity = cache._gen_identity(self.key, self.data)
        content = await r.get(identity)
        content = cache._unpack(content)
        assert content == self.data
        await asyncio.sleep(1.1)
        content = await r.get(identity)
        assert content is None

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set_with_plain_key(self, r):
        cache = Cache(r, self.app, identity_generator_class=None)
        res = await cache.set(
            self.key, self.expensive_work(self.data), self.data, expire_time=1
        )
        assert res
        identity = cache._gen_identity(self.key, self.data)
        assert identity == self.key
        content = await r.get(identity)
        content = cache._unpack(content)
        assert content == self.data

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_get(self, r):
        cache = Cache(r, self.app)
        res = await cache.set(
            self.key, self.expensive_work(self.data), self.data, expire_time=1
        )
        assert res
        content = await cache.get(self.key, self.data)
        assert content == self.data

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set_many(self, r):
        cache = Cache(r, self.app)
        res = await cache.set_many(self.expensive_work(self.data), self.data)
        assert res
        for key, value in self.data.items():
            assert await cache.get(key, self.data) == value

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_delete(self, r):
        cache = Cache(r, self.app)
        res = await cache.set(
            self.key, self.expensive_work(self.data), self.data, expire_time=1
        )
        assert res
        content = await cache.get(self.key, self.data)
        assert content == self.data
        res = await cache.delete(self.key, self.data)
        assert res
        content = await cache.get(self.key, self.data)
        assert content is None

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_delete_pattern(self, r):
        cache = Cache(r, self.app)
        await cache.set_many(self.expensive_work(self.data), self.data)
        res = await cache.delete_pattern("test_*", 10)
        assert res == 3
        content = await cache.get(self.key, self.data)
        assert content is None

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_ttl(self, r, event_loop):
        cache = Cache(r, self.app)
        await cache.set(
            self.key, self.expensive_work(self.data), self.data, expire_time=1
        )
        ttl = await cache.ttl(self.key, self.data)
        assert ttl > 0
        await asyncio.sleep(1.1)
        ttl = await cache.ttl(self.key, self.data)
        assert ttl < 0

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_exists(self, r, event_loop):
        cache = Cache(r, self.app)
        await cache.set(
            self.key, self.expensive_work(self.data), self.data, expire_time=1
        )
        exists = await cache.exist(self.key, self.data)
        assert exists is True
        await asyncio.sleep(1.1)
        exists = await cache.exist(self.key, self.data)
        assert exists is False


class TestHerdCache:

    app = "test_cache"
    key = "test_key"
    data = {str(i): i for i in range(3)}

    def expensive_work(self, data):
        return data

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set(self, r):
        cache = HerdCache(r, self.app, default_herd_timeout=1, extend_herd_timeout=1)
        now = int(time.time())
        res = await cache.set(self.key, self.expensive_work(self.data), self.data)
        assert res
        identity = cache._gen_identity(self.key, self.data)
        content = await r.get(identity)
        content, expect_expire_time = cache._unpack(content)
        # supposed equal to 1, but may there be latency
        assert expect_expire_time - now <= 1
        assert content == self.data

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_get(self, r):
        cache = HerdCache(r, self.app, default_herd_timeout=1, extend_herd_timeout=1)
        res = await cache.set(self.key, self.expensive_work(self.data), self.data)
        assert res
        content = await cache.get(self.key, self.data)
        assert content == self.data

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set_many(self, r):
        cache = HerdCache(r, self.app, default_herd_timeout=1, extend_herd_timeout=1)
        res = await cache.set_many(self.expensive_work(self.data), self.data)
        assert res
        for key, value in self.data.items():
            assert await cache.get(key, self.data) == value

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_herd(self, r, event_loop):
        now = int(time.time())
        cache = HerdCache(r, self.app, default_herd_timeout=1, extend_herd_timeout=1)
        await cache.set(self.key, self.expensive_work(self.data), self.data)
        await asyncio.sleep(1)
        # first get
        identity = cache._gen_identity(self.key, self.data)
        content = await r.get(identity)
        content, expect_expire_time = cache._unpack(content)
        assert now + 1 == expect_expire_time
        # HerdCach.get
        await asyncio.sleep(0.1)
        res = await cache.get(self.key, self.data)
        # first herd get will reset expire time and return None
        assert res is None
        # second get
        identity = cache._gen_identity(self.key, self.data)
        content = await r.get(identity)
        content, new_expire_time = cache._unpack(content)
        assert new_expire_time >= expect_expire_time + 1
