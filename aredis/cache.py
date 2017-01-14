import hashlib
import zlib
try:
    import ujson as json
except ImportError:
    import json

from aredis.utils import b
from aredis.exceptions import CompressError


class IdentityGenerator(object):
    """
    Generator of identity for unique key
    """

    TEMPLATE = '{app}:{key}:{content}'

    def __init__(self, app, encoding='utf-8'):
        self.app = app
        self.encoding = encoding

    def generate(self, key, content):
        if isinstance(content, str):
            content = content.encode(self.encoding)
        elif isinstance(content, int):
            content = b(str(content))
        elif isinstance(content, float):
            content = b(repr(content))
        md5 = hashlib.md5()
        md5.update(content)
        hash = md5.hexdigest()
        identity = self.TEMPLATE.format(app=self.app, key=key, content=hash)
        return identity


class Compressor(object):
    """
    use zlib to compress and decompress cache in redis,
    you may overwrite your own Compressor
    with api compress and decompress
    """

    min_length = 15
    preset = 6

    def compress(self, content):
        if len(content) > self.min_length:
            return zlib.compress(content, self.preset)
        return content

    def decompress(self, content):
        try:
            return zlib.decompress(content)
        except zlib.error as exc:
            raise CompressError(exc)


class Serializer(object):
    """
    use json to serialize and deserialize cache to str,
    you may overwrite your own serialize
    with api serialize and deserialize
    """

    def serialize(self, content):
        return json.dumps(content)

    def deserialize(self, content):
        return json.loads(content)


class Cache(object):
    """Basic cache class which provides basic function"""

    def __init__(self, client, app='', identity_generator_class=IdentityGenerator,
                 compressor_class=Compressor, serializer_class=Serializer,
                 encoding='utf-8'):
        self.client = client
        self.identity_generator = self.compressor = self.serializer = None
        if identity_generator_class:
            self.identity_generator = identity_generator_class(app, encoding)
        if compressor_class:
            self.compressor = compressor_class()
        if serializer_class:
            self.serializer = serializer_class()

    def __repr__(self):
        return "{}<{}>".format(type(self).__name__, repr(self.client))

    def _gen_identity(self, key, value=None):
        if self.identity_generator and value:
            if self.serializer:
                value = self.serializer.serialize(value)
            if self.compressor:
                value = self.compressor.compress(value)
            identity = self.identity_generator.generate(key, value)
        else:
            identity = key
        return identity

    def _transfer_content(self, content):
        if self.serializer:
            content = self.serializer.serialize(content)
        if self.compressor:
            content = self.compressor.compress(content)
        return content

    def _recover_cache(self, content):
        if self.compressor:
            content = self.compressor.decompress(content)
        if self.serializer:
            content = self.serializer.deserialize(content)
        return content

    async def get(self, key, value=None):
        identity = self._gen_identity(key, value)
        res = await self.client.get(identity)
        self._recover_cache(res)
        return res

    async def set(self, key, value, expire_time=None):
        identity = self._gen_identity(key, value)
        self._transfer_content(value)
        return await self.client.set(identity, value, ex=expire_time)

    async def set_many(self, data, expire_time=None):
        pipeline = await self.client.pipeline()
        for key, value in data.items():
            self._transfer_content(value)
            await pipeline.set(key, value, expire_time)
        return await pipeline.execute()

    async def delete(self, key, value=None):
        identity = self._gen_identity(key, value)
        return await self.client.delete(identity)

    async def delete_pattern(self, pattern, count=None):
        cursor = '0'
        count_deleted = 0
        while cursor != 0:
            cursor, identities = await self.client.scan(
                cursor=cursor, match=pattern, count=count
            )
            await self.client.delete(identities)
            count_deleted += len(identities)
        return count_deleted

    async def exist(self, key, value=None):
        identity = self._gen_identity(key, value)
        return await self.client.exists(identity)

    async def ttl(self, key, value=None):
        identity = self._gen_identity(key, value)
        return await self.client.ttl(identity)


class HerdCache(Cache):
    """Cache that won't cause herd problem, but may use more memory in redis"""

    def __init__(self, client, app='', identity_generator_class=IdentityGenerator,
                 compressor_class=Compressor, serializer_class=Serializer,
                 encoding='utf-8'):
        super(HerdCache, self).__init__(client, app, identity_generator_class,
                                        compressor_class, serializer_class, encoding)

    def _transfer_content(self, content):
        
