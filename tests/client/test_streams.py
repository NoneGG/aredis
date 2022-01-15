#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest

from coredis.exceptions import RedisError, ResponseError


class TestStreams:
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xadd_with_wrong_id(self, r):
        with pytest.raises(RedisError):
            await r.xadd(
                "test_stream",
                {"k1": "v1", "k2": 1},
                stream_id=0,
                max_len=10,
                approximate=False,
            )

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xadd_without_given_id(self, r):
        stream_id = await r.xadd("test_stream", {"k1": "v1", "k2": 1})
        assert len(stream_id.decode().split("-")) == 2

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xadd_with_given_id(self, r):
        stream_id = await r.xadd(
            "test_stream", {"k1": "v1", "k2": 1}, stream_id="12321"
        )
        assert stream_id == b"12321-0"
        await r.flushdb()
        stream_id = await r.xadd(
            "test_stream", {"k1": "v1", "k2": 1}, stream_id="12321-0"
        )
        assert stream_id == b"12321-0"

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xadd_with_maxlen_accurately(self, r):
        for idx in range(10):
            await r.xadd(
                "test_stream", {"k1": "v1", "k2": 1}, max_len=2, approximate=False
            )
        # also test xlen here
        length = await r.xlen("test_stream")
        assert length == 2

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xadd_with_maxlen_approximately(self, r):
        for idx in range(10):
            await r.xadd(
                "test_stream", {"k1": "v1", "k2": 1}, max_len=2, approximate=True
            )
        length = await r.xlen("test_stream")
        assert length == 10

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xrange(self, r):
        for idx in range(1, 10):
            await r.xadd(
                "test_stream",
                {"k1": "v1", "k2": 1},
                stream_id=idx,
                max_len=10,
                approximate=False,
            )
        entries = await r.xrange("test_stream", count=5)
        assert (
            len(entries) == 5
            and isinstance(entries, list)
            and isinstance(entries[0], tuple)
        )
        entries = await r.xrange("test_stream", start="2", end="3", count=3)
        assert len(entries) == 2 and entries[0][0] == b"2-0"

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xrevrange(self, r):
        for idx in range(1, 10):
            await r.xadd(
                "test_stream",
                {"k1": "v1", "k2": 1},
                stream_id=idx,
                max_len=10,
                approximate=False,
            )
        entries = await r.xrevrange("test_stream", count=5)
        assert (
            len(entries) == 5
            and isinstance(entries, list)
            and isinstance(entries[0], tuple)
        )
        entries = await r.xrevrange("test_stream", start="2", end="3", count=3)
        assert len(entries) == 0
        entries = await r.xrevrange("test_stream", start="3", end="2", count=3)
        assert len(entries) == 2 and entries[0][0] == b"3-0"

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xread(self, r):
        for idx in range(1, 10):
            await r.xadd("test_stream", {"k1": "v1", "k2": 1}, stream_id=idx)
        entries = await r.xread(count=5, block=10, test_stream="0")
        assert len(entries[b"test_stream"]) == 5
        entries = await r.xread(count=10, block=10, test_stream="$")
        assert not entries
        entries = await r.xread(count=10, block=10, test_stream="2")
        assert entries and len(entries[b"test_stream"]) == 7
        assert entries[b"test_stream"][0] == (b"3-0", {b"k1": b"v1", b"k2": b"1"})

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xreadgroup(self, r):
        for idx in range(1, 10):
            await r.xadd("test_stream", {"k1": "v1", "k2": 1}, stream_id=idx)
        # read from group does not exist
        with pytest.raises(ResponseError):
            await r.xreadgroup(
                "wrong_group", "lalala", count=10, block=10, test_stream="1"
            )
        assert await r.xgroup_create("test_stream", "test_group", "0") is True
        entries = await r.xreadgroup(
            "test_group", "consumer1", count=5, test_stream=">"
        )
        assert len(entries[b"test_stream"]) == 5

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xgroup_create(self, r):
        for idx in range(1, 10):
            await r.xadd("test_stream", {"k1": "v1", "k2": 1}, stream_id=idx)
        with pytest.raises(ResponseError):
            await r.xgroup_create("wrong_group", "test_group")
        res = await r.xgroup_create("test_stream", "test_group")
        assert res is True
        group_info = await r.xinfo_groups("test_stream")
        assert len(group_info) == 1
        assert group_info[0][b"name"] == b"test_group"

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xgroup_set_id(self, r):
        for idx in range(1, 10):
            await r.xadd("test_stream", {"k1": "v1", "k2": 1}, stream_id=idx)
        assert await r.xgroup_create("test_stream", "test_group", "$") is True
        entries = await r.xreadgroup(
            "test_group", "consumer1", count=5, test_stream="1"
        )
        assert len(entries[b"test_stream"]) == 0
        group_info = await r.xinfo_groups("test_stream")
        assert group_info[0][b"pending"] == 0
        assert await r.xgroup_set_id("test_stream", "test_group", "0") is True
        await r.xreadgroup("test_group", "consumer1", count=5, test_stream=">")
        group_info = await r.xinfo_groups("test_stream")
        assert group_info[0][b"pending"] == 5

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xgroup_destroy(self, r):
        await r.xadd("test_stream", {"k1": "v1", "k2": 1})
        assert await r.xgroup_create("test_stream", "test_group") is True
        group_info = await r.xinfo_groups("test_stream")
        assert len(group_info) == 1
        assert group_info[0][b"name"] == b"test_group"
        assert await r.xgroup_destroy("test_stream", "test_group") == 1
        group_info = await r.xinfo_groups("test_stream")
        assert len(group_info) == 0

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xgroup_del_consumer(self, r):
        await r.xadd("test_stream", {"k1": "v1", "k2": 1})
        assert await r.xgroup_create("test_stream", "test_group") is True
        await r.xreadgroup("test_group", "consumer1", count=5, test_stream="1")
        group_info = await r.xinfo_groups("test_stream")
        assert len(group_info) == 1
        assert group_info[0][b"consumers"] == 1
        consumer_info = await r.xinfo_consumers("test_stream", "test_group")
        assert len(consumer_info) == 1
        assert consumer_info[0][b"name"] == b"consumer1"
        await r.xgroup_del_consumer("test_stream", "test_group", "consumer1")
        consumer_info = await r.xinfo_consumers("test_stream", "test_group")
        assert len(consumer_info) == 0

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xpending(self, r):
        for idx in range(1, 10):
            await r.xadd("test_stream", {"k1": "v1", "k2": 1}, stream_id=idx)
        assert await r.xgroup_create("test_stream", "test_group", "$") is True
        entries = await r.xreadgroup(
            "test_group", "consumer1", count=5, test_stream="1"
        )
        assert len(entries[b"test_stream"]) == 0
        group_info = await r.xinfo_groups("test_stream")
        assert group_info[0][b"pending"] == 0
        assert (
            len(
                await r.xpending(
                    "test_stream", "test_group", count=10, consumer="consumer1"
                )
            )
            == 0
        )
        assert await r.xgroup_set_id("test_stream", "test_group", "0") is True
        await r.xreadgroup("test_group", "consumer1", count=5, test_stream=">")
        group_info = await r.xinfo_groups("test_stream")
        assert group_info[0][b"pending"] == 5
        assert (
            len(
                await r.xpending(
                    "test_stream", "test_group", count=10, consumer="consumer1"
                )
            )
            == 5
        )
        xpending_entries_in_range = await r.xpending(
            "test_stream",
            "test_group",
            start="2",
            end="2",
            count=10,
            consumer="consumer1",
        )
        assert len(xpending_entries_in_range) == 1
        assert xpending_entries_in_range[0][0] == b"2-0"
