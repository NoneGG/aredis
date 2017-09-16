#!/usr/bin/python
# -*- coding: utf-8 -*-

import aredis
import asyncio
import concurrent.futures
import time
import logging


async def wait_for_message(pubsub, timeout=2, ignore_subscribe_messages=False):
    now = time.time()
    timeout = now + timeout
    while now < timeout:
        message = await pubsub.get_message(
            ignore_subscribe_messages=ignore_subscribe_messages,
            timeout=1
        )
        if message is not None:
            print(message)
        await asyncio.sleep(0.01)
        now = time.time()
    return None


async def subscribe(client):
    await client.flushdb()
    pubsub = client.pubsub()
    assert pubsub.subscribed is False
    await pubsub.subscribe('foo')
    # assert await pubsub.subscribe() is True
    await wait_for_message(pubsub)


async def publish(client):
    # sleep to wait for subscriber to listen
    await asyncio.sleep(1)
    await client.publish('foo', 'test message')
    await client.publish('foo', 'quit')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    client = aredis.StrictRedis()
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(asyncio.run_coroutine_threadsafe, publish(client), loop)
    loop.run_until_complete(subscribe(client))
