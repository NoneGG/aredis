#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
from aredis import StrictRedis


async def example_bitfield():
    redis = StrictRedis(host='127.0.0.1')
    await redis.flushdb()
    bitfield = redis.bitfield('example')
    res = await (bitfield.set('i8', '#1', 100).get('i8', '#1')).exc()
    assert res == [0, 100]
    print(res)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example_bitfield())
