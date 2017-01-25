#!/usr/bin/python
# -*- coding: utf-8 -*-

import aredis
import asyncio
import functools


def cached(app, cache):
    def decorator(func):
        @functools.wraps(func)
        async def _inner(*args, **kwargs):
            key = func.__name__
            res = await cache.get(key, (args, kwargs))
            if res:
                print('using cache: {}'.format(res))
            else:
                print('cache miss')
                res = func(*args, **kwargs)
                await cache.set(key, res, (args, kwargs))
            return res
        return _inner
    return decorator


cache = aredis.StrictRedis().cache('example_cache')


@cached(app='example', cache=cache)
def job(*args, **kwargs):
    return 'example_results'


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(job(111))


