#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
from aredis import StrictRedis


async def example(client):
    # clear the db
    await client.flushdb()
    await client.set('foo', 1)
    assert await client.exists('foo') is True
    await client.incr('foo', 100)
    # will return b'101' (byte type)
    assert int(await client.get('foo')) == 101
    await client.expire('foo', 1)
    await asyncio.sleep(0.1)
    await client.ttl('foo')
    await asyncio.sleep(1)
    assert not await client.exists('foo')


if __name__ == '__main__':
    # initial redis client synchronously, which enable client to be intitialized out of function
    client = StrictRedis(host='127.0.0.1', port=6379, db=0)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example(client))
