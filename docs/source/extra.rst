Extra
=====

Lock
----

`For now Lock only support for single redis node, please don't use it in cluster env.`

There are two kinds of `Lock class` available for now, you can also make your own for special requirements.

.. py:method:: lock(self, name, timeout=None, sleep=0.1, blocking_timeout=None, lock_class=None, thread_local=True)

    Return a new Lock object using key ``name`` that mimics
    the behavior of threading.Lock.

    If specified, ``timeout`` indicates a maximum life for the lock.
    By default, it will remain locked until release() is called.

    ``sleep`` indicates the amount of time to sleep per loop iteration
    when the lock is in blocking mode and another client is currently
    holding the lock.

    ``blocking_timeout`` indicates the maximum amount of time in seconds to
    spend trying to acquire the lock. A value of ``None`` indicates
    continue trying forever. ``blocking_timeout`` can be specified as a
    float or integer, both representing the number of seconds to wait.

    ``lock_class`` forces the specified lock implementation.

    ``thread_local`` indicates whether the lock token is placed in
    thread-local storage. By default, the token is placed in thread local
    storage so that a thread only sees its token, not a token set by
    another thread. Consider the following timeline:

        time: 0, thread-1 acquires `my-lock`, with a timeout of 5 seconds.
                 thread-1 sets the token to "abc"
        time: 1, thread-2 blocks trying to acquire `my-lock` using the
                 Lock instance.
        time: 5, thread-1 has not yet completed. redis expires the lock
                 key.
        time: 5, thread-2 acquired `my-lock` now that it's available.
                 thread-2 sets the token to "xyz"
        time: 6, thread-1 finishes its work and calls release(). if the
                 token is *not* stored in thread local storage, then
                 thread-1 would see the token value as "xyz" and would be
                 able to successfully release the thread-2's lock.

    In some use cases it's necessary to disable thread local storage. For
    example, if you have code where one thread acquires a lock and passes
    that lock instance to a worker thread to release later. If thread
    local storage isn't disabled in this case, the worker thread won't see
    the token set by the thread that acquired the lock. Our assumption
    is that these cases aren't common and as such default to using
    thread local storage.

.. code-block:: python

    async def example():
        client = aredis.StrictRedis()
        await client.flushall()
        lock = client.lock('lalala')
        print(await lock.acquire())
        print(await lock.acquire(blocking=False))
        print(await lock.release())
        print(await lock.acquire())

    # True
    # False
    # None
    # True


Cluster Lock
------------
    Cluster lock is supposed to solve distributed lock problem in redis cluster.
    Since high availability is provided by redis cluster using master-slave model,
    the kind of lock aims to solve the fail-over problem referred in distributed lock
    post given by redis official.

    Why not use Redlock algorithm provided by official directly?

    It is impossible to make a key hashed to different nodes
    in a redis cluster and hard to generate keys
    in a specific rule and make sure they do not migrated in cluster.
    In the worst situation, all key slots may exists in one node.
    Then the availability will be the same as one key in one node.

    For more discussion please see:
    https://github.com/NoneGG/aredis/issues/55

    To gather more ideas i also raise a problem in stackoverflow:
    Not_a_Golfer's solution is awesome, but considering the migration problem, i think this solution may be better.
    https://stackoverflow.com/questions/46438857/how-to-create-a-distributed-lock-using-redis-cluster

    My solution is described below:

    1. random token + SETNX + expire time to acquire a lock in cluster master node

    2. if lock is acquired successfully then check the lock in slave nodes(may there be N slave nodes)
    using READONLY mode, if N/2+1 is synced successfully then break the check and return True,
    time used to check is also accounted into expire time

    3.Use lua script described in redlock algorithm to release lock
    with the client which has the randomly generated token,
    if the client crashes, then wait until the lock key expired.

    Actually you can regard the algorithm as a master-slave version of redlock,
    which is designed for multi master nodes.

    Please read these article below before using this cluster lock in your app.
    https://redis.io/topics/distlock
    http://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html
    http://antirez.com/news/101

.. code-block:: python

    async def example():
        client = aredis.StrictRedis()
        await client.flushall()
        lock = client.lock('lalala', lock_class=ClusterLock, timeout=1)
        print(await lock.acquire())
        print(await lock.acquire(blocking=False))
        print(await lock.release())
        print(await lock.acquire())

    # True
    # False
    # None
    # True

Cache
-----

Cache has support for both single redis node and redis cluster.

There are two kinds of cache class(Cache & HerdCache) provided.
Cache classes consists of IdentityGenerator(used to generate unique identity in redis),
Serializer(used to serialize content before compress and finally put in redis),
Compressor(used to compress cache to reduce memory usage of redis.
IdentityGenerator, Serializer, Compressor can be overwritten to meet your special needs,
and if you don't need it, just set them to None when intialize a cache:

.. py:method:: cache(self, name, cache_class=Cache, identity_generator_class=IdentityGenerator, compressor_class=Compressor, serializer_class=Serializer, *args, **kwargs)

        Return a cache object using default identity generator,
        serializer and compressor.

        ``name`` is used to identify the series of your cache

        ``cache_class`` Cache is for normal use and HerdCache is used in case of Thundering Herd Problem

        ``identity_generator_class`` is the class used to generate the real unique key in cache, can be overwritten to
        meet your special needs. It should provide `generate` API

        ``compressor_class`` is the class used to compress cache in redis, can be overwritten with API `compress` and `decompress` retained.

        ``serializer_class`` is the class used to serialize content before compress, can be overwritten with API `serialize` and `deserialize` retained.

.. code-block:: python

    class CustomIdentityGenerator(IdentityGenerator):
        def generate(self, key, content):
            return key
    
    def cpu_intensive_function(data):
        return data
    
    async def example():
        client = aredis.StrictRedis()
        await client.flushall()
        cache = client.cache('example_cache',
                identity_generator_class=CustomIdentityGenerator)
        data = {1: 1}
        await cache.set('example_key', cpu_intensive_function(data), data)
        res = await cache.get('example_key', data)
        assert res == cpu_intensive_function(data)

For ease of use and expandability, only `set`, `set_many`, `exists`, `delete`, `delete_many`,
`ttl`, `get` APIs are realized.

HerdCache is a solution for `thundering herd problem <https://en.wikipedia.org/wiki/Thundering_herd_problem>`_
It is suitable for scene with low consistency and in which refresh cache costs a lot.
It will save redundant update work when there are multi process read cache from redis and the cache is expired.
If the cache is expired is judged by the expire time saved with each key, and the real expire time of the key
`real_expire_time = the time key is set + expire_time + herd_timeout` once a process find out that the cache is expired,
it will reset the expire time saved in redis with `new_expire_time = the time key is found expired + extend_expire_time`,
and return None(act like cache expired), so that other processes will not noticed the cache expired.