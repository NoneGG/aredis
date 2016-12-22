#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import asyncio
import asyncio_redis
import aioredis
from redis.connection import Connection as SConnection
from aredis.connection import Connection

__author__ = 'chenming@bilibili.com'


HOST = '172.16.131.254'


async def test_aredis(i):
    start = time.time()
    a = Connection(host=HOST)
    res = None
    for i in range(i):
        await a.send_command('keys', '*')
        res = await a.read_response()
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


def test_conn(i):
    start = time.time()
    a = SConnection(host=HOST)
    res = None
    for i in range(i):
        a.send_command('keys', '*')
        res = a.read_response()
    print(time.time() - start)
    return res


async def test_aioredis(i, loop):
    start = time.time()
    redis = await aioredis.create_redis((HOST, 6379), loop=loop)
    val = None
    for i in range(i):
        val = await redis.keys('*')
    print(time.time() - start)
    redis.close()
    await redis.wait_closed()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    print('aredis')
    loop.run_until_complete(test_aredis(1000))
    # print('asyncio_redis')
    # loop.run_until_complete(test_asyncio_redis(1000))
    # print('redis-py')
    # assert res == test_conn(1000)
    # print('aioredis')
    # loop.run_until_complete(test_aioredis(1000, loop))

