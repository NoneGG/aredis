import datetime

import pytest

from coredis import CommandSyntaxError, PureToken
from coredis.utils import iteritems
from tests.conftest import targets


@targets("redis_basic", "redis_cluster")
@pytest.mark.asyncio()
class TestString:
    async def test_append(self, client):
        assert await client.append("a", "a1") == 2
        assert await client.get("a") == "a1"
        assert await client.append("a", "a2") == 4
        assert await client.get("a") == "a1a2"

    async def test_decr(self, client):
        assert await client.decr("a") == -1
        assert await client.get("a") == "-1"
        assert await client.decr("a") == -2
        assert await client.get("a") == "-2"

    async def test_decr_by(self, client):
        assert await client.decrby("a", 2) == -2
        assert await client.get("a") == "-2"
        assert await client.decrby("a", 2) == -4
        assert await client.get("a") == "-4"

    async def test_incr(self, client):
        assert await client.incr("a") == 1
        assert await client.get("a") == "1"
        assert await client.incr("a") == 2
        assert await client.get("a") == "2"

    async def test_incrby(self, client):
        assert await client.incrby("a", 1) == 1
        assert await client.incrby("a", 4) == 5
        assert await client.get("a") == "5"

    async def test_incrbyfloat(self, client):
        assert await client.incrbyfloat("a", 1.0) == 1.0
        assert await client.get("a") == "1"
        assert await client.incrbyfloat("a", 1.1) == 2.1
        assert float(await client.get("a")) == float(2.1)

    async def test_getrange(self, client):
        await client.set("a", "foo")
        assert await client.getrange("a", 0, 0) == "f"
        assert await client.getrange("a", 0, 2) == "foo"
        assert await client.getrange("a", 3, 4) == ""

    async def test_getset(self, client):
        assert await client.getset("a", "foo") is None
        assert await client.getset("a", "bar") == "foo"
        assert await client.get("a") == "bar"

    async def test_get_and_set(self, client):
        # get and set can't be tested independently of each other
        assert await client.get("a") is None
        byte_string = "value"
        integer = 5
        unicode_string = chr(33) + "abcd" + chr(22)
        assert await client.set("byte_string", byte_string)
        assert await client.set("integer", "5")
        assert await client.set("unicode_string", unicode_string)
        assert await client.get("byte_string") == byte_string
        assert await client.get("integer") == str(integer)
        assert await client.get("unicode_string") == unicode_string

    @pytest.mark.min_server_version("6.2.0")
    async def test_getdel(self, client):
        assert await client.getdel("a") is None
        await client.set("a", "1")
        assert await client.getdel("a") == "1"
        assert await client.getdel("a") is None

    @pytest.mark.min_server_version("6.2.0")
    async def test_getex(self, client, redis_server_time):
        await client.set("a", "1")
        assert await client.getex("a") == "1"
        assert await client.ttl("a") == -1
        assert await client.getex("a", ex=60) == "1"
        assert await client.ttl("a") == 60
        assert await client.getex("a", px=6000) == "1"
        assert await client.ttl("a") == 6
        expire_at = await redis_server_time(client) + datetime.timedelta(minutes=1)
        assert await client.getex("a", pxat=expire_at) == "1"
        assert await client.ttl("a") <= 61
        assert await client.getex("a", persist=True) == "1"
        assert await client.ttl("a") == -1
        with pytest.raises(CommandSyntaxError):
            await client.getex("a", ex=1, px=1)

    async def test_mget(self, client):
        assert await client.mget(["a", "b"]) == (None, None)
        await client.set("a", "1")
        await client.set("b", "2")
        await client.set("c", "3")
        assert await client.mget(["a", "other", "b", "c"]) == (
            "1",
            None,
            "2",
            "3",
        )

    async def test_mset(self, client):
        d = {"a": "1", "b": "2", "c": "3"}
        assert await client.mset(d)

        assert await client.get("a") == "1"
        assert await client.get("b") == "2"
        assert await client.get("c") == "3"

    async def test_msetnx(self, client):
        d = {"a": "1", "b": "2", "c": "3"}
        assert await client.msetnx(d)
        d2 = {"a": "x", "d": "4"}
        assert not await client.msetnx(d2)

        for k, v in iteritems(d):
            assert await client.get(k) == v
        assert await client.get("d") is None

    async def test_psetex(self, client):
        assert await client.psetex("a", 1000, "value")
        assert await client.get("a") == "value"
        assert 0 < await client.pttl("a") <= 1000

    async def test_psetex_timedelta(self, client):
        expire_at = datetime.timedelta(milliseconds=1000)
        assert await client.psetex("a", expire_at, "value")
        assert await client.get("a") == "value"
        assert 0 < await client.pttl("a") <= 1000

    async def test_set_nx(self, client):
        assert await client.set("a", "1", condition=PureToken.NX)
        assert not await client.set("a", "2", condition=PureToken.NX)
        assert await client.get("a") == "1"

    async def test_set_xx(self, client):
        assert not await client.set("a", "1", condition=PureToken.XX)
        assert await client.get("a") is None
        await client.set("a", "bar")
        assert await client.set("a", "2", condition=PureToken.XX)
        assert await client.get("a") == "2"

    async def test_set_px(self, client):
        assert await client.set("a", "1", px=10000)
        assert await client.get("a") == "1"
        assert 0 < await client.pttl("a") <= 10000
        assert 0 < await client.ttl("a") <= 10

    async def test_set_px_timedelta(self, client):
        expire_at = datetime.timedelta(milliseconds=1000)
        assert await client.set("a", "1", px=expire_at)
        assert 0 < await client.pttl("a") <= 1000
        assert 0 < await client.ttl("a") <= 1

    async def test_set_ex(self, client):
        assert await client.set("a", "1", ex=10)
        assert 0 < await client.ttl("a") <= 10

    async def test_set_ex_timedelta(self, client):
        expire_at = datetime.timedelta(seconds=60)
        assert await client.set("a", "1", ex=expire_at)
        assert 0 < await client.ttl("a") <= 60

    async def test_set_multipleoptions(self, client):
        await client.set("a", "val")
        assert await client.set("a", "1", condition=PureToken.XX, px=10000)
        assert 0 < await client.ttl("a") <= 10

    async def test_setex(self, client):
        assert await client.setex("a", "1", 60)
        assert await client.get("a") == "1"
        assert 0 < await client.ttl("a") <= 60

    async def test_setnx(self, client):
        assert await client.setnx("a", "1")
        assert await client.get("a") == "1"
        assert not await client.setnx("a", "2")
        assert await client.get("a") == "1"

    async def test_setrange(self, client):
        assert await client.setrange("a", 5, "foo") == 8
        assert await client.get("a") == "\0\0\0\0\0foo"
        await client.set("a", "abcdefghijh")
        assert await client.setrange("a", 6, "12345") == 11
        assert await client.get("a") == "abcdef12345"

    async def test_strlen(self, client):
        await client.set("a", "foo")
        assert await client.strlen("a") == 3

    async def test_substr(self, client):
        await client.set("a", "0123456789")
        assert await client.substr("a", 0, -1) == "0123456789"
        assert await client.substr("a", 2, -1) == "23456789"
        assert await client.substr("a", 3, 5) == "345"
        assert await client.substr("a", 3, -2) == "345678"

    async def test_binary_get_set(self, client):
        assert await client.set(" foo bar ", "123")
        assert await client.get(" foo bar ") == "123"

        assert await client.set(" foo\r\nbar\r\n ", "456")
        assert await client.get(" foo\r\nbar\r\n ") == "456"

        assert await client.set(" \r\n\t\x07\x13 ", "789")
        assert await client.get(" \r\n\t\x07\x13 ") == "789"

        assert sorted(await client.keys("*")) == [
            " \r\n\t\x07\x13 ",
            " foo\r\nbar\r\n ",
            " foo bar ",
        ]

        assert await client.delete([" foo bar "])
        assert await client.delete([" foo\r\nbar\r\n "])
        assert await client.delete([" \r\n\t\x07\x13 "])
