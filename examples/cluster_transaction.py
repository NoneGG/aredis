#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
from coredis import StrictRedisCluster


async def func1(pipe):
    for _ in range(10):
        await pipe.incr('foobar', 1)



async def func2():
    cluster = StrictRedisCluster(startup_nodes=[{'host': '127.0.0.1', 'port': 7001}], decode_responses=True)
    while True:
        foobar = int(await cluster.get('foobar'))
        print('thread: get `foobar` = {}'.format(foobar))
        if foobar >= 0:
            print('thread: cluster get foobar == {}, decrease it'.format(foobar))
            await cluster.decr('foobar', 1)
        if foobar < 0:
            print('thread: break loop now')
            break


async def run_func1():
    cluster = StrictRedisCluster(startup_nodes=[{'host': '127.0.0.1', 'port': 7001}], decode_responses=True)
    print('before transaction: set key `foobar` = 0')
    await cluster.set('foobar', 0)
    try:
        await cluster.transaction(func1, 'foobar', watch_delay=2)
    except Exception as exc:
        print(exc)
    print('after transaction: `foobar` = {}'.format(await cluster.get('foobar')))
    print('wait for thread to end...')
    await asyncio.sleep(1)


if __name__ == '__main__':
    """
    The output should be like below:

    before transaction: set key `foobar` = 0
    thread: get `foobar` = 0
    thread: get `foobar` = 11
    thread: cluster get foobar == 11, try to set it to -1
    after transaction: `foobar` = 11
    wait for thread to end...
    thread: get `foobar` = -1
    thread: break loop now

    Notice the intermediate state of key `foobar` is not printed,
    which means all `incr` commands run in transaction
    """
    loop = asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(func2(), loop)
    loop.run_until_complete(run_func1())
