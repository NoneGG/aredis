import pickle

import pytest

import coredis


@pytest.fixture
async def redis_no_decode(redis_basic_server):
    client = coredis.Redis()
    await client.flushdb()
    return client


@pytest.mark.asyncio()
class TestEncoding:
    async def test_simple_encoding(self, redis_basic):
        unicode_string = chr(124) + "abcd" + chr(125)
        await redis_basic.set("unicode-string", unicode_string)
        cached_val = await redis_basic.get("unicode-string")
        assert isinstance(cached_val, str)
        assert unicode_string == cached_val

    async def test_list_encoding(self, redis_basic):
        unicode_string = chr(124) + "abcd" + chr(125)
        result = [unicode_string, unicode_string, unicode_string]
        await redis_basic.rpush("a", result)
        assert await redis_basic.lrange("a", 0, -1) == result

    async def test_object_value(self, redis_basic):
        unicode_string = chr(124) + "abcd" + chr(125)
        await redis_basic.set("unicode-string", str(Exception(unicode_string)))
        cached_val = await redis_basic.get("unicode-string")
        assert isinstance(cached_val, str)
        assert unicode_string == cached_val

    async def test_pickled_object(self, redis_no_decode):
        obj = Exception("args")
        pickled_obj = pickle.dumps(obj)
        await redis_no_decode.set("pickled-obj", pickled_obj)
        cached_obj = await redis_no_decode.get("pickled-obj")
        assert isinstance(cached_obj, bytes)
        assert obj.args == pickle.loads(cached_obj).args
