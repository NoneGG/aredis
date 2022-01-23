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
async def test_invalid_authentication(redis_auth, username, password):
    client = coredis.StrictRedis(
        "localhost", 6389, username=username, password=password
    )
    with pytest.raises(AuthenticationError):
        await client.ping()


@pytest.mark.min_server_version("6.0.0")
async def test_valid_authentication(redis_auth):
    client = coredis.StrictRedis("localhost", 6389, password="sekret")
    assert await client.ping()
