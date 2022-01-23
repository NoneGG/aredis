import pytest

import coredis
from coredis.exceptions import AuthenticationError


@pytest.mark.parametrize(
    "username, password",
    (
        ["", ""],
        ["fubar", ""],
        ["", "fubar"],
        ["fubar", "fubar"],
    ),
)
async def test_invalid_authentication(redis_auth_server, username, password):
    client = coredis.StrictRedis(
        redis_auth_server[0], redis_auth_server[1], username=username, password=password
    )
    with pytest.raises(AuthenticationError):
        await client.ping()


async def test_valid_authentication(redis_auth_server):
    client = coredis.StrictRedis(
        redis_auth_server[0], redis_auth_server[1], password="sekret"
    )
    assert await client.ping()
