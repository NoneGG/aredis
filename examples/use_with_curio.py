import curio

import coredis


async def aio_child():
    redis = coredis.StrictRedis(host='127.0.0.1', port=6379, db=0)
    await redis.flushdb()
    await redis.set('bar', 'foo')
    bar = await redis.get('bar')
    return bar


async def wrapper():
    async with curio.bridge.AsyncioLoop() as loop:
        return await loop.run_asyncio(aio_child)


if __name__ == '__main__':
    print(curio.run(wrapper))