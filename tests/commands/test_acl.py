import pytest

from coredis import AuthenticationError
from tests.conftest import targets


@targets("redis_basic", "redis_auth", "redis_cluster")
@pytest.mark.min_server_version("6.0.0")
@pytest.mark.asyncio()
class TestACL:
    async def test_acl_cat(self, client):
        assert {"keyspace"} & set(await client.acl_cat())
        assert {"keys"} & set(await client.acl_cat("keyspace"))

    async def test_acl_list(self, client):
        assert "user default" in (await client.acl_list())[0]

    async def test_del_user(self, client):
        assert 0 == await client.acl_deluser(["john", "doe"])

    async def test_gen_pass(self, client):
        assert len(await client.acl_genpass()) == 64
        assert len(await client.acl_genpass(4)) == 1

    @pytest.mark.min_server_version("6.0.0")
    @pytest.mark.nocluster
    async def test_acl_log(self, client):
        with pytest.raises(AuthenticationError):
            await client.auth("wrong", "wrong")
        log = await client.acl_log()
        assert len(log) == 1
        await client.acl_log(reset=True)
        assert len(await client.acl_log()) == 0

    async def test_setuser(self, client):
        assert await client.acl_setuser("default")

    async def test_users(self, client):
        assert await client.acl_users() == ("default",)

    async def test_whoami(self, client):
        assert await client.acl_whoami() == "default"

    async def test_new_user(self, client):
        try:
            assert await client.acl_setuser("test_user", "on")
            new_user = await client.acl_getuser("test_user")
            assert "on" in new_user["flags"]
        finally:
            await client.acl_deluser(["test_user"])

    async def test_get_user(self, client):
        default_user = await client.acl_getuser("default")
        assert "on" in default_user["flags"]
