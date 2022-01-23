import datetime
import time

import pytest

from coredis import DataError, ResponseError
from coredis.utils import b
from tests.conftest import targets


@targets("redis_basic", "redis_cluster")
@pytest.mark.asyncio()
class TestGeneric:
    async def test_sort_basic(self, client):
        await client.rpush("a", "3", "2", "1", "4")
        assert await client.sort("a") == [b("1"), b("2"), b("3"), b("4")]

    async def test_sort_limited(self, client):
        await client.rpush("a", "3", "2", "1", "4")
        assert await client.sort("a", start=1, num=2) == [b("2"), b("3")]

    async def test_sort_by(self, client):
        await client.set("score:1", 8)
        await client.set("score:2", 3)
        await client.set("score:3", 5)
        await client.rpush("a", "3", "2", "1")
        assert await client.sort("a", by="score:*") == [b("2"), b("3"), b("1")]

    async def test_sort_get(self, client):
        await client.set("user:1", "u1")
        await client.set("user:2", "u2")
        await client.set("user:3", "u3")
        await client.rpush("a", "2", "3", "1")
        assert await client.sort("a", get="user:*") == [b("u1"), b("u2"), b("u3")]

    async def test_sort_get_multi(self, client):
        await client.set("user:1", "u1")
        await client.set("user:2", "u2")
        await client.set("user:3", "u3")
        await client.rpush("a", "2", "3", "1")
        assert await client.sort("a", get=("user:*", "#")) == [
            b("u1"),
            b("1"),
            b("u2"),
            b("2"),
            b("u3"),
            b("3"),
        ]

    async def test_sort_get_groups_two(self, client):
        await client.set("user:1", "u1")
        await client.set("user:2", "u2")
        await client.set("user:3", "u3")
        await client.rpush("a", "2", "3", "1")
        assert await client.sort("a", get=("user:*", "#"), groups=True) == [
            (b("u1"), b("1")),
            (b("u2"), b("2")),
            (b("u3"), b("3")),
        ]

    async def test_sort_groups_string_get(self, client):
        await client.set("user:1", "u1")
        await client.set("user:2", "u2")
        await client.set("user:3", "u3")
        await client.rpush("a", "2", "3", "1")
        with pytest.raises(DataError):
            await client.sort("a", get="user:*", groups=True)

    async def test_sort_groups_just_one_get(self, client):
        await client.set("user:1", "u1")
        await client.set("user:2", "u2")
        await client.set("user:3", "u3")
        await client.rpush("a", "2", "3", "1")
        with pytest.raises(DataError):
            await client.sort("a", get=["user:*"], groups=True)

    async def test_sort_groups_no_get(self, client):
        await client.set("user:1", "u1")
        await client.set("user:2", "u2")
        await client.set("user:3", "u3")
        await client.rpush("a", "2", "3", "1")
        with pytest.raises(DataError):
            await client.sort("a", groups=True)

    async def test_sort_groups_three_gets(self, client):
        await client.set("user:1", "u1")
        await client.set("user:2", "u2")
        await client.set("user:3", "u3")
        await client.set("door:1", "d1")
        await client.set("door:2", "d2")
        await client.set("door:3", "d3")
        await client.rpush("a", "2", "3", "1")
        assert await client.sort("a", get=("user:*", "door:*", "#"), groups=True) == [
            (b("u1"), b("d1"), b("1")),
            (b("u2"), b("d2"), b("2")),
            (b("u3"), b("d3"), b("3")),
        ]

    async def test_sort_desc(self, client):
        await client.rpush("a", "2", "3", "1")
        assert await client.sort("a", desc=True) == [b("3"), b("2"), b("1")]

    async def test_sort_alpha(self, client):
        await client.rpush("a", "e", "c", "b", "d", "a")
        assert await client.sort("a", alpha=True) == [
            b("a"),
            b("b"),
            b("c"),
            b("d"),
            b("e"),
        ]

    async def test_sort_store(self, client):
        await client.rpush("a", "2", "3", "1")
        assert await client.sort("a", store="sorted_values") == 3
        assert await client.lrange("sorted_values", 0, -1) == [b("1"), b("2"), b("3")]

    async def test_sort_all_options(self, client):
        await client.set("user:1:username", "zeus")
        await client.set("user:2:username", "titan")
        await client.set("user:3:username", "hermes")
        await client.set("user:4:username", "hercules")
        await client.set("user:5:username", "apollo")
        await client.set("user:6:username", "athena")
        await client.set("user:7:username", "hades")
        await client.set("user:8:username", "dionysus")

        await client.set("user:1:favorite_drink", "yuengling")
        await client.set("user:2:favorite_drink", "rum")
        await client.set("user:3:favorite_drink", "vodka")
        await client.set("user:4:favorite_drink", "milk")
        await client.set("user:5:favorite_drink", "pinot noir")
        await client.set("user:6:favorite_drink", "water")
        await client.set("user:7:favorite_drink", "gin")
        await client.set("user:8:favorite_drink", "apple juice")

        await client.rpush("gods", "5", "8", "3", "1", "2", "7", "6", "4")
        num = await client.sort(
            "gods",
            start=2,
            num=4,
            by="user:*:username",
            get="user:*:favorite_drink",
            desc=True,
            alpha=True,
            store="sorted",
        )
        assert num == 4
        assert await client.lrange("sorted", 0, 10) == [
            b("vodka"),
            b("milk"),
            b("gin"),
            b("apple juice"),
        ]

    async def test_delete(self, client):
        assert await client.delete("a") == 0
        await client.set("a", "foo")
        assert await client.delete("a") == 1

    async def test_delete_with_multiple_keys(self, client):
        await client.set("a", "foo")
        await client.set("b", "bar")
        assert await client.delete("a", "b") == 2
        assert await client.get("a") is None
        assert await client.get("b") is None

    async def test_dump_and_restore(self, client):
        await client.set("a", "foo")
        dumped = await client.dump("a")
        await client.delete("a")
        await client.restore("a", 0, dumped)
        assert await client.get("a") == b("foo")

    async def test_dump_and_restore_and_replace(self, client):
        await client.set("a", "bar")
        dumped = await client.dump("a")
        with pytest.raises(ResponseError):
            await client.restore("a", 0, dumped)

        await client.restore("a", 0, dumped, replace=True)
        assert await client.get("a") == b("bar")

    @pytest.mark.nocluster
    async def test_object(self, client):
        await client.set("a", "foo")
        assert isinstance(await client.object("refcount", "a"), int)
        assert isinstance(await client.object("idletime", "a"), int)
        assert await client.object("encoding", "a") in (b("raw"), b("embstr"))
        assert await client.object("idletime", "invalid-key") is None

    async def test_object_encoding(self, client):
        await client.set("a", "foo")
        await client.hset("b", "foo", 1)
        assert await client.object_encoding("a") == b"embstr"
        assert await client.object_encoding("b") == b"ziplist"

    async def test_object_freq(self, client):
        await client.set("a", "foo")
        with pytest.raises(ResponseError):
            await client.object_freq("a"),
        await client.config_set("maxmemory-policy", "allkeys-lfu")
        assert isinstance(await client.object_freq("a"), int)

    async def test_object_idletime(self, client):
        await client.set("a", "foo")
        assert isinstance(await client.object_idletime("a"), int)
        await client.config_set("maxmemory-policy", "allkeys-lfu")
        with pytest.raises(ResponseError):
            await client.object_idletime("a"),

    async def test_object_refcount(self, client):
        await client.set("a", "foo")
        assert await client.object_refcount("a") == 1

    async def test_exists(self, client):
        assert not await client.exists("a")
        await client.set("a", "foo")
        assert await client.exists("a")

    async def test_expire(self, client):
        assert not await client.expire("a", 10)
        await client.set("a", "foo")
        assert await client.expire("a", 10)
        assert 0 < await client.ttl("a") <= 10
        assert await client.persist("a")
        assert await client.ttl("a") == -1

    async def test_expireat_datetime(self, client, redis_server_time):
        expire_at = await redis_server_time(client) + datetime.timedelta(minutes=1)
        await client.set("a", "foo")
        assert await client.expireat("a", expire_at)
        assert 0 < await client.ttl("a") <= 61

    async def test_expireat_no_key(self, client, redis_server_time):
        expire_at = await redis_server_time(client) + datetime.timedelta(minutes=1)
        assert not await client.expireat("a", expire_at)

    async def test_expireat_unixtime(self, client, redis_server_time):
        expire_at = await redis_server_time(client) + datetime.timedelta(minutes=1)
        await client.set("a", "foo")
        expire_at_seconds = int(time.mktime(expire_at.timetuple()))
        assert await client.expireat("a", expire_at_seconds)
        assert 0 < await client.ttl("a") <= 61

    async def test_keys(self, client):
        assert await client.keys() == []
        keys_with_underscores = {b("test_a"), b("test_b")}
        keys = keys_with_underscores.union({b("testc")})

        for key in keys:
            await client.set(key, 1)
        assert set(await client.keys(pattern="test_*")) == keys_with_underscores
        assert set(await client.keys(pattern="test*")) == keys

    async def test_pexpire(self, client):
        assert not await client.pexpire("a", 60000)
        await client.set("a", "foo")
        assert await client.pexpire("a", 60000)
        assert 0 < await client.pttl("a") <= 60000
        assert await client.persist("a")
        assert await client.pttl("a") < 0

    async def test_pexpireat_datetime(self, client, redis_server_time):
        expire_at = await redis_server_time(client) + datetime.timedelta(minutes=1)
        await client.set("a", "foo")
        assert await client.pexpireat("a", expire_at)
        assert 0 < await client.pttl("a") <= 61000

    async def test_pexpireat_no_key(self, client, redis_server_time):
        expire_at = await redis_server_time(client) + datetime.timedelta(minutes=1)
        assert not await client.pexpireat("a", expire_at)

    async def test_pexpireat_unixtime(self, client, redis_server_time):
        expire_at = await redis_server_time(client) + datetime.timedelta(minutes=1)
        await client.set("a", "foo")
        expire_at_seconds = int(time.mktime(expire_at.timetuple())) * 1000
        assert await client.pexpireat("a", expire_at_seconds)
        assert 0 < await client.pttl("a") <= 61000

    async def test_randomkey(self, client):
        assert await client.randomkey() is None

        for key in ("a", "b", "c"):
            await client.set(key, 1)
        assert await client.randomkey() in (b("a"), b("b"), b("c"))

    async def test_rename(self, client):
        await client.set("a", 1)
        assert await client.rename("a", "b")
        assert await client.get("a") is None
        assert await client.get("b") == b("1")

    async def test_renamenx(self, client):
        await client.set("a", 1)
        await client.set("b", 2)
        assert not await client.renamenx("a", "b")
        assert await client.get("a") == b("1")
        assert await client.get("b") == b("2")

    async def test_type(self, client):
        assert await client.type("a") == b("none")
        await client.set("a", "1")
        assert await client.type("a") == b("string")
        await client.delete("a")
        await client.lpush("a", "1")
        assert await client.type("a") == b("list")
        await client.delete("a")
        await client.sadd("a", "1")
        assert await client.type("a") == b("set")
        await client.delete("a")
        await client.zadd("a", **{"1": 1})
        assert await client.type("a") == b("zset")

    async def test_touch(self, client):
        keys = ["a{foo}", "b{foo}", "c{foo}", "d{foo}"]

        for index, key in enumerate(keys):
            await client.set(key, index)
        assert await client.touch(keys) == len(keys)

    async def test_unlink(self, client):
        keys = ["a{foo}", "b{foo}", "c{foo}", "d{foo}"]

        for index, key in enumerate(keys):
            await client.set(key, index)
        await client.unlink(*keys)

        for key in keys:
            assert await client.get(key) is None

    @pytest.mark.nocluster
    async def test_scan(self, client):
        await client.set("a", 1)
        await client.set("b", 2)
        await client.set("c", 3)
        cursor, keys = await client.scan()
        assert cursor == 0
        assert set(keys) == set([b("a"), b("b"), b("c")])
        _, keys = await client.scan(match="a")
        assert set(keys) == set([b("a")])

    async def test_scan_iter(self, client):
        await client.set("a", 1)
        await client.set("b", 2)
        await client.set("c", 3)
        keys = set()
        async for key in client.scan_iter():
            keys.add(key)
        assert keys == set([b("a"), b("b"), b("c")])
        async for key in client.scan_iter(match="a"):
            assert key == b("a")
