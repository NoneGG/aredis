import pytest

from coredis import PureToken
from coredis.utils import iteritems, iterkeys
from tests.conftest import targets


@targets("redis_basic", "redis_cluster")
@pytest.mark.asyncio()
class TestList:
    async def test_blpop(self, client):
        await client.rpush("a{foo}", ["1", "2"])
        await client.rpush("b{foo}", ["3", "4"])
        assert await client.blpop(["b{foo}", "a{foo}"], timeout=1) == [
            "b{foo}",
            "3",
        ]
        assert await client.blpop(["b{foo}", "a{foo}"], timeout=1) == [
            "b{foo}",
            "4",
        ]
        assert await client.blpop(["b{foo}", "a{foo}"], timeout=1) == [
            "a{foo}",
            "1",
        ]
        assert await client.blpop(["b{foo}", "a{foo}"], timeout=1) == [
            "a{foo}",
            "2",
        ]
        assert await client.blpop(["b{foo}", "a{foo}"], timeout=1) is None
        await client.rpush("c{foo}", ["1"])
        assert await client.blpop(["c{foo}"], timeout=1) == ["c{foo}", "1"]

    async def test_brpop(self, client):
        await client.rpush("a{foo}", ["1", "2"])
        await client.rpush("b{foo}", ["3", "4"])
        assert await client.brpop(["b{foo}", "a{foo}"], timeout=1) == [
            "b{foo}",
            "4",
        ]
        assert await client.brpop(["b{foo}", "a{foo}"], timeout=1) == [
            "b{foo}",
            "3",
        ]
        assert await client.brpop(["b{foo}", "a{foo}"], timeout=1) == [
            "a{foo}",
            "2",
        ]
        assert await client.brpop(["b{foo}", "a{foo}"], timeout=1) == [
            "a{foo}",
            "1",
        ]
        assert await client.brpop(["b{foo}", "a{foo}"], timeout=1) is None
        await client.rpush("c{foo}", ["1"])
        assert await client.brpop(["c{foo}"], timeout=1) == ["c{foo}", "1"]

    async def test_brpoplpush(self, client):
        await client.rpush("a", ["1", "2"])
        await client.rpush("b", ["3", "4"])
        assert await client.brpoplpush("a", "b", timeout=1) == "2"
        assert await client.brpoplpush("a", "b", timeout=1) == "1"
        assert await client.brpoplpush("a", "b", timeout=1) is None
        assert await client.lrange("a", 0, -1) == []
        assert await client.lrange("b", 0, -1) == ["1", "2", "3", "4"]

    async def test_brpoplpush_empty_string(self, client):
        await client.rpush("a", [""])
        assert await client.brpoplpush("a", "b", timeout=1) == ""

    async def test_lindex(self, client):
        await client.rpush("a", ["1", "2", "3"])
        assert await client.lindex("a", 0) == "1"
        assert await client.lindex("a", 1) == "2"
        assert await client.lindex("a", 2) == "3"
        assert await client.lindex("a", 10) is None

    async def test_linsert(self, client):
        await client.rpush("a", ["1", "2", "3"])
        assert await client.linsert("a", PureToken.AFTER, "2", "2.5") == 4
        assert await client.lrange("a", 0, -1) == ["1", "2", "2.5", "3"]
        assert await client.linsert("a", PureToken.BEFORE, "2", "1.5") == 5
        assert await client.lrange("a", 0, -1) == [
            "1",
            "1.5",
            "2",
            "2.5",
            "3",
        ]

    async def test_llen(self, client):
        await client.rpush("a", ["1", "2", "3"])
        assert await client.llen("a") == 3

    async def test_lpop(self, client):
        await client.rpush("a", ["1", "2", "3"])
        assert await client.lpop("a") == "1"
        assert await client.lpop("a") == "2"
        assert await client.lpop("a") == "3"
        assert await client.lpop("a") is None

    @pytest.mark.min_server_version("6.2.0")
    async def test_lpop_count(self, client):
        await client.rpush("a", ["1", "2", "3"])
        assert await client.lpop("a", 3) == ["1", "2", "3"]

    async def test_lpush(self, client):
        assert await client.lpush("a", ["1"]) == 1
        assert await client.lpush("a", ["2"]) == 2
        assert await client.lpush("a", ["3", "4"]) == 4
        assert await client.lrange("a", 0, -1) == ["4", "3", "2", "1"]

    async def test_lpushx(self, client):
        assert await client.lpushx("a", ["1"]) == 0
        assert await client.lrange("a", 0, -1) == []
        await client.rpush("a", ["1", "2", "3"])
        assert await client.lpushx("a", ["4"]) == 4
        assert await client.lrange("a", 0, -1) == ["4", "1", "2", "3"]

    async def test_lrange(self, client):
        await client.rpush("a", ["1", "2", "3", "4", "5"])
        assert await client.lrange("a", 0, 2) == ["1", "2", "3"]
        assert await client.lrange("a", 2, 10) == ["3", "4", "5"]
        assert await client.lrange("a", 0, -1) == [
            "1",
            "2",
            "3",
            "4",
            "5",
        ]

    async def test_lrem(self, client):
        await client.rpush("a", ["1", "1", "1", "1"])
        assert await client.lrem("a", 1, "1") == 1
        assert await client.lrange("a", 0, -1) == ["1", "1", "1"]
        assert await client.lrem("a", 3, "1") == 3
        assert await client.lrange("a", 0, -1) == []

    async def test_lset(self, client):
        await client.rpush("a", ["1", "2", "3"])
        assert await client.lrange("a", 0, -1) == ["1", "2", "3"]
        assert await client.lset("a", 1, "4")
        assert await client.lrange("a", 0, 2) == ["1", "4", "3"]

    async def test_ltrim(self, client):
        await client.rpush("a", ["1", "2", "3"])
        assert await client.ltrim("a", 0, 1)
        assert await client.lrange("a", 0, -1) == ["1", "2"]

    async def test_rpop(self, client):
        await client.rpush("a", ["1", "2", "3"])
        assert await client.rpop("a") == "3"
        assert await client.rpop("a") == "2"
        assert await client.rpop("a") == "1"
        assert await client.rpop("a") is None

    @pytest.mark.min_server_version("6.2.0")
    async def test_rpop_count(self, client):
        await client.rpush("a", ["1", "2", "3"])
        assert await client.rpop("a", 3) == ["3", "2", "1"]

    async def test_rpoplpush(self, client):
        await client.rpush("a", ["a1", "a2", "a3"])
        await client.rpush("b", ["b1", "b2", "b3"])
        assert await client.rpoplpush("a", "b") == "a3"
        assert await client.lrange("a", 0, -1) == ["a1", "a2"]
        assert await client.lrange("b", 0, -1) == ["a3", "b1", "b2", "b3"]

    async def test_rpush(self, client):
        assert await client.rpush("a", ["1"]) == 1
        assert await client.rpush("a", ["2"]) == 2
        assert await client.rpush("a", ["3", "4"]) == 4
        assert await client.lrange("a", 0, -1) == ["1", "2", "3", "4"]

    async def test_rpushx(self, client):
        assert await client.rpushx("a", ["b"]) == 0
        assert await client.lrange("a", 0, -1) == []
        await client.rpush("a", ["1", "2", "3"])
        assert await client.rpushx("a", ["4"]) == 4
        assert await client.lrange("a", 0, -1) == ["1", "2", "3", "4"]

    @pytest.mark.min_server_version("6.0.6")
    async def test_lpos(self, client):
        assert await client.rpush("a", ["a", "b", "c", "1", "2", "3", "c", "c"]) == 8
        assert await client.lpos("a", "a") == 0
        assert await client.lpos("a", "c") == 2

        assert await client.lpos("a", "c", rank=1) == 2
        assert await client.lpos("a", "c", rank=2) == 6
        assert await client.lpos("a", "c", rank=4) is None
        assert await client.lpos("a", "c", rank=-1) == 7
        assert await client.lpos("a", "c", rank=-2) == 6

        assert await client.lpos("a", "c", count=0) == [2, 6, 7]
        assert await client.lpos("a", "c", count=1) == [2]
        assert await client.lpos("a", "c", count=2) == [2, 6]
        assert await client.lpos("a", "c", count=100) == [2, 6, 7]

        assert await client.lpos("a", "c", count=0, rank=2) == [6, 7]
        assert await client.lpos("a", "c", count=2, rank=-1) == [7, 6]

        assert await client.lpos("axxx", "c", count=0, rank=2) == []
        assert await client.lpos("axxx", "c") is None

        assert await client.lpos("a", "x", count=2) == []
        assert await client.lpos("a", "x") is None

        assert await client.lpos("a", "a", count=0, maxlen=1) == [0]
        assert await client.lpos("a", "c", count=0, maxlen=1) == []
        assert await client.lpos("a", "c", count=0, maxlen=3) == [2]
        assert await client.lpos("a", "c", count=0, maxlen=3, rank=-1) == [7, 6]
        assert await client.lpos("a", "c", count=0, maxlen=7, rank=2) == [6]

    @pytest.mark.min_server_version("6.2.0")
    async def test_lmove(self, client):
        await client.rpush("a{foo}", ["one", "two", "three", "four"])
        assert await client.lmove("a{foo}", "b{foo}", PureToken.LEFT, PureToken.RIGHT)
        assert await client.lmove("a{foo}", "b{foo}", PureToken.RIGHT, PureToken.LEFT)

    @pytest.mark.min_server_version("6.2.0")
    async def test_blmove(self, client):
        await client.rpush("a{foo}", ["one", "two", "three", "four"])
        assert await client.blmove(
            "a{foo}", "b{foo}", PureToken.LEFT, PureToken.RIGHT, timeout=5
        )
        assert await client.blmove(
            "a{foo}", "b{foo}", PureToken.RIGHT, PureToken.LEFT, timeout=1
        )

    async def test_binary_lists(self, client):
        mapping = {
            "foo bar": ["1", "2", "3"],
            "foo\r\nbar\r\n": ["4", "5", "6"],
            "foo\tbar\x07": ["7", "8", "9"],
        }
        # fill in lists

        for key, value in iteritems(mapping):
            await client.rpush(key, value)

        # check that KEYS returns all the keys as they are
        assert sorted(await client.keys("*")) == sorted(list(iterkeys(mapping)))

        # check that it is possible to get list content by key name

        for key, value in iteritems(mapping):
            assert await client.lrange(key, 0, -1) == value
