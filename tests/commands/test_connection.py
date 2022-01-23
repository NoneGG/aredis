import pytest

import coredis
from tests.conftest import targets


@targets("redis_basic")
@pytest.mark.asyncio()
class TestConnection:
    async def test_ping(self, client):
        assert await client.ping()

    async def test_echo(self, client):
        assert await client.echo("foo bar") == b"foo bar"

    async def test_client_list(self, client):
        clients = await client.client_list()
        assert isinstance(clients[0], dict)
        assert "addr" in clients[0]

    async def test_client_list_after_client_setname(self, client):
        await client.client_setname("cl=i=ent")
        clients = await client.client_list()
        assert "cl=i=ent" in [c["name"] for c in clients]

    async def test_client_getname(self, client):
        assert await client.client_getname() is None

    async def test_client_setname(self, client):
        assert await client.client_setname("redis_py_test")
        assert await client.client_getname() == "redis_py_test"

    async def test_client_pause(self, client, event_loop):
        key = "key_should_expire"
        another_client = coredis.StrictRedis(loop=event_loop)
        await client.set(key, 1, px=100)
        assert await client.client_pause(100)
        res = await another_client.get(key)
        assert not res
