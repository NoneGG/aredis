#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
from aredis import StrictRedis


async def example(client):
    res = None
    async with await client.pipeline(transaction=True) as pipe:
        await client.flushdb()
        await client.set('foo', 'bar')
        await client.set('bar', 'foo')
        res = await client.keys('*')
        print(res)
    # results should be in corresponding
    assert res == [b'bar', b'foo']


if __name__ == '__main__':
    # default to connect to local redis server at port 6379
    client = StrictRedis()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example(client))
