#!/usr/bin/python
# -*- coding: utf-8 -*-

import coredis
import asyncio


async def example():
    client = coredis.Redis()
    await client.flushdb()
    await client.mset({"a": 1, "b": 2, "c": 3})
    # pay attention that async_generator don't need to be awaited
    keys = client.scan_iter()
    # use `async for` instead of `for` only
    collected = set()
    async for key in keys:
        collected.add(key)
    assert collected == set([b"c", b"b", b"a"]), collected

    await client.hmset("d", {"a": 1, "b": 2, "c": 3})
    hash_keys = [k async for k in client.scan_iter(type_="HASH")]
    assert hash_keys == [b"d"]


async def cluster_example():
    client = coredis.RedisCluster("localhost", 7000)
    await client.flushdb()
    await client.mset({"a": 1, "b": 2, "c": 3})
    # pay attention that async_generator don't need to be awaited
    keys = client.scan_iter()
    # use `async for` instead of `for` only
    collected = set()
    async for key in keys:
        collected.add(key)
    assert collected == set([b"c", b"b", b"a"]), collected

    await client.hmset("d", {"a": 1, "b": 2, "c": 3})
    hash_keys = [k async for k in client.scan_iter(type_="HASH")]
    assert hash_keys == [b"d"]


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    # loop.run_until_complete(example())
    loop.run_until_complete(cluster_example())
