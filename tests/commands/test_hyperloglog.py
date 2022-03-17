import pytest

from tests.conftest import targets


@targets("redis_basic", "redis_cluster")
@pytest.mark.asyncio()
class TestHyperLogLog:
    async def test_pfadd(self, client):
        members = {"1", "2", "3"}
        assert await client.pfadd("a", members)
        assert not await client.pfadd("a", members)
        assert await client.pfcount(["a"]) == len(members)

    @pytest.mark.nocluster
    async def test_pfcount(self, client):
        members = {"1", "2", "3"}
        await client.pfadd("a", members)
        assert await client.pfcount(["a"]) == len(members)
        members_b = {"2", "3", "4"}
        await client.pfadd("b", members_b)
        assert await client.pfcount(["b"]) == len(members_b)
        assert await client.pfcount(["a", "b"]) == len(members_b.union(members))

    async def test_pfmerge(self, client):
        mema = {"1", "2", "3"}
        memb = {"2", "3", "4"}
        memc = {"5", "6", "7"}
        await client.pfadd("a{foo}", mema)
        await client.pfadd("b{foo}", memb)
        await client.pfadd("c{foo}", memc)
        await client.pfmerge("d{foo}", ["c{foo}", "a{foo}"])
        assert await client.pfcount(["d{foo}"]) == 6
        await client.pfmerge("d{foo}", ["b{foo}"])
        assert await client.pfcount(["d{foo}"]) == 7
