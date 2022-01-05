from __future__ import with_statement
import pytest

from coredis.exceptions import NoScriptError, ResponseError
from coredis.utils import b


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


class TestScripting:
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_eval(self, r):
        await r.flushdb()
        await r.set("a", 2)
        # 2 * 3 == 6
        assert await r.eval(multiply_script, 1, "a", 3) == 6

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_evalsha(self, r):
        await r.set("a", 2)
        sha = await r.script_load(multiply_script)
        # 2 * 3 == 6
        assert await r.evalsha(sha, 1, "a", 3) == 6

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_evalsha_script_not_loaded(self, r):
        await r.set("a", 2)
        sha = await r.script_load(multiply_script)
        # remove the script from Redis's cache
        await r.script_flush()
        with pytest.raises(NoScriptError):
            await r.evalsha(sha, 1, "a", 3)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_script_loading(self, r):
        # get the sha, then clear the cache
        sha = await r.script_load(multiply_script)
        await r.script_flush()
        assert await r.script_exists(sha) == [False]
        await r.script_load(multiply_script)
        assert await r.script_exists(sha) == [True]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_script_object(self, r):
        await r.script_flush()
        await r.set("a", 2)
        multiply = r.register_script(multiply_script)
        precalculated_sha = multiply.sha
        assert precalculated_sha
        assert await r.script_exists(multiply.sha) == [False]
        # Test second evalsha block (after NoScriptError)
        assert await multiply.execute(keys=["a"], args=[3]) == 6
        # At this point, the script should be loaded
        assert await r.script_exists(multiply.sha) == [True]
        # Test that the precalculated sha matches the one from redis
        assert multiply.sha == precalculated_sha
        # Test first evalsha block
        assert await multiply.execute(keys=["a"], args=[3]) == 6

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_script_object_in_pipeline(self, r):
        await r.script_flush()
        multiply = r.register_script(multiply_script)
        precalculated_sha = multiply.sha
        assert precalculated_sha
        pipe = await r.pipeline()
        await pipe.set("a", 2)
        await pipe.get("a")
        await multiply.execute(keys=["a"], args=[3], client=pipe)
        assert await r.script_exists(multiply.sha) == [False]
        # [SET worked, GET 'a', result of multiple script]
        assert await pipe.execute() == [True, b("2"), 6]
        # The script should have been loaded by pipe.execute()
        assert await r.script_exists(multiply.sha) == [True]
        # The precalculated sha should have been the correct one
        assert multiply.sha == precalculated_sha

        # purge the script from redis's cache and re-run the pipeline
        # the multiply script should be reloaded by pipe.execute()
        await r.script_flush()
        pipe = await r.pipeline()
        await pipe.set("a", 2)
        await pipe.get("a")
        await multiply.execute(keys=["a"], args=[3], client=pipe)
        assert await r.script_exists(multiply.sha) == [False]
        # [SET worked, GET 'a', result of multiple script]
        assert await pipe.execute() == [True, b("2"), 6]
        assert await r.script_exists(multiply.sha) == [True]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_eval_msgpack_pipeline_error_in_lua(self, r):
        msgpack_hello = r.register_script(msgpack_hello_script)
        assert msgpack_hello.sha

        pipe = await r.pipeline()

        # avoiding a dependency to msgpack, this is the output of
        # msgpack.dumps({"name": "joe"})
        msgpack_message_1 = b"\x81\xa4name\xa3Joe"

        await msgpack_hello.execute(args=[msgpack_message_1], client=pipe)

        assert await r.script_exists(msgpack_hello.sha) == [False]
        assert (await pipe.execute())[0] == b"hello Joe"
        assert await r.script_exists(msgpack_hello.sha) == [True]

        msgpack_hello_broken = r.register_script(msgpack_hello_script_broken)

        await msgpack_hello_broken.execute(args=[msgpack_message_1], client=pipe)
        with pytest.raises(ResponseError) as excinfo:
            await pipe.execute()
        assert excinfo.type == ResponseError
