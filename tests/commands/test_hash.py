import pytest

from coredis.utils import iterkeys, itervalues
from tests.conftest import targets


@targets("redis_basic", "redis_cluster")
@pytest.mark.asyncio()
class TestHash:
    async def test_hget_and_hset(self, client):
        await client.hmset("a", {"1": 1, "2": 2, "3": 3})
        assert await client.hget("a", "1") == "1"
        assert await client.hget("a", "2") == "2"
        assert await client.hget("a", "3") == "3"

        # field was updated, redis returns 0
        assert await client.hset("a", {"2": 5}) == 0
        assert await client.hget("a", "2") == "5"

        # field is new, redis returns 1
        assert await client.hset("a", {"4": 4}) == 1
        assert await client.hget("a", "4") == "4"

        # key inside of hash that doesn't exist returns null value
        assert await client.hget("a", "b") is None

    async def test_hdel(self, client):
        await client.hmset("a", {"1": 1, "2": 2, "3": 3})
        assert await client.hdel("a", ["2"]) == 1
        assert await client.hget("a", "2") is None
        assert await client.hdel("a", ["1", "3"]) == 2
        assert await client.hlen("a") == 0

    async def test_hexists(self, client):
        await client.hmset("a", {"1": 1, "2": 2, "3": 3})
        assert await client.hexists("a", "1")
        assert not await client.hexists("a", "4")

    async def test_hgetall(self, client):
        h = {"a1": "1", "a2": "2", "a3": "3"}
        await client.hmset("a", h)
        assert await client.hgetall("a") == h

    async def test_hincrby(self, client):
        assert await client.hincrby("a", "1", increment=1) == 1
        assert await client.hincrby("a", "1", increment=2) == 3
        assert await client.hincrby("a", "1", increment=-2) == 1

    async def test_hincrbyfloat(self, client):
        assert await client.hincrbyfloat("a", "1", increment=1.0) == 1.0
        assert await client.hincrbyfloat("a", "1", increment=1.0) == 2.0
        assert await client.hincrbyfloat("a", "1", 1.2) == 3.2

    async def test_hkeys(self, client):
        h = {"a1": "1", "a2": "2", "a3": "3"}
        await client.hmset("a", h)
        local_keys = list(iterkeys(h))
        remote_keys = await client.hkeys("a")
        assert sorted(local_keys) == sorted(remote_keys)

    async def test_hlen(self, client):
        await client.hmset("a", {"1": 1, "2": 2, "3": 3})
        assert await client.hlen("a") == 3

    async def test_hmget(self, client):
        assert await client.hmset("a", {"a": 1, "b": 2, "c": 3})
        assert await client.hmget("a", ["a", "b", "c"]) == ("1", "2", "3")

    async def test_hmset(self, client):
        h = {"a": "1", "b": "2", "c": "3"}
        assert await client.hmset("a", h)
        assert await client.hgetall("a") == h

    async def test_hsetnx(self, client):
        # Initially set the hash field
        assert await client.hsetnx("a", "1", "1")
        assert await client.hget("a", "1") == "1"
        assert not await client.hsetnx("a", "1", "2")
        assert await client.hget("a", "1") == "1"

    async def test_hvals(self, client):
        h = {"a1": "1", "a2": "2", "a3": "3"}
        await client.hmset("a", h)
        local_vals = list(itervalues(h))
        remote_vals = await client.hvals("a")
        assert sorted(local_vals) == sorted(remote_vals)

    async def test_hstrlen(self, client):
        key = "myhash"
        myhash = {"f1": "HelloWorld", "f2": 99, "f3": -256}
        await client.hmset(key, myhash)
        assert await client.hstrlen("key_not_exist", "f1") == 0
        assert await client.hstrlen(key, "f4") == 0
        assert await client.hstrlen(key, "f1") == 10
        assert await client.hstrlen(key, "f2") == 2
        assert await client.hstrlen(key, "f3") == 4

    @pytest.mark.min_server_version("6.2.0")
    async def test_hrandfield(self, client):
        assert await client.hrandfield("key") is None
        await client.hmset("key", {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})
        assert await client.hrandfield("key") is not None
        assert len(await client.hrandfield("key", 2)) == 2
        # with values
        assert len(await client.hrandfield("key", 2, True)) == 2
        # without duplications
        assert len(await client.hrandfield("key", 10)) == 5
        # with duplications
        assert len(await client.hrandfield("key", -10)) == 10
        assert await client.hrandfield("key-not-exist") is None

    async def test_hscan(self, client):
        await client.hmset("a", {"a": 1, "b": 2, "c": 3})
        cursor, dic = await client.hscan("a")
        assert cursor == 0
        assert dic == {"a": "1", "b": "2", "c": "3"}
        _, dic = await client.hscan("a", match="a")
        assert dic == {"a": "1"}

    async def test_hscan_iter(self, client):
        await client.hmset("a", {"a": 1, "b": 2, "c": 3})
        dic = dict()
        async for data in client.hscan_iter("a"):
            dic.update(dict([data]))
        assert dic == {"a": "1", "b": "2", "c": "3"}
        async for data in client.hscan_iter("a", match="a"):
            assert dict([data]) == {"a": "1"}
