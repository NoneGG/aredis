import pytest

from coredis.utils import b
from tests.conftest import targets


@targets("redis_basic", "redis_cluster")
@pytest.mark.asyncio()
class TestHyperLogLog:
    async def test_pfadd(self, client):
        members = set([b("1"), b("2"), b("3")])
        assert await client.pfadd("a", *members) == 1
        assert await client.pfadd("a", *members) == 0
        assert await client.pfcount("a") == len(members)

    @pytest.mark.nocluster
    async def test_pfcount(self, client):
        members = set([b("1"), b("2"), b("3")])
        await client.pfadd("a", *members)
        assert await client.pfcount("a") == len(members)
        members_b = set([b("2"), b("3"), b("4")])
        await client.pfadd("b", *members_b)
        assert await client.pfcount("b") == len(members_b)
        assert await client.pfcount("a", "b") == len(members_b.union(members))

    async def test_pfmerge(self, client):
        mema = set([b("1"), b("2"), b("3")])
        memb = set([b("2"), b("3"), b("4")])
        memc = set([b("5"), b("6"), b("7")])
        await client.pfadd("a", *mema)
        await client.pfadd("b", *memb)
        await client.pfadd("c", *memc)
        await client.pfmerge("d", "c", "a")
        assert await client.pfcount("d") == 6
        await client.pfmerge("d", "b")
        assert await client.pfcount("d") == 7
