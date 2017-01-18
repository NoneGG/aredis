#!/usr/bin/python
# -*- coding: utf-8 -*-

import aredis
import asyncio
from aredis.cache import IdentityGenerator


class CustomIdentityGenerator(IdentityGenerator):

    def generate(self, key, content):
        return key


def expensive_work(data):
    """some work that waits for io or occupy cpu"""
    return data


async def example():
    client = aredis.StrictRedis()
    await client.flushall()
    cache = client.cache('example_cache',
                         identity_generator_class=CustomIdentityGenerator)
    data = {1: 1}
    await cache.set('example_key', expensive_work(data), data)
    res = await cache.get('example_key', data)
    assert res == expensive_work(data)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
