from __future__ import with_statement
import pytest
import pickle
import coredis


class TestEncoding:
    @pytest.fixture()
    def r(self, request):
        return coredis.StrictRedis(decode_responses=True)

    @pytest.mark.asyncio()
    async def test_simple_encoding(self, r):
        await r.flushdb()
        unicode_string = chr(124) + "abcd" + chr(125)
        await r.set("unicode-string", unicode_string)
        cached_val = await r.get("unicode-string")
        assert isinstance(cached_val, str)
        assert unicode_string == cached_val

    @pytest.mark.asyncio()
    async def test_list_encoding(self, r):
        unicode_string = chr(124) + "abcd" + chr(125)
        result = [unicode_string, unicode_string, unicode_string]
        await r.rpush("a", *result)
        assert await r.lrange("a", 0, -1) == result

    @pytest.mark.asyncio()
    async def test_object_value(self, r):
        unicode_string = chr(124) + "abcd" + chr(125)
        await r.set("unicode-string", Exception(unicode_string))
        cached_val = await r.get("unicode-string")
        assert isinstance(cached_val, str)
        assert unicode_string == cached_val

    @pytest.mark.asyncio()
    async def test_pickled_object(self):
        r = coredis.StrictRedis()
        obj = Exception("args")
        pickled_obj = pickle.dumps(obj)
        await r.set("pickled-obj", pickled_obj)
        cached_obj = await r.get("pickled-obj")
        assert isinstance(cached_obj, bytes)
        assert obj.args == pickle.loads(cached_obj).args
