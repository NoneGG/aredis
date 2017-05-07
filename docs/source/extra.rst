Extra
=====

Cache
-----

There are two kinds of cache class(Cache & HerdCache) provided.
Cache classes consists of IdentityGenerator(used to generate unique identity in redis),
Serializer(used to serialize content before compress and finally put in redis),
Compressor(used to compress cache to reduce memory usage of redis.
IdentityGenerator, Serializer, Compressor can be overwritten to meet your special needs,
and if you don't need it, just set them to None when intialize a cache:

.. code-block:: python

    >>> class CustomIdentityGenerator(IdentityGenerator):
    >>>     def generate(self, key, content):
    >>>         return key
    >>>
    >>> def expensive_work(data):
    >>> """some work that waits for io or occupy cpu"""
    >>>     return data
    >>>
    >>> async def example():
    >>>     client = aredis.StrictRedis()
    >>>     await client.flushall()
    >>>     cache = client.cache('example_cache',
    >>>             identity_generator_class=CustomIdentityGenerator)
    >>>     data = {1: 1}
    >>>     await cache.set('example_key', expensive_work(data), data)
    >>>     res = await cache.get('example_key', data)
    >>>     assert res == expensive_work(data)

For ease of use and expandability, only `set`, `set_many`, `exists`, `delete`, `delete_many`,
`ttl`, `get` APIs are realized.

HerdCache is a solution for `thundering herd problem <https://en.wikipedia.org/wiki/Thundering_herd_problem>`_
It is suitable for scene with low consistency and in which refresh cache costs a lot.
It will save redundant update work when there are multi process read cache from redis and the cache is expired.
If the cache is expired is judged by the expire time saved with each key, and the real expire time of the key
`real_expire_time = the time key is set + expire_time + herd_timeout` once a process find out that the cache is expired,
it will reset the expire time saved in redis with `new_expire_time = the time key is found expired + extend_expire_time`,
and return None(act like cache expired), so that other processes will not noticed the cache expired.