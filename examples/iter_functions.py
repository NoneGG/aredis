#!/usr/bin/python
# -*- coding: utf-8 -*-

import aredis
import asyncio


async def example():
    client = aredis.StrictRedis()
    # pay attention that async_generator don't need to be awaited
    keys = client.scan_iter()
    # use `async for` instead of `for` only
    async for key in keys:
        print(key)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
