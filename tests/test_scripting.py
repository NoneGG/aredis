import pytest

from coredis.exceptions import NoScriptError, ResponseError
from coredis.utils import b
from tests.conftest import targets

multiply_script = """
local value = redis.call('GET', KEYS[1])
value = tonumber(value)

return value * ARGV[1]"""

msgpack_hello_script = """
local message = cmsgpack.unpack(ARGV[1])
local name = message['name']

return "hello " .. name
"""
msgpack_hello_script_broken = """
local message = cmsgpack.unpack(ARGV[1])
local names = message['name']

return "hello " .. name
"""


@pytest.mark.asyncio()
@targets("redis_basic")
class TestScripting:
    async def test_eval(self, client):
        await client.set("a", 2)
        # 2 * 3 == 6
        assert await client.eval(multiply_script, 1, "a", 3) == 6

    async def test_evalsha(self, client):
        await client.set("a", 2)
        sha = await client.script_load(multiply_script)
        # 2 * 3 == 6
        assert await client.evalsha(sha, 1, "a", 3) == 6

    async def test_evalsha_script_not_loaded(self, client):
        await client.set("a", 2)
        sha = await client.script_load(multiply_script)
        # remove the script from Redis's cache
        await client.script_flush()
        with pytest.raises(NoScriptError):
            await client.evalsha(sha, 1, "a", 3)

    async def test_script_loading(self, client):
        # get the sha, then clear the cache
        sha = await client.script_load(multiply_script)
        await client.script_flush()
        assert await client.script_exists(sha) == [False]
        await client.script_load(multiply_script)
        assert await client.script_exists(sha) == [True]

    async def test_script_object(self, client):
        await client.script_flush()
        await client.set("a", 2)
        multiply = client.register_script(multiply_script)
        precalculated_sha = multiply.sha
        assert precalculated_sha
        assert await client.script_exists(multiply.sha) == [False]
        # Test second evalsha block (after NoScriptError)
        assert await multiply.execute(keys=["a"], args=[3]) == 6
        # At this point, the script should be loaded
        assert await client.script_exists(multiply.sha) == [True]
        # Test that the precalculated sha matches the one from redis
        assert multiply.sha == precalculated_sha
        # Test first evalsha block
        assert await multiply.execute(keys=["a"], args=[3]) == 6

    async def test_script_object_in_pipeline(self, client):
        await client.script_flush()
        multiply = client.register_script(multiply_script)
        precalculated_sha = multiply.sha
        assert precalculated_sha
        pipe = await client.pipeline()
        await pipe.set("a", 2)
        await pipe.get("a")
        await multiply.execute(keys=["a"], args=[3], client=pipe)
        assert await client.script_exists(multiply.sha) == [False]
        # [SET worked, GET 'a', result of multiple script]
        assert await pipe.execute() == [True, b("2"), 6]
        # The script should have been loaded by pipe.execute()
        assert await client.script_exists(multiply.sha) == [True]
        # The precalculated sha should have been the correct one
        assert multiply.sha == precalculated_sha

        # purge the script from redis's cache and re-run the pipeline
        # the multiply script should be reloaded by pipe.execute()
        await client.script_flush()
        pipe = await client.pipeline()
        await pipe.set("a", 2)
        await pipe.get("a")
        await multiply.execute(keys=["a"], args=[3], client=pipe)
        assert await client.script_exists(multiply.sha) == [False]
        # [SET worked, GET 'a', result of multiple script]
        assert await pipe.execute() == [True, b("2"), 6]
        assert await client.script_exists(multiply.sha) == [True]

    async def test_eval_msgpack_pipeline_error_in_lua(self, client):
        msgpack_hello = client.register_script(msgpack_hello_script)
        assert msgpack_hello.sha

        pipe = await client.pipeline()

        # avoiding a dependency to msgpack, this is the output of
        # msgpack.dumps({"name": "joe"})
        msgpack_message_1 = b"\x81\xa4name\xa3Joe"

        await msgpack_hello.execute(args=[msgpack_message_1], client=pipe)

        assert await client.script_exists(msgpack_hello.sha) == [False]
        assert (await pipe.execute())[0] == b"hello Joe"
        assert await client.script_exists(msgpack_hello.sha) == [True]

        msgpack_hello_broken = client.register_script(msgpack_hello_script_broken)

        await msgpack_hello_broken.execute(args=[msgpack_message_1], client=pipe)
        with pytest.raises(ResponseError) as excinfo:
            await pipe.execute()
        assert excinfo.type == ResponseError
