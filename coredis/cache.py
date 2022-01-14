import hashlib
import time
import zlib

from coredis.exceptions import CompressError, SerializeError
from coredis.utils import b

try:
    import ujson as json
except ImportError:
    import json


class IdentityGenerator:
    """
    Generator of identity for unique key,
    you may overwrite it to meet your customize requirements.
    """

    TEMPLATE = "{app}:{key}:{content}"

    def __init__(self, app, encoding="utf-8"):
        self.app = app
        self.encoding = encoding

    def _trans_type(self, content):
        if isinstance(content, str):
            content = content.encode(self.encoding)
        elif isinstance(content, int):
            content = b(str(content))
        elif isinstance(content, float):
            content = b(repr(content))
        return content

    def generate(self, key, content):
        content = self._trans_type(content)
        md5 = hashlib.md5()
        md5.update(content)
        hash = md5.hexdigest()
        identity = self.TEMPLATE.format(app=self.app, key=key, content=hash)
        return identity


class Compressor:
    """
    Uses zlib to compress and decompress Redis cache. You may implement your
    own Compressor implementing `compress` and `decompress` methods
    """

    min_length = 15
    preset = 6

    def __init__(self, encoding="utf-8"):
        self.encoding = encoding

    def _trans_type(self, content):
        if isinstance(content, str):
            content = content.encode(self.encoding)
        elif isinstance(content, int):
            content = b(str(content))
        elif isinstance(content, float):
            content = b(repr(content))
        if not isinstance(content, bytes):
            raise TypeError("Wrong data type({}) to compress".format(type(content)))
        return content

    def compress(self, content):
        content = self._trans_type(content)
        if len(content) > self.min_length:
            try:
                return zlib.compress(content, self.preset)
            except zlib.error:
                raise CompressError("Content can not be compressed.")
        return content

    def decompress(self, content):
        content = self._trans_type(content)
        try:
            return zlib.decompress(content)
        except zlib.error:
            raise CompressError("Content can not be decompressed.")


class Serializer:
    """
    Uses json to serialize and deserialize cache to str. You may implement
    your own Serializer implemting `serialize` and `deserialize` methods.
    """

    def __init__(self, encoding="utf-8"):
        self.encoding = encoding

    def _trans_type(self, content):
        if isinstance(content, bytes):
            content = content.decode(self.encoding)
        if not isinstance(content, str):
            raise TypeError("Wrong data type({}) to compress".format(type(content)))
        return content

    def serialize(self, content):
        try:
            return json.dumps(content)
        except Exception:
            raise SerializeError("Content can not be serialized.")

    def deserialize(self, content):
        content = self._trans_type(content)
        try:
            return json.loads(content)
        except Exception:
            raise SerializeError("Content can not be deserialized.")


class BasicCache:
    """Basic cache class, should not be used explicitly"""

    def __init__(
        self,
        client,
        app="",
        identity_generator_class=IdentityGenerator,
        compressor_class=Compressor,
        serializer_class=Serializer,
        encoding="utf-8",
    ):
        self.client = client
        self.identity_generator = self.compressor = self.serializer = None
        # set identity generator, compressor and serializer to None if not needed
        if identity_generator_class:
            self.identity_generator = identity_generator_class(app, encoding)
        if compressor_class:
            self.compressor = compressor_class(encoding)
        if serializer_class:
            self.serializer = serializer_class(encoding)

    def __repr__(self):
        return "{}<{}>".format(type(self).__name__, repr(self.client))

    def _gen_identity(self, key, param=None):
        """generate identity according to key and param given"""
        if self.identity_generator and param is not None:
            if self.serializer:
                param = self.serializer.serialize(param)
            if self.compressor:
                param = self.compressor.compress(param)
            identity = self.identity_generator.generate(key, param)
        else:
            identity = key
        return identity

    def _pack(self, content):
        """Packs the content using serializer and compressor"""
        if self.serializer:
            content = self.serializer.serialize(content)
        if self.compressor:
            content = self.compressor.compress(content)
        return content

    def _unpack(self, content):
        """Unpacks cache using serializer and compressor"""
        if self.compressor:
            try:
                content = self.compressor.decompress(content)
            except CompressError:
                pass
        if self.serializer:
            content = self.serializer.deserialize(content)
        return content

    async def delete(self, key, param=None):
        """
        Deletes cache corresponding to identity
        generated from key and param
        """
        identity = self._gen_identity(key, param)
        return await self.client.delete(identity)

    async def delete_pattern(self, pattern, count=None):
        """
        Deletes cache according to pattern in redis,
        delete `count` keys each time
        """
        cursor = "0"
        count_deleted = 0
        while cursor != 0:
            cursor, identities = await self.client.scan(
                cursor=cursor, match=pattern, count=count
            )
            count_deleted += await self.client.delete(*identities)
        return count_deleted

    async def exist(self, key, param=None):
        """Checks if specific identity exists"""
        identity = self._gen_identity(key, param)
        return await self.client.exists(identity)

    async def ttl(self, key, param=None):
        """Gets time to live of a specific identity"""
        identity = self._gen_identity(key, param)
        return await self.client.ttl(identity)


