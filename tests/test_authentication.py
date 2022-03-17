import pytest

import coredis
from coredis.exceptions import AuthenticationError


@pytest.mark.min_server_version("6.0.0")
@pytest.mark.parametrize(
    "username, password",
    (
        ["", ""],
        ["fubar", ""],
        ["", "fubar"],
        ["fubar", "fubar"],
    ),
)
@pytest.mark.asyncio
async def test_invalid_authentication(redis_auth, username, password):
    client = coredis.Redis("localhost", 6389, username=username, password=password)
    with pytest.raises(AuthenticationError):
        await client.ping()


@pytest.mark.min_server_version("6.0.0")
@pytest.mark.asyncio
async def test_valid_authentication(redis_auth):
    client = coredis.Redis("localhost", 6389, password="sekret")
    assert await client.ping()


@pytest.mark.min_server_version("6.0.0")
@pytest.mark.asyncio
async def test_valid_authentication_delayed(redis_auth):
    client = coredis.Redis("localhost", 6389)
    await client.auth(password="sekret")
    assert await client.ping()
