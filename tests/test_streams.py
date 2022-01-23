import pytest

from coredis.exceptions import RedisError, ResponseError
from tests.conftest import targets


@targets("redis_basic")
@pytest.mark.asyncio()
class TestStreams:
    async def test_xadd_with_wrong_id(self, client):
        with pytest.raises(RedisError):
            await client.xadd(
                "test_stream",
                {"k1": "v1", "k2": 1},
                stream_id=0,
                max_len=10,
                approximate=False,
            )

    async def test_xadd_without_given_id(self, client):
        stream_id = await client.xadd("test_stream", {"k1": "v1", "k2": 1})
        assert len(stream_id.decode().split("-")) == 2

    async def test_xadd_with_given_id(self, client):
        stream_id = await client.xadd(
            "test_stream", {"k1": "v1", "k2": 1}, stream_id="12321"
        )
        assert stream_id == b"12321-0"
        await client.flushdb()
        stream_id = await client.xadd(
            "test_stream", {"k1": "v1", "k2": 1}, stream_id="12321-0"
        )
        assert stream_id == b"12321-0"

    async def test_xadd_with_maxlen_accurately(self, client):
        for idx in range(10):
            await client.xadd(
                "test_stream", {"k1": "v1", "k2": 1}, max_len=2, approximate=False
            )
        # also test xlen here
        length = await client.xlen("test_stream")
        assert length == 2

    async def test_xadd_with_maxlen_approximately(self, client):
        for idx in range(10):
            await client.xadd(
                "test_stream", {"k1": "v1", "k2": 1}, max_len=2, approximate=True
            )
        length = await client.xlen("test_stream")
        assert length == 10

    async def test_xrange(self, client):
        for idx in range(1, 10):
            await client.xadd(
                "test_stream",
                {"k1": "v1", "k2": 1},
                stream_id=idx,
                max_len=10,
                approximate=False,
            )
        entries = await client.xrange("test_stream", count=5)
        assert (
            len(entries) == 5
            and isinstance(entries, list)
            and isinstance(entries[0], tuple)
        )
        entries = await client.xrange("test_stream", start="2", end="3", count=3)
        assert len(entries) == 2 and entries[0][0] == b"2-0"

    async def test_xrevrange(self, client):
        for idx in range(1, 10):
            await client.xadd(
                "test_stream",
                {"k1": "v1", "k2": 1},
                stream_id=idx,
                max_len=10,
                approximate=False,
            )
        entries = await client.xrevrange("test_stream", count=5)
        assert (
            len(entries) == 5
            and isinstance(entries, list)
            and isinstance(entries[0], tuple)
        )
        entries = await client.xrevrange("test_stream", start="2", end="3", count=3)
        assert len(entries) == 0
        entries = await client.xrevrange("test_stream", start="3", end="2", count=3)
        assert len(entries) == 2 and entries[0][0] == b"3-0"

    async def test_xread(self, client):
        for idx in range(1, 10):
            await client.xadd("test_stream", {"k1": "v1", "k2": 1}, stream_id=idx)
        entries = await client.xread(count=5, block=10, test_stream="0")
        assert len(entries[b"test_stream"]) == 5
        entries = await client.xread(count=10, block=10, test_stream="$")
        assert not entries
        entries = await client.xread(count=10, block=10, test_stream="2")
        assert entries and len(entries[b"test_stream"]) == 7
        assert entries[b"test_stream"][0] == (b"3-0", {b"k1": b"v1", b"k2": b"1"})

    async def test_xreadgroup(self, client):
        for idx in range(1, 10):
            await client.xadd("test_stream", {"k1": "v1", "k2": 1}, stream_id=idx)
        # read from group does not exist
        with pytest.raises(ResponseError):
            await client.xreadgroup(
                "wrong_group", "lalala", count=10, block=10, test_stream="1"
            )
        assert await client.xgroup_create("test_stream", "test_group", "0") is True
        entries = await client.xreadgroup(
            "test_group", "consumer1", count=5, test_stream=">"
        )
        assert len(entries[b"test_stream"]) == 5

    async def test_xgroup_create(self, client):
        for idx in range(1, 10):
            await client.xadd("test_stream", {"k1": "v1", "k2": 1}, stream_id=idx)
        with pytest.raises(ResponseError):
            await client.xgroup_create("wrong_group", "test_group")
        res = await client.xgroup_create("test_stream", "test_group")
        assert res is True
        group_info = await client.xinfo_groups("test_stream")
        assert len(group_info) == 1
        assert group_info[0][b"name"] == b"test_group"

    async def test_xgroup_set_id(self, client):
        for idx in range(1, 10):
            await client.xadd("test_stream", {"k1": "v1", "k2": 1}, stream_id=idx)
        assert await client.xgroup_create("test_stream", "test_group", "$") is True
        entries = await client.xreadgroup(
            "test_group", "consumer1", count=5, test_stream="1"
        )
        assert len(entries[b"test_stream"]) == 0
        group_info = await client.xinfo_groups("test_stream")
        assert group_info[0][b"pending"] == 0
        assert await client.xgroup_set_id("test_stream", "test_group", "0") is True
        await client.xreadgroup("test_group", "consumer1", count=5, test_stream=">")
        group_info = await client.xinfo_groups("test_stream")
        assert group_info[0][b"pending"] == 5

    async def test_xgroup_destroy(self, client):
        await client.xadd("test_stream", {"k1": "v1", "k2": 1})
        assert await client.xgroup_create("test_stream", "test_group") is True
        group_info = await client.xinfo_groups("test_stream")
        assert len(group_info) == 1
        assert group_info[0][b"name"] == b"test_group"
        assert await client.xgroup_destroy("test_stream", "test_group") == 1
        group_info = await client.xinfo_groups("test_stream")
        assert len(group_info) == 0

    async def test_xgroup_del_consumer(self, client):
        await client.xadd("test_stream", {"k1": "v1", "k2": 1})
        assert await client.xgroup_create("test_stream", "test_group") is True
        await client.xreadgroup("test_group", "consumer1", count=5, test_stream="1")
        group_info = await client.xinfo_groups("test_stream")
        assert len(group_info) == 1
        assert group_info[0][b"consumers"] == 1
        consumer_info = await client.xinfo_consumers("test_stream", "test_group")
        assert len(consumer_info) == 1
        assert consumer_info[0][b"name"] == b"consumer1"
        await client.xgroup_del_consumer("test_stream", "test_group", "consumer1")
        consumer_info = await client.xinfo_consumers("test_stream", "test_group")
        assert len(consumer_info) == 0

    async def test_xpending(self, client):
        for idx in range(1, 10):
            await client.xadd("test_stream", {"k1": "v1", "k2": 1}, stream_id=idx)
        assert await client.xgroup_create("test_stream", "test_group", "$") is True
        entries = await client.xreadgroup(
            "test_group", "consumer1", count=5, test_stream="1"
        )
        assert len(entries[b"test_stream"]) == 0
        group_info = await client.xinfo_groups("test_stream")
        assert group_info[0][b"pending"] == 0
        assert (
            len(
                await client.xpending(
                    "test_stream", "test_group", count=10, consumer="consumer1"
                )
            )
            == 0
        )
        assert await client.xgroup_set_id("test_stream", "test_group", "0") is True
        await client.xreadgroup("test_group", "consumer1", count=5, test_stream=">")
        group_info = await client.xinfo_groups("test_stream")
        assert group_info[0][b"pending"] == 5
        assert (
            len(
                await client.xpending(
                    "test_stream", "test_group", count=10, consumer="consumer1"
                )
            )
            == 5
        )
        xpending_entries_in_range = await client.xpending(
            "test_stream",
            "test_group",
            start="2",
            end="2",
            count=10,
            consumer="consumer1",
        )
        assert len(xpending_entries_in_range) == 1
        assert xpending_entries_in_range[0][0] == b"2-0"
