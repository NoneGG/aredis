#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import asyncio
import asyncio_redis
import aioredis
from redis.connection import Connection as SConnection
from aredis.connection import Connection

__author__ = 'chenming@bilibili.com'

async def test_aredis(i):
    start = time.time()
    a = Connection(host='172.16.131.222')
    res = None
    for i in range(i):
        await a.send_command('keys', '*')
        res = await a.read_response()
    print(time.time() - start)
    return res


async def test_asyncio_redis(i):
    connection = await asyncio_redis.Connection.create(host='172.16.131.222', port=6379)
    start = time.time()
    res = None
    for i in range(i):
        res = await connection.keys('*')
    print(time.time() - start)
    connection.close()


def test_conn(i):
    start = time.time()
    a = SConnection(host='172.16.131.222')
    res = None
    for i in range(i):
        a.send_command('keys', '*')
        res = a.read_response()
    print(time.time() - start)
    return res


async def test_aioredis(i, loop):
    start = time.time()
    redis = await aioredis.create_redis(
        ('172.16.131.222', 6379), loop=loop)
    val = None
    for i in range(i):
        val = await redis.keys('*')
    print(time.time() - start)
    redis.close()
    await redis.wait_closed()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    print('aredis')
    loop.run_until_complete(test_aredis(100))
    print('asyncio_redis')
    loop.run_until_complete(test_asyncio_redis(100))
    print('redis-py')
    test_conn(100)
    print('aioredis')
    loop.run_until_complete(test_aioredis(100, loop))

