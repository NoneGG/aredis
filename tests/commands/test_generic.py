import asyncio
import datetime
import time

import pytest

from coredis import PureToken, ResponseError
from tests.conftest import targets


@targets("redis_basic", "redis_cluster")
@pytest.mark.asyncio()
class TestGeneric:
    async def test_sort_basic(self, client):
        await client.rpush("a", ["3", "2", "1", "4"])
        assert await client.sort("a") == ("1", "2", "3", "4")

    async def test_sort_limited(self, client):
        await client.rpush("a", ["3", "2", "1", "4"])
        assert await client.sort("a", offset=1, count=2) == ("2", "3")

    async def test_sort_by(self, client):
        await client.set("score:1", "8")
        await client.set("score:2", "3")
        await client.set("score:3", "5")
        await client.rpush("a", ["3", "2", "1"])
        assert await client.sort("a", by="score:*") == ("2", "3", "1")

    async def test_sort_get(self, client):
        await client.set("user:1", "u1")
        await client.set("user:2", "u2")
        await client.set("user:3", "u3")
        await client.rpush("a", ["2", "3", "1"])
        assert await client.sort("a", ["user:*"]) == ("u1", "u2", "u3")

    async def test_sort_get_multi(self, client):
        await client.set("user:1", "u1")
        await client.set("user:2", "u2")
        await client.set("user:3", "u3")
        await client.rpush("a", ["2", "3", "1"])
        assert await client.sort("a", gets=("user:*", "#")) == (
            "u1",
            "1",
            "u2",
            "2",
            "u3",
            "3",
        )

    async def test_sort_three_gets(self, client):
        await client.set("user:1", "u1")
        await client.set("user:2", "u2")
        await client.set("user:3", "u3")
        await client.set("door:1", "d1")
        await client.set("door:2", "d2")
        await client.set("door:3", "d3")
        await client.rpush("a", ["2", "3", "1"])
        assert await client.sort("a", gets=["user:*", "door:*", "#"]) == (
            "u1",
            "d1",
            "1",
            "u2",
            "d2",
            "2",
            "u3",
            "d3",
            "3",
        )

    async def test_sort_desc(self, client):
        await client.rpush("a", ["2", "3", "1"])
        assert await client.sort("a", order=PureToken.DESC) == ("3", "2", "1")

    async def test_sort_alpha(self, client):
        await client.rpush("a", ["e", "c", "b", "d", "a"])
        assert await client.sort("a", alpha=True) == (
            "a",
            "b",
            "c",
            "d",
            "e",
        )

    async def test_sort_store(self, client):
        await client.rpush("a", ["2", "3", "1"])
        assert await client.sort("a", store="sorted_values") == 3
        assert await client.lrange("sorted_values", 0, -1) == ["1", "2", "3"]

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

        await client.rpush("gods", ["5", "8", "3", "1", "2", "7", "6", "4"])
        num = await client.sort(
            "gods",
            offset=2,
            count=4,
            by="user:*:username",
            gets=["user:*:favorite_drink"],
            order=PureToken.DESC,
            alpha=True,
            store="sorted",
        )
        assert num == 4
        assert await client.lrange("sorted", 0, 10) == [
            "vodka",
            "milk",
            "gin",
            "apple juice",
        ]

    async def test_delete(self, client):
        assert await client.delete("a") == 0
        await client.set("a", "foo")
        assert await client.delete("a") == 1

    async def test_delete_with_multiple_keys(self, client):
        await client.set("a", "foo")
        await client.set("b", "bar")
        assert await client.delete(["a", "b"]) == 2
        assert await client.get("a") is None
        assert await client.get("b") is None

    async def test_dump_and_restore_with_freq(self, client):
        await client.config_set({"maxmemory-policy": "allkeys-lfu"})
        await client.set("a", "foo")
        freq = await client.object_freq("a")
        dumped = await client.dump("a")
        await client.delete("a")
        await client.restore("a", 0, dumped, freq=freq)
        assert await client.get("a") == "foo"
        freq_now = await client.object_freq("a")
        assert freq + 1 == freq_now

    async def test_dump_and_restore_with_idle_time(self, client):
        await client.set("a", "foo")
        await asyncio.sleep(1)
        idle = await client.object_idletime("a")
        dumped = await client.dump("a")
        await client.delete("a")
        await client.restore("a", 0, dumped, idletime=idle)
        new_idle = await client.object_idletime("a")
        assert idle == new_idle

    async def test_dump_and_restore_and_replace(self, client):
        await client.set("a", "bar")
        dumped = await client.dump("a")
        with pytest.raises(ResponseError):
            await client.restore("a", 0, dumped)

        await client.restore("a", 0, dumped, replace=True)
        assert await client.get("a") == "bar"

    @pytest.mark.nocluster
    async def test_migrate_single_key(self, client, redis_auth):
        auth_connection = await redis_auth.connection_pool.get_connection()
        await client.set("a", "1")
        assert not await client.migrate("172.17.0.1", auth_connection.port, 0, 100, "b")
        with pytest.raises(ResponseError):
            assert await client.migrate("172.17.0.1", auth_connection.port, 0, 100, "a")
        assert await client.migrate(
            "172.17.0.1", auth_connection.port, 0, 100, "a", auth="sekret"
        )
        assert await redis_auth.get("a") == "1"

    @pytest.mark.nocluster
    async def test_migrate_multiple_keys(self, client, redis_auth):
        auth_connection = await redis_auth.connection_pool.get_connection()
        await client.set("a", "1")
        await client.set("c", "2")
        assert not await client.migrate(
            "172.17.0.1", auth_connection.port, 0, 100, "d", "b"
        )
        assert await client.migrate(
            "172.17.0.1", auth_connection.port, 0, 100, "a", "c", auth="sekret"
        )

        assert await redis_auth.get("a") == "1"
        assert await redis_auth.get("c") == "2"

    @pytest.mark.min_server_version("6.2.0")
    async def test_copy(self, client):
        await client.set("a{foo}", "foo")
        await client.set("c{foo}", "bar")
        assert await client.copy("x{foo}", "y{foo}") is False
        assert True == (await client.copy("a{foo}", "b{foo}"))
        assert await client.get("b{foo}") == "foo"
        assert False == (await client.copy("a{foo}", "c{foo}", replace=False))
        assert await client.get("c{foo}") == "bar"
        assert True == (await client.copy("a{foo}", "c{foo}", replace=True))
        assert await client.get("c{foo}") == "foo"

    async def test_object(self, client):
        await client.set("a", "foo")
        assert isinstance(await client.object("refcount", "a"), int)
        assert isinstance(await client.object("idletime", "a"), int)
        assert await client.object("encoding", "a") in ("raw", "embstr")
        assert await client.object("idletime", "invalid-key") is None

    @pytest.mark.max_server_version("6.2.0")
    async def test_object_encoding(self, client):
        await client.set("a", "foo")
        await client.hset("b", {"foo": "1"})
        assert await client.object_encoding("a") == "embstr"
        assert await client.object_encoding("b") == "ziplist"

    @pytest.mark.min_server_version("6.9.0")
    async def test_object_encoding_listpack(self, client):
        await client.set("a", "foo")
        await client.hset("b", {"foo": "1"})
        assert await client.object_encoding("a") == "embstr"
        assert await client.object_encoding("b") == "listpack"

    async def test_object_freq(self, client):
        await client.set("a", "foo")
        with pytest.raises(ResponseError):
            await client.object_freq("a"),
        await client.config_set({"maxmemory-policy": "allkeys-lfu"})
        assert isinstance(await client.object_freq("a"), int)

    async def test_object_idletime(self, client):
        await client.set("a", "foo")
        assert isinstance(await client.object_idletime("a"), int)
        await client.config_set({"maxmemory-policy": "allkeys-lfu"})
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
        assert await client.keys() == set()
        keys_with_underscores = {"test_a", "test_b"}
        keys = keys_with_underscores | {"testc"}

        for key in keys:
            await client.set(key, "1")
        assert await client.keys(pattern="test_*") == keys_with_underscores
        assert await client.keys(pattern="test*") == keys

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
            await client.set(key, "1")
        assert await client.randomkey() in ("a", "b", "c")

    async def test_rename(self, client):
        await client.set("a", "1")
        assert await client.rename("a", "b")
        assert await client.get("a") is None
        assert await client.get("b") == "1"

    async def test_renamenx(self, client):
        await client.set("a", "1")
        await client.set("b", "2")
        assert not await client.renamenx("a", "b")
        assert await client.get("a") == "1"
        assert await client.get("b") == "2"

    async def test_type(self, client):
        assert await client.type("a") == "none"
        await client.set("a", "1")
        assert await client.type("a") == "string"
        await client.delete("a")
        await client.lpush("a", "1")
        assert await client.type("a") == "list"
        await client.delete("a")
        await client.sadd("a", "1")
        assert await client.type("a") == "set"
        await client.delete("a")
        await client.zadd("a", {"1": "1"})
        assert await client.type("a") == "zset"

    async def test_touch(self, client):
        keys = ["a{foo}", "b{foo}", "c{foo}", "d{foo}"]

        for index, key in enumerate(keys):
            await client.set(key, str(index))
        assert await client.touch(keys) == len(keys)

    async def test_unlink(self, client):
        keys = ["a{foo}", "b{foo}", "c{foo}", "d{foo}"]

        for index, key in enumerate(keys):
            await client.set(key, str(index))
        await client.unlink(keys)

        for key in keys:
            assert await client.get(key) is None

    @pytest.mark.nocluster
    async def test_scan(self, client):
        await client.set("a", "1")
        await client.set("b", "2")
        await client.set("c", "3")
        cursor, keys = await client.scan()
        assert cursor == 0
        assert set(keys) == set(["a", "b", "c"])
        _, keys = await client.scan(match="a")
        assert set(keys) == set(["a"])

    async def test_scan_iter(self, client):
        await client.set("a", "1")
        await client.set("b", "2")
        await client.set("c", "3")
        keys = set()
        async for key in client.scan_iter():
            keys.add(key)
        assert keys == set(["a", "b", "c"])
        async for key in client.scan_iter(match="a"):
            assert key == "a"
