#!/usr/bin/python
# -*- coding: utf-8 -*-

import aredis
import asyncio


def my_handler(x):
    print(x)


async def use_pubsub_in_thread():
    client = aredis.StrictRedis()
    pubsub = client.pubsub()
    await pubsub.subscribe(**{'my-channel': my_handler})
    pubsub.run_in_thread(daemon=True)
    for _ in range(10):
        await client.publish('my-channel', 'lalala')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(use_pubsub_in_thread())
