# -*- coding: utf-8 -*-

from __future__ import with_statement

import pytest

from coredis.exceptions import NoScriptError, RedisClusterException, ResponseError

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
    async def reset_scripts(self, redis_cluster):
        await redis_cluster.script_flush()

    @pytest.mark.asyncio()
    async def test_eval(self, redis_cluster):
        await redis_cluster.set("a", 2)
        # 2 * 3 == 6
        assert await redis_cluster.eval(multiply_script, ["a"], [3]) == 6

    @pytest.mark.asyncio()
    async def test_eval_same_slot(self, redis_cluster):
        await redis_cluster.set("A{foo}", 2)
        await redis_cluster.set("B{foo}", 4)
        # 2 * 4 == 8

        script = """
        local value = redis.call('GET', KEYS[1])
        local value2 = redis.call('GET', KEYS[2])
        return value * value2
        """
        result = await redis_cluster.eval(script, ["A{foo}", "B{foo}"])
        assert result == 8

    @pytest.mark.asyncio()
    async def test_eval_crossslot(self, redis_cluster):
        """
        This test assumes that {foo} and {bar} will not go to the same
        server when used. In 3 masters + 3 slaves config this should pass.
        """
        await redis_cluster.set("A{foo}", 2)
        await redis_cluster.set("B{bar}", 4)
        # 2 * 4 == 8

        script = """
        local value = redis.call('GET', KEYS[1])
        local value2 = redis.call('GET', KEYS[2])
        return value * value2
        """
        with pytest.raises(RedisClusterException):
            await redis_cluster.eval(script, ["A{foo}", "B{bar}"])

    @pytest.mark.asyncio()
    async def test_evalsha(self, redis_cluster):
        await redis_cluster.set("a", 2)
        sha = await redis_cluster.script_load(multiply_script)
        # 2 * 3 == 6
        assert await redis_cluster.evalsha(sha, ["a"], [3]) == 6

    @pytest.mark.asyncio()
    async def test_evalsha_script_not_loaded(self, redis_cluster):
        await redis_cluster.set("a", 2)
        sha = await redis_cluster.script_load(multiply_script)
        # remove the script from Redis's cache
        await redis_cluster.script_flush()
        with pytest.raises(NoScriptError):
            await redis_cluster.evalsha(sha, ["a"], [3])

    @pytest.mark.asyncio()
    async def test_script_loading(self, redis_cluster):
        # get the sha, then clear the cache
        sha = await redis_cluster.script_load(multiply_script)
        await redis_cluster.script_flush()

        assert await redis_cluster.script_exists([sha]) == (False,)
        await redis_cluster.script_load(multiply_script)
        assert await redis_cluster.script_exists([sha]) == (True,)

    @pytest.mark.asyncio()
    async def test_script_object(self, redis_cluster):
        await redis_cluster.set("a", 2)
        multiply = redis_cluster.register_script(multiply_script)
        assert multiply.sha == "29cdf3e36c89fa05d7e6d6b9734b342ab15c9ea7"
        # test evalsha fail -> script load + retry
        assert await multiply.execute(keys=["a"], args=[3]) == 6
        assert multiply.sha
        assert await redis_cluster.script_exists([multiply.sha]) == (True,)
        # test first evalsha
        assert await multiply.execute(keys=["a"], args=[3]) == 6

    @pytest.mark.asyncio()
    @pytest.mark.xfail(reason="Not Yet Implemented")
    async def test_script_object_in_pipeline(self, redis_cluster):
        multiply = await redis_cluster.register_script(multiply_script)
        assert not multiply.sha
        pipe = redis_cluster.pipeline()
        await pipe.set("a", 2)
        await pipe.get("a")
        multiply(keys=["a"], args=[3], client=pipe)
        # even though the pipeline wasn't executed yet, we made sure the
        # script was loaded and got a valid sha
        assert multiply.sha
        assert await redis_cluster.script_exists(multiply.sha) == (True,)
        # [SET worked, GET 'a', result of multiple script]
        assert await pipe.execute() == [True, "2", 6]

        # purge the script from redis's cache and re-run the pipeline
        # the multiply script object knows it's sha, so it shouldn't get
        # reloaded until pipe.execute()
        await redis_cluster.script_flush()
        pipe = await redis_cluster.pipeline()
        await pipe.set("a", 2)
        await pipe.get("a")
        assert multiply.sha
        multiply(keys=["a"], args=[3], client=pipe)
        assert await redis_cluster.script_exists(multiply.sha) == (False,)
        # [SET worked, GET 'a', result of multiple script]
        assert await pipe.execute() == [True, "2", 6]

    @pytest.mark.asyncio()
    @pytest.mark.xfail(reason="Not Yet Implemented")
    async def test_eval_msgpack_pipeline_error_in_lua(self, redis_cluster):
        msgpack_hello = await redis_cluster.register_script(msgpack_hello_script)
        assert not msgpack_hello.sha

        pipe = redis_cluster.pipeline()

        # avoiding a dependency to msgpack, this is the output of
        # msgpack.dumps({"name": "joe"})
        msgpack_message_1 = "\x81\xa4name\xa3Joe"

        msgpack_hello(args=[msgpack_message_1], client=pipe)

        assert await redis_cluster.script_exists(msgpack_hello.sha) == (True,)
        assert await pipe.execute()[0] == "hello Joe"

        msgpack_hello_broken = await redis_cluster.register_script(
            msgpack_hello_script_broken
        )

        msgpack_hello_broken(args=[msgpack_message_1], client=pipe)
        with pytest.raises(ResponseError) as excinfo:
            await pipe.execute()
        assert excinfo.type == ResponseError
