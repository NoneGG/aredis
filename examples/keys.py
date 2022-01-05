#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
from coredis import StrictRedis, StrictRedisCluster


async def example_client():
    client = StrictRedis(host='127.0.0.1', port=6379, db=0)
    # clear the db
    await client.flushdb()
    await client.set('foo', 1)
    print(await client.get('foo'))
    assert await client.exists('foo') is True
    await client.incr('foo', 100)
    # will return b'101' (byte type)
    assert int(await client.get('foo')) == 101
    await client.expire('foo', 1)
    await asyncio.sleep(0.1)
    await client.ttl('foo')
    await asyncio.sleep(1)
    assert not await client.exists('foo')


async def example_cluster():
    client = StrictRedisCluster(host='127.0.0.1', port=7001)
    await client.flushdb()
    await client.set('foo', 1)
    await client.lpush('a', 1)
    print(await client.cluster_slots())
    # 'a' and 'b' are in different slots
    await client.rpoplpush('a', 'b')
    assert await client.rpop('b') == b'1'


if __name__ == '__main__':
    # initial redis client synchronously, which enable client to be intitialized out of function
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example_client())
    # loop.run_until_complete(example_cluster())
