#!/usr/bin/python
# -*- coding: utf-8 -*-

import coredis
import asyncio
import logging


def my_handler(x):
    print(x)


async def use_pubsub_in_thread():
    client = coredis.Redis()
    pubsub = client.pubsub()
    await pubsub.subscribe(**{"my-channel": my_handler})
    thread = pubsub.run_in_thread()
    for _ in range(10):
        await client.publish("my-channel", "lalala")
    thread.stop()
    await asyncio.sleep(0.1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.new_event_loop()
    loop.set_debug(enabled=True)
    loop.run_until_complete(use_pubsub_in_thread())
