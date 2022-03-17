import pytest

from tests.conftest import targets


@targets("redis_basic", "redis_cluster")
@pytest.mark.asyncio()
class TestSet:
    async def test_sadd(self, client):
        members = set(["1", "2", "3"])
        await client.sadd("a", members)
        assert await client.smembers("a") == members

    async def test_scard(self, client):
        await client.sadd("a", ["1", "2", "3"])
        assert await client.scard("a") == 3

    async def test_sdiff(self, client):
        await client.sadd("a", ["1", "2", "3"])
        assert await client.sdiff(["a", "b"]) == set(["1", "2", "3"])
        await client.sadd("b", ["2", "3"])
        assert await client.sdiff(["a", "b"]) == set(["1"])

    async def test_sdiffstore(self, client):
        await client.sadd("a", ["1", "2", "3"])
        assert await client.sdiffstore(["a", "b"], destination="c") == 3
        assert await client.smembers("c") == set(["1", "2", "3"])
        await client.sadd("b", ["2", "3"])
        assert await client.sdiffstore(["a", "b"], destination="c") == 1
        assert await client.smembers("c") == set(["1"])

    async def test_sinter(self, client):
        await client.sadd("a", ["1", "2", "3"])
        assert await client.sinter(["a", "b"]) == set()
        await client.sadd("b", ["2", "3"])
        assert await client.sinter(["a", "b"]) == set(["2", "3"])

    async def test_sinterstore(self, client):
        await client.sadd("a", ["1", "2", "3"])
        assert await client.sinterstore(["a", "b"], destination="c") == 0
        assert await client.smembers("c") == set()
        await client.sadd("b", ["2", "3"])
        assert await client.sinterstore(["a", "b"], destination="c") == 2
        assert await client.smembers("c") == set(["2", "3"])

    async def test_sismember(self, client):
        await client.sadd("a", ["1", "2", "3"])
        assert await client.sismember("a", "1")
        assert await client.sismember("a", "2")
        assert await client.sismember("a", "3")
        assert not await client.sismember("a", "4")

    async def test_smembers(self, client):
        await client.sadd("a", ["1", "2", "3"])
        assert await client.smembers("a") == set(["1", "2", "3"])

    @pytest.mark.min_server_version("6.2.0")
    async def test_smismember(self, client):
        await client.sadd("a", ["1", "2", "3"])
        result_list = (True, False, True, True)
        assert (await client.smismember("a", ["1", "4", "2", "3"])) == result_list

    async def test_smove(self, client):
        await client.sadd("a", ["a1", "a2"])
        await client.sadd("b", ["b1", "b2"])
        assert await client.smove("a", "b", "a1")
        assert await client.smembers("a") == set(["a2"])
        assert await client.smembers("b") == set(["b1", "b2", "a1"])

    async def test_spop(self, client):
        s = ["1", "2", "3"]
        await client.sadd("a", s)
        value = await client.spop("a")
        assert set(await client.smembers("a")) == set(s) - {value}

    async def test_spop_multi_value(self, client):
        s = ["1", "2", "3"]
        await client.sadd("a", s)
        values = await client.spop("a", 2)
        assert await client.smembers("a") == set(s) - values

    async def test_srandmember(self, client):
        s = ["1", "2", "3"]
        await client.sadd("a", s)
        assert (await client.srandmember("a"))[0] in s

    async def test_srandmember_multi_value(self, client):
        s = ["1", "2", "3"]
        await client.sadd("a", s)
        randoms = await client.srandmember("a", count=2)
        assert len(randoms) == 2
        assert set(randoms).intersection(s) == set(randoms)

    async def test_srem(self, client):
        await client.sadd("a", ["1", "2", "3", "4"])
        assert await client.srem("a", ["5"]) == 0
        assert await client.srem("a", ["2", "4"]) == 2
        assert await client.smembers("a") == set(["1", "3"])

    async def test_sunion(self, client):
        await client.sadd("a", ["1", "2"])
        await client.sadd("b", ["2", "3"])
        assert await client.sunion(["a", "b"]) == set(["1", "2", "3"])

    async def test_sunionstore(self, client):
        await client.sadd("a", ["1", "2"])
        await client.sadd("b", ["2", "3"])
        assert await client.sunionstore(["a", "b"], destination="c") == 3
        assert await client.smembers("c") == set(["1", "2", "3"])

    async def test_sscan(self, client):
        await client.sadd("a", ["1", "2", "3"])
        cursor, members = await client.sscan("a")
        assert cursor == 0
        assert set(members) == set(["1", "2", "3"])
        _, members = await client.sscan("a", match="1")
        assert set(members) == set(["1"])

    async def test_sscan_iter(self, client):
        await client.sadd("a", ["1", "2", "3"])
        members = set()
        async for member in client.sscan_iter("a"):
            members.add(member)
        assert members == set(["1", "2", "3"])
        async for member in client.sscan_iter("a", match="1"):
            assert member == "1"
