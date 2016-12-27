import aredis
import asyncio
import uvloop
import time
import sys
from functools import wraps
from argparse import ArgumentParser

if sys.version_info[0] == 3:
    long = int


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-n',
                        type=int,
                        help='Total number of requests (default 100000)',
                        default=100000)
    parser.add_argument('-P',
                        type=int,
                        help=('Pipeline <numreq> requests.'
                              ' Default 1 (no pipeline).'),
                        default=1)
    parser.add_argument('-s',
                        type=int,
                        help='Data size of SET/GET value in bytes (default 2)',
                        default=2)

    args = parser.parse_args()
    print(args)
    return args


async def run():
    args = parse_args()
    r = aredis.StrictRedis()
    await r.flushall()
    await set_str(conn=r, num=args.n, pipeline_size=args.P, data_size=args.s)
    await set_int(conn=r, num=args.n, pipeline_size=args.P, data_size=args.s)
    await get_str(conn=r, num=args.n, pipeline_size=args.P, data_size=args.s)
    await get_int(conn=r, num=args.n, pipeline_size=args.P, data_size=args.s)
    await incr(conn=r, num=args.n, pipeline_size=args.P, data_size=args.s)
    await lpush(conn=r, num=args.n, pipeline_size=args.P, data_size=args.s)
    await lrange_300(conn=r, num=args.n, pipeline_size=args.P, data_size=args.s)
    await lpop(conn=r, num=args.n, pipeline_size=args.P, data_size=args.s)
    await hmset(conn=r, num=args.n, pipeline_size=args.P, data_size=args.s)


def timer(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.clock()
        ret = await func(*args, **kwargs)
        duration = time.clock() - start
        if 'num' in kwargs:
            count = kwargs['num']
        else:
            count = args[1]
        print('{0} - {1} Requests'.format(func.__name__, count))
        print('Duration  = {}'.format(duration))
        print('Rate = {}'.format(count/duration))
        print('')
        return ret
    return wrapper


@timer
async def set_str(conn, num, pipeline_size, data_size):
    if pipeline_size > 1:
        conn = await conn.pipeline()

    format_str = '{:0<%d}' % data_size
    set_data = format_str.format('a')
    for i in range(num):
        await conn.set('set_str:%d' % i, set_data)
        if pipeline_size > 1 and i % pipeline_size == 0:
            await conn.execute()

    if pipeline_size > 1:
        await conn.execute()
        await conn.reset()


@timer
async def set_int(conn, num, pipeline_size, data_size):
    if pipeline_size > 1:
        conn = await conn.pipeline()

    format_str = '{:0<%d}' % data_size
    set_data = int(format_str.format('1'))
    for i in range(num):
        await conn.set('set_int:%d' % i, set_data)
        if pipeline_size > 1 and i % pipeline_size == 0:
            await conn.execute()

    if pipeline_size > 1:
        await conn.execute()
        await conn.reset()


@timer
async def get_str(conn, num, pipeline_size, data_size):
    if pipeline_size > 1:
        conn = await conn.pipeline()

    for i in range(num):
        await conn.get('set_str:%d' % i)
        if pipeline_size > 1 and i % pipeline_size == 0:
            await conn.execute()

    if pipeline_size > 1:
        await conn.execute()
        await conn.reset()


@timer
async def get_int(conn, num, pipeline_size, data_size):
    if pipeline_size > 1:
        conn = await conn.pipeline()

    for i in range(num):
        await conn.get('set_int:%d' % i)
        if pipeline_size > 1 and i % pipeline_size == 0:
            await conn.execute()

    if pipeline_size > 1:
        await conn.execute()
        await conn.reset()


@timer
async def incr(conn, num, pipeline_size, *args, **kwargs):
    if pipeline_size > 1:
        conn = await conn.pipeline()

    for i in range(num):
        await conn.incr('incr_key')
        if pipeline_size > 1 and i % pipeline_size == 0:
            await conn.execute()

    if pipeline_size > 1:
        await conn.execute()
        await conn.reset()


@timer
async def lpush(conn, num, pipeline_size, data_size):
    if pipeline_size > 1:
        conn = await conn.pipeline()

    format_str = '{:0<%d}' % data_size
    set_data = int(format_str.format('1'))
    for i in range(num):
        await conn.lpush('lpush_key', set_data)
        if pipeline_size > 1 and i % pipeline_size == 0:
            await conn.execute()

    if pipeline_size > 1:
        await conn.execute()
        await conn.reset()


@timer
async def lrange_300(conn, num, pipeline_size, data_size):
    if pipeline_size > 1:
        conn = await conn.pipeline()

    for i in range(num):
        await conn.lrange('lpush_key', i, i+300)
        if pipeline_size > 1 and i % pipeline_size == 0:
            await conn.execute()

    if pipeline_size > 1:
        await conn.execute()
        await conn.reset()


@timer
async def lpop(conn, num, pipeline_size, data_size):
    if pipeline_size > 1:
        conn = await conn.pipeline()
    for i in range(num):
        await conn.lpop('lpush_key')
        if pipeline_size > 1 and i % pipeline_size == 0:
            await conn.execute()
    if pipeline_size > 1:
        await conn.execute()
        await conn.reset()


@timer
async def hmset(conn, num, pipeline_size, data_size):
    if pipeline_size > 1:
        conn = await conn.pipeline()

    set_data = {'str_value': 'string',
                'int_value': 123456,
                'long_value': long(123456),
                'float_value': 123456.0}
    for i in range(num):
        await conn.hmset('hmset_key', set_data)
        if pipeline_size > 1 and i % pipeline_size == 0:
            await conn.execute()

    if pipeline_size > 1:
        await conn.execute()
        await conn.reset()

if __name__ == '__main__':
    print('WITH ASYNCIO ONLY:')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    print('WITH UVLOOP:')
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
