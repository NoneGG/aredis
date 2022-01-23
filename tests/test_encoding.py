import pickle

import pytest

import coredis


@pytest.fixture
async def redis(redis_basic_server):
    client = coredis.StrictRedis(decode_responses=True)
    await client.flushdb()
    return client


@pytest.mark.asyncio()
class TestEncoding:
    async def test_simple_encoding(self, redis):
        unicode_string = chr(124) + "abcd" + chr(125)
        await redis.set("unicode-string", unicode_string)
        cached_val = await redis.get("unicode-string")
        assert isinstance(cached_val, str)
        assert unicode_string == cached_val

    async def test_list_encoding(self, redis):
        unicode_string = chr(124) + "abcd" + chr(125)
        result = [unicode_string, unicode_string, unicode_string]
        await redis.rpush("a", *result)
        assert await redis.lrange("a", 0, -1) == result

    async def test_object_value(self, redis):
        unicode_string = chr(124) + "abcd" + chr(125)
        await redis.set("unicode-string", Exception(unicode_string))
        cached_val = await redis.get("unicode-string")
        assert isinstance(cached_val, str)
        assert unicode_string == cached_val

    async def test_pickled_object(self, redis_basic):
        obj = Exception("args")
        pickled_obj = pickle.dumps(obj)
        await redis_basic.set("pickled-obj", pickled_obj)
        cached_obj = await redis_basic.get("pickled-obj")
        assert isinstance(cached_obj, bytes)
        assert obj.args == pickle.loads(cached_obj).args
