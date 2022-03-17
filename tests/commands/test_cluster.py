import pytest

from tests.conftest import targets


@targets("redis_cluster")
@pytest.mark.asyncio()
class TestCluster:
    async def test_cluster_info(self, client):
        info = await client.cluster_info()
        assert info["cluster_state"] == "ok"

        info = await list(client.replicas)[0].cluster_info()
        assert info["cluster_state"] == "ok"

        info = await list(client.primaries)[0].cluster_info()
        assert info["cluster_state"] == "ok"

    async def test_cluster_keyslot(self, client):
        slot = await client.cluster_keyslot("a")
        assert slot is not None
        await client.set("a", "1")
        assert await client.cluster_countkeysinslot(slot) == 1
        assert await client.cluster_getkeysinslot(slot, 1) == ("a",)

    async def test_cluster_nodes(self, client):
        nodes = await client.cluster_nodes()
        assert len(nodes) == 6
        replicas = await client.cluster_replicas(
            [n["id"] for n in nodes if "master" in n["flags"]].pop()
        )
        assert len(replicas) == 1
