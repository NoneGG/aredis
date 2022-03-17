import pytest

from coredis import PureToken
from coredis.exceptions import RedisError, ResponseError
from tests.conftest import targets


async def get_stream_message(client, stream, message_id):
    "Fetch a stream message and format it as a (message_id, fields) pair"
    response = await client.xrange(stream, start=message_id, end=message_id)
    assert len(response) == 1
    return response[0]


@targets("redis_basic")
@pytest.mark.asyncio()
class TestStreams:
    async def test_xadd_with_wrong_id(self, client):
        with pytest.raises(RedisError):
            await client.xadd(
                "test_stream",
                identifier="0",
                field_values={"k1": "v1", "k2": "1"},
                trim_strategy=PureToken.MAXLEN,
                trim_operator=PureToken.APPROXIMATELY,
                threshold=10,
            )

    async def test_xadd_without_given_id(self, client):
        identifier = await client.xadd(
            "test_stream", field_values={"k1": "v1", "k2": "1"}
        )
        assert len(identifier.split("-")) == 2

    async def test_xadd_with_given_id(self, client):
        identifier = await client.xadd(
            "test_stream", field_values={"k1": "v1", "k2": "1"}, identifier="12321"
        )
        assert identifier == "12321-0"
        await client.flushdb()
        identifier = await client.xadd(
            "test_stream", field_values={"k1": "v1", "k2": "1"}, identifier="12321-0"
        )
        assert identifier == "12321-0"

    async def test_xadd_with_maxlen_accurately(self, client):
        for idx in range(10):
            await client.xadd(
                "test_stream",
                field_values={"k1": "v1", "k2": "1"},
                trim_strategy=PureToken.MAXLEN,
                trim_operator=PureToken.EQUAL,
                threshold=2,
            )
        # also test xlen here
        length = await client.xlen("test_stream")
        assert length == 2

    async def test_xadd_with_maxlen_approximately(self, client):
        for idx in range(10):
            await client.xadd(
                "test_stream",
                field_values={"k1": "v1", "k2": "1"},
                trim_strategy=PureToken.MAXLEN,
                trim_operator=PureToken.APPROXIMATELY,
                threshold=2,
            )
        length = await client.xlen("test_stream")
        assert length == 10

    @pytest.mark.min_server_version("5.0.0")
    async def test_xclaim(self, client):
        stream = "stream"
        group = "group"
        consumer1 = "consumer1"
        consumer2 = "consumer2"
        message_id = await client.xadd(stream, {"john": "wick"})
        message = await get_stream_message(client, stream, message_id)
        await client.xgroup_create(stream, group, "0")

        # trying to claim a message that isn't already pending doesn't
        # do anything
        response = await client.xclaim(stream, group, consumer2, 0, [message_id])
        assert response == ()

        # read the group as consumer1 to initially claim the messages
        await client.xreadgroup(group, consumer1, streams={stream: ">"})

        # claim the message as consumer2
        response = await client.xclaim(
            stream,
            group,
            consumer2,
            0,
            [message_id],
        )
        assert response[0] == message

        # reclaim the message as consumer1, but use the justid argument
        # which only returns message ids
        assert await client.xclaim(
            stream,
            group,
            consumer1,
            0,
            [message_id],
            justid=True,
        ) == (message_id,)

    @pytest.mark.min_server_version("6.2.0")
    async def test_xautoclaim(self, client):
        stream = "stream"
        group = "group"
        consumer1 = "consumer1"
        consumer2 = "consumer2"

        message_id1 = await client.xadd(stream, {"john": "wick"})
        message_id2 = await client.xadd(stream, {"johny": "deff"})
        message = await get_stream_message(client, stream, message_id1)
        await client.xgroup_create(stream, group, "0")

        # trying to claim a message that isn't already pending doesn't
        # do anything
        response = await client.xautoclaim(stream, group, consumer2, 0, "0")
        assert response == ("0-0", (), ())

        # read the group as consumer1 to initially claim the messages
        await client.xreadgroup(group, consumer1, streams={stream: ">"})

        # claim one message as consumer2
        response = await client.xautoclaim(stream, group, consumer2, 0, "0", count=1)
        assert response[1] == (message,)

        # reclaim the messages as consumer1, but use the justid argument
        # which only returns message ids
        assert (await client.xautoclaim(stream, group, consumer1, 0, "0", justid=True))[
            1
        ] == (message_id1, message_id2)
        assert (
            await client.xautoclaim(
                stream, group, consumer1, 0, message_id2, justid=True
            )
        )[1] == (message_id2,)

    async def test_xrange(self, client):
        for idx in range(1, 10):
            await client.xadd(
                "test_stream",
                field_values={"k1": "v1", "k2": "1"},
                identifier=str(idx),
                trim_strategy=PureToken.MAXLEN,
                trim_operator=PureToken.EQUAL,
                threshold=10,
            )
        entries = await client.xrange("test_stream", count=5)
        assert (
            len(entries) == 5
            and isinstance(entries, tuple)
            and isinstance(entries[0], tuple)
        )
        entries = await client.xrange("test_stream", start="2", end="3", count=3)
        assert len(entries) == 2 and entries[0][0] == "2-0"
        assert entries[0][1] == {"k1": "v1", "k2": "1"}

    async def test_xrevrange(self, client):
        for idx in range(1, 10):
            await client.xadd(
                "test_stream",
                field_values={"k1": "v1", "k2": "1"},
                identifier=str(idx),
                trim_strategy=PureToken.MAXLEN,
                trim_operator=PureToken.EQUAL,
                threshold=10,
            )
        entries = await client.xrevrange("test_stream", count=5)
        assert (
            len(entries) == 5
            and isinstance(entries, tuple)
            and isinstance(entries[0], tuple)
        )
        entries = await client.xrevrange("test_stream", end="2", start="3", count=3)
        assert len(entries) == 0
        entries = await client.xrevrange("test_stream", end="3", start="2", count=3)
        assert len(entries) == 2 and entries[0][0] == "3-0"

    async def test_xread(self, client):
        for idx in range(1, 10):
            await client.xadd(
                "test_stream", field_values={"k1": "v1", "k2": "1"}, identifier=str(idx)
            )
        entries = await client.xread(count=5, block=10, streams=dict(test_stream="0"))
        assert len(entries["test_stream"]) == 5
        entries = await client.xread(count=10, block=10, streams=dict(test_stream="$"))
        assert not entries
        entries = await client.xread(count=10, block=10, streams=dict(test_stream="2"))
        assert entries and len(entries["test_stream"]) == 7
        assert entries["test_stream"][0] == ("3-0", {"k1": "v1", "k2": "1"})

    async def test_xreadgroup(self, client):
        for idx in range(1, 10):
            await client.xadd(
                "test_stream", field_values={"k1": "v1", "k2": "1"}, identifier=str(idx)
            )
        # read from group does not exist
        with pytest.raises(ResponseError):
            await client.xreadgroup(
                "wrong_group",
                "lalala",
                count=10,
                block=10,
                streams=dict(test_stream="1"),
            )
        assert await client.xgroup_create("test_stream", "test_group", "0") is True
        entries = await client.xreadgroup(
            "test_group", "consumer1", count=5, streams=dict(test_stream=">")
        )
        assert len(entries["test_stream"]) == 5

    async def test_xgroup_create(self, client):
        for idx in range(1, 10):
            await client.xadd(
                "test_stream", field_values={"k1": "v1", "k2": "1"}, identifier=str(idx)
            )
        with pytest.raises(ResponseError):
            await client.xgroup_create("wrong_group", "test_group")
        res = await client.xgroup_create("test_stream", "test_group")
        assert res is True
        group_info = await client.xinfo_groups("test_stream")
        assert len(group_info) == 1
        assert group_info[0]["name"] == "test_group"

    async def test_xgroup_setid(self, client):
        for idx in range(1, 10):
            await client.xadd(
                "test_stream", field_values={"k1": "v1", "k2": "1"}, identifier=str(idx)
            )
        assert await client.xgroup_create("test_stream", "test_group", "$") is True
        entries = await client.xreadgroup(
            "test_group", "consumer1", count=5, streams=dict(test_stream="1")
        )
        assert len(entries["test_stream"]) == 0
        group_info = await client.xinfo_groups("test_stream")
        assert group_info[0]["pending"] == 0
        assert await client.xgroup_setid("test_stream", "test_group", "0") is True
        await client.xreadgroup(
            "test_group", "consumer1", count=5, streams=dict(test_stream=">")
        )
        group_info = await client.xinfo_groups("test_stream")
        assert group_info[0]["pending"] == 5

    async def test_xgroup_destroy(self, client):
        await client.xadd("test_stream", field_values={"k1": "v1", "k2": "1"})
        assert await client.xgroup_create("test_stream", "test_group") is True
        group_info = await client.xinfo_groups("test_stream")
        assert len(group_info) == 1
        assert group_info[0]["name"] == "test_group"
        assert await client.xgroup_destroy("test_stream", "test_group") == 1
        group_info = await client.xinfo_groups("test_stream")
        assert len(group_info) == 0

    async def test_xgroup_delconsumer(self, client):
        await client.xadd("test_stream", field_values={"k1": "v1", "k2": "1"})
        assert await client.xgroup_create("test_stream", "test_group") is True
        await client.xreadgroup(
            "test_group", "consumer1", count=5, streams=dict(test_stream="1")
        )
        group_info = await client.xinfo_groups("test_stream")
        assert len(group_info) == 1
        assert group_info[0]["consumers"] == 1
        consumer_info = await client.xinfo_consumers("test_stream", "test_group")
        assert len(consumer_info) == 1
        assert consumer_info[0]["name"] == "consumer1"
        await client.xgroup_delconsumer("test_stream", "test_group", "consumer1")
        consumer_info = await client.xinfo_consumers("test_stream", "test_group")
        assert len(consumer_info) == 0

    async def test_xpending(self, client):
        for idx in range(1, 10):
            await client.xadd(
                "test_stream", field_values={"k1": "v1", "k2": "1"}, identifier=str(idx)
            )
        assert await client.xgroup_create("test_stream", "test_group", "$") is True
        entries = await client.xreadgroup(
            "test_group", "consumer1", count=5, streams=dict(test_stream="1")
        )
        assert len(entries["test_stream"]) == 0
        group_info = await client.xinfo_groups("test_stream")
        assert group_info[0]["pending"] == 0
        assert (
            len(
                await client.xpending(
                    "test_stream",
                    "test_group",
                    start="-",
                    end="+",
                    count=10,
                    consumer="consumer1",
                )
            )
            == 0
        )
        assert await client.xgroup_setid("test_stream", "test_group", "0") is True
        await client.xreadgroup(
            "test_group", "consumer1", count=5, streams=dict(test_stream=">")
        )
        group_info = await client.xinfo_groups("test_stream")
        assert group_info[0]["pending"] == 5
        assert (
            len(
                await client.xpending(
                    "test_stream",
                    "test_group",
                    start="-",
                    end="+",
                    count=10,
                    consumer="consumer1",
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
        assert xpending_entries_in_range[0].identifier == "2-0"

    async def test_xinfo_stream(self, client):
        assert await client.xadd(
            "test_stream", field_values={"k1": "v1", "k2": "1"}, identifier="1"
        )
        xinfo = await client.xinfo_stream("test_stream")
        assert xinfo["first_entry"] == ("1-0", {"k1": "v1", "k2": "1"})
        assert xinfo["last_entry"] == ("1-0", {"k1": "v1", "k2": "1"})
        assert await client.xadd(
            "test_stream", field_values={"k1": "v2", "k2": "2"}, identifier="1-1"
        )
        xinfo = await client.xinfo_stream("test_stream")
        assert xinfo["first_entry"] == ("1-0", {"k1": "v1", "k2": "1"})
        assert xinfo["last_entry"] == ("1-1", {"k1": "v2", "k2": "2"})