class Cache(BasicCache):
    """Provides basic caching"""

    async def get(self, key, param=None):
        identity = self._gen_identity(key, param)
        res = await self.client.get(identity)
        if res:
            res = self._unpack(res)
        return res

    async def set(self, key, value, param=None, expire_time=None):
        identity = self._gen_identity(key, param)
        value = self._pack(value)
        return await self.client.set(identity, value, ex=expire_time)

    async def set_many(self, data, param=None, expire_time=None):
        async with await self.client.pipeline() as pipeline:
            for key, value in data.items():
                identity = self._gen_identity(key, param)
                value = self._pack(value)
                await pipeline.set(identity, value, expire_time)
            return await pipeline.execute()


class HerdCache(BasicCache):
    """
    Cache that handles thundering herd problem
    (https://en.wikipedia.org/wiki/Thundering_herd_problem)
    by cacheing expiration time in set instead of directly using expire
    operation of redis.
    This kind of cache is suitable for low consistency scene where update
    operations are expensive.
    """

    def __init__(
        self,
        client,
        app="",
        identity_generator_class=IdentityGenerator,
        compressor_class=Compressor,
        serializer_class=Serializer,
        default_herd_timeout=1,
        extend_herd_timeout=1,
        encoding="utf-8",
    ):
        self.default_herd_timeout = default_herd_timeout
        self.extend_herd_timeout = extend_herd_timeout
        super(HerdCache, self).__init__(
            client,
            app,
            identity_generator_class,
            compressor_class,
            serializer_class,
            encoding,
        )

    async def set(self, key, value, param=None, expire_time=None, herd_timeout=None):
        """
        Uses key and param to generate identity and pack the content,
        expire the key within real_timeout if expire_time is given.
        real_timeout is equal to the sum of expire_time and herd_time.
        The content is cached with expire_time.
        """
        identity = self._gen_identity(key, param)
        expected_expired_ts = int(time.time())
        if expire_time:
            expected_expired_ts += expire_time
        expected_expired_ts += herd_timeout or self.default_herd_timeout
        value = self._pack([value, expected_expired_ts])
        return await self.client.set(identity, value, ex=expire_time)

    async def set_many(self, data, param=None, expire_time=None, herd_timeout=None):
        async with await self.client.pipeline() as pipeline:
            for key, value in data.items():
                identity = self._gen_identity(key, param)
                expected_expired_ts = int(time.time())
                if expire_time:
                    expected_expired_ts += expire_time
                expected_expired_ts += herd_timeout or self.default_herd_timeout
                value = self._pack([value, expected_expired_ts])
                await pipeline.set(identity, value, ex=expire_time)
            return await pipeline.execute()

    async def get(self, key, param=None, extend_herd_timeout=None):
        """
        Uses key or identity generated from key and param to get cached
        content and expiratiom time.
        Uses time.now() to check expiration. If not expired, returns unpacked
        content. Otherwise returns None and sets cache with extended timeout
        """
        identity = self._gen_identity(key, param)
        res = await self.client.get(identity)
        if res:
            res, timeout = self._unpack(res)
            now = int(time.time())
            if timeout <= now:
                extend_timeout = extend_herd_timeout or self.extend_herd_timeout
                expected_expired_ts = now + extend_timeout
                value = self._pack([res, expected_expired_ts])
                await self.client.set(identity, value, extend_timeout)
                return None
        return res
