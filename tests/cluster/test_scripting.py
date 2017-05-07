# -*- coding: utf-8 -*-

# python std lib
from __future__ import with_statement

# rediscluster imports
import asyncio
from aredis.exceptions import RedisClusterException, NoScriptError, ResponseError
from aredis.utils import b

# 3rd party imports
import pytest


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


class TestScripting(object):

    async def reset_scripts(self, r):
        await r.script_flush()

    @pytest.mark.asyncio()
    async def test_eval(self, r):
        await r.set('a', 2)
        # 2 * 3 == 6
        assert await r.eval(multiply_script, 1, 'a', 3) == 6

    @pytest.mark.asyncio()
    async def test_eval_same_slot(self, r):
        await r.set('A{foo}', 2)
        await r.set('B{foo}', 4)
        # 2 * 4 == 8

        script = """
        local value = redis.call('GET', KEYS[1])
        local value2 = redis.call('GET', KEYS[2])
        return value * value2
        """
        result = await r.eval(script, 2, 'A{foo}', 'B{foo}')
        assert result == 8

    @pytest.mark.asyncio()
    async def test_eval_crossslot(self, r):
        """
        This test assumes that {foo} and {bar} will not go to the same
        server when used. In 3 masters + 3 slaves config this should pass.
        """
        await r.set('A{foo}', 2)
        await r.set('B{bar}', 4)
        # 2 * 4 == 8

        script = """
        local value = redis.call('GET', KEYS[1])
        local value2 = redis.call('GET', KEYS[2])
        return value * value2
        """
        with pytest.raises(RedisClusterException):
            await r.eval(script, 2, 'A{foo}', 'B{bar}')

    @pytest.mark.asyncio()
    async def test_evalsha(self, r):
        await r.set('a', 2)
        sha = await r.script_load(multiply_script)
        # 2 * 3 == 6
        assert await r.evalsha(sha, 1, 'a', 3) == 6

    @pytest.mark.asyncio()
    async def test_evalsha_script_not_loaded(self, r):
        await r.set('a', 2)
        sha = await r.script_load(multiply_script)
        # remove the script from Redis's cache
        await r.script_flush()
        with pytest.raises(NoScriptError):
            await r.evalsha(sha, 1, 'a', 3)

    @pytest.mark.asyncio()
    async def test_script_loading(self, r):
        # get the sha, then clear the cache
        sha = await r.script_load(multiply_script)
        await r.script_flush()
        assert await r.script_exists(sha) == [False]
        await r.script_load(multiply_script)
        assert await r.script_exists(sha) == [True]

    @pytest.mark.asyncio()
    async def test_script_object(self, r):
        await r.set('a', 2)
        multiply = r.register_script(multiply_script)
        assert not multiply.sha
        # test evalsha fail -> script load + retry
        assert await multiply.execute(keys=['a'], args=[3]) == 6
        assert multiply.sha
        assert await r.script_exists(multiply.sha) == [True]
        # test first evalsha
        assert await multiply.execute(keys=['a'], args=[3]) == 6

    @pytest.mark.xfail(reason="Not Yet Implemented")
    async def test_script_object_in_pipeline(self, r):
        multiply = await r.register_script(multiply_script)
        assert not multiply.sha
        pipe = r.pipeline()
        await pipe.set('a', 2)
        await pipe.get('a')
        multiply(keys=['a'], args=[3], client=pipe)
        # even though the pipeline wasn't executed yet, we made sure the
        # script was loaded and got a valid sha
        assert multiply.sha
        assert await r.script_exists(multiply.sha) == [True]
        # [SET worked, GET 'a', result of multiple script]
        assert await pipe.execute() == [True, b('2'), 6]

        # purge the script from redis's cache and re-run the pipeline
        # the multiply script object knows it's sha, so it shouldn't get
        # reloaded until pipe.execute()
        await r.script_flush()
        pipe = await r.pipeline()
        await pipe.set('a', 2)
        await pipe.get('a')
        assert multiply.sha
        multiply(keys=['a'], args=[3], client=pipe)
        assert await r.script_exists(multiply.sha) == [False]
        # [SET worked, GET 'a', result of multiple script]
        assert await pipe.execute() == [True, b('2'), 6]

    @pytest.mark.xfail(reason="Not Yet Implemented")
    async def test_eval_msgpack_pipeline_error_in_lua(self, r):
        msgpack_hello = await r.register_script(msgpack_hello_script)
        assert not msgpack_hello.sha

        pipe = r.pipeline()

        # avoiding a dependency to msgpack, this is the output of
        # msgpack.dumps({"name": "joe"})
        msgpack_message_1 = b'\x81\xa4name\xa3Joe'

        msgpack_hello(args=[msgpack_message_1], client=pipe)

        assert await r.script_exists(msgpack_hello.sha) == [True]
        assert await pipe.execute()[0] == b'hello Joe'

        msgpack_hello_broken = await r.register_script(msgpack_hello_script_broken)

        msgpack_hello_broken(args=[msgpack_message_1], client=pipe)
        with pytest.raises(ResponseError) as excinfo:
            await pipe.execute()
        assert excinfo.type == ResponseError
