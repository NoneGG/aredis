#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import curio
import asyncio
import asyncio_redis
from redis.connection import Connection as SConnection
from aredis.connection import Connection

__author__ = 'chenming@bilibili.com'

async def test_async_conn(i):
    start = time.time()
    kernel = curio.Kernel()
    a = Connection(host='172.16.131.222', kernel=kernel)
    res = None
    for i in range(i):
        await a.send_command('keys', '*')
        res = await a.read_response()
    print(time.time() - start)
    return res


async def test_asyncio_redis(i):
    connection = await asyncio_redis.Connection.create(host='172.16.131.222', port=6379)
    start = time.time()
    for i in range(i):
        await connection.keys('*')
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


if __name__ == '__main__':
    kernel = curio.Kernel()
    kernel.run(test_async_conn(100))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_asyncio_redis(100))
    test_conn(100)
