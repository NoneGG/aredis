#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import asyncio
import asyncio_redis
import aioredis
import redis
import redis.asyncio
import coredis


HOST = '127.0.0.1'
NUM = 10000


async def test_coredis(i):
    start = time.time()
    client = coredis.Redis(host=HOST)
    res = None
    for i in range(i):
        res = await client.keys('*')
    print(time.time() - start)
    return res


async def test_asyncio_redis(i):
    connection = await asyncio_redis.Connection.create(host=HOST, port=6379)
    start = time.time()
    res = None
    for i in range(i):
        res = await connection.keys('*')
    print(time.time() - start)
    connection.close()
    return res


def test_conn(i):
    start = time.time()
    client = redis.Redis(host=HOST)
    res = None
    for i in range(i):
        res = client.keys('*')
    print(time.time() - start)
    return res

async def test_redis_py_asyncio(i, loop):
    start = time.time()
    r = redis.asyncio.Redis()
    val = None
    for i in range(i):
        val = await r.keys('*')
    print(time.time() - start)
    r.close()
    return val

async def test_aioredis(i, loop):
    start = time.time()
    redis = await aioredis.Redis()
    val = None
    for i in range(i):
        val = await redis.keys('*')
    print(time.time() - start)
    redis.close()
    return val


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    print('coredis')
    print(loop.run_until_complete(test_coredis(NUM)))
    print('asyncio_redis')
    print(loop.run_until_complete(test_asyncio_redis(NUM)))
    print('redis-py')
    print(test_conn(NUM))
    print('aioredis')
    print(loop.run_until_complete(test_aioredis(NUM, loop)))
    print('redis-py-asyncio')
    print(loop.run_until_complete(test_redis_py_asyncio(NUM, loop)))

