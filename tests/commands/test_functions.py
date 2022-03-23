import pytest

from coredis import PureToken
from tests.conftest import targets

library_definition = """
local function fu(keys, args)
    return keys[1]
end
local function bar(keys, args)
    return 1.0*args[1]
end
redis.register_function('fu', fu)
redis.register_function('bar', bar)
"""


@pytest.fixture(autouse=True)
async def setup(client):
    await client.function_flush()


@pytest.fixture
async def simple_library(client):
    await client.function_load("lua", "coredis", library_definition)


@targets("redis_basic", "redis_cluster")
@pytest.mark.asyncio
@pytest.mark.min_server_version("6.9.0")
class TestFunctions:
    async def test_empty_library(self, client):
        assert await client.function_list() == {}

    async def test_load_library(self, client):
        assert await client.function_load(
            "lua",
            "coredis",
            library_definition,
        )
        libraries = await client.function_list()
        assert libraries["coredis"]
        assert len(libraries["coredis"]["functions"]) == 2
        stats = await client.function_stats()
        assert stats["running_script"] is None

    async def test_fcall(self, client, simple_library):
        assert await client.fcall("fu", ["a"], []) == "a"
        assert await client.fcall("bar", ["a"], [2]) == 2.0

    async def test_dump_restore(self, client, simple_library):
        dump = await client.function_dump()
        assert await client.function_flush()
        assert await client.function_list() == {}
        assert await client.function_restore(dump, policy=PureToken.FLUSH)
        assert len((await client.function_list())["coredis"]["functions"]) == 2


@targets("redis_basic", "redis_cluster")
@pytest.mark.asyncio
@pytest.mark.min_server_version("6.9.0")
class TestLibrary:
    async def test_register_library(self, client):
        library = await client.register_library("coredis", library_definition)
        assert len(library.functions) == 2

    async def test_load_library(self, client, simple_library):
        library = await client.get_library("coredis")
        assert len(library.functions) == 2

    async def test_call_library_function(self, client, simple_library):
        library = await client.get_library("coredis")
        assert await library["fu"](args=(1, 2, 3), keys=["A"]) == "A"
        assert await library["bar"](args=(1.0, 2.0, 3.0), keys=["A"]) == 1.0

    async def test_call_library_update(self, client, simple_library):
        library = await client.get_library("coredis")
        assert len(library.functions) == 2
        assert await library.update(
            """
        local function baz(keys, args)
            return args[1] + args[2]
        end
        redis.register_function('baz', baz)
        """
        )
        assert len(library.functions) == 1
        assert await library["baz"](args=[1, 2, 3]) == 3
