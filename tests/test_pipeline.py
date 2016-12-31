from __future__ import with_statement
import pytest

from aredis.utils import b
from aredis.exceptions import (WatchError,
                               ResponseError)


class TestPipeline(object):

    @pytest.mark.asyncio
    async def test_pipeline(self, r):
        await r.flushdb()
        async with await r.pipeline() as pipe:
            await pipe.set('a', 'a1')
            await pipe.get('a')
            await pipe.zadd('z', z1=1)
            await pipe.zadd('z', z2=4)
            await pipe.zincrby('z', 'z1')
            await pipe.zrange('z', 0, 5, withscores=True)
            assert await pipe.execute() == \
                [
                    True,
                    b('a1'),
                    1,
                    1,
                    2.0,
                    [(b('z1'), 2.0), (b('z2'), 4)],
                ]

    @pytest.mark.asyncio
    async def test_pipeline_length(self, r):
        await r.flushdb()
        async with await r.pipeline() as pipe:
            # Initially empty.
            assert len(pipe) == 0
            assert not pipe

            # Fill 'er up!
            await pipe.set('a', 'a1')
            await pipe.set('b', 'b1')
            await pipe.set('c', 'c1')
            assert len(pipe) == 3
            assert pipe

            # Execute calls reset(), so empty once again.
            await pipe.execute()
            assert len(pipe) == 0
            assert not pipe

    @pytest.mark.asyncio
    async def test_pipeline_no_transaction(self, r):
        await r.flushdb()
        async with await r.pipeline(transaction=False) as pipe:
            await pipe.set('a', 'a1')
            await pipe.set('b', 'b1')
            await pipe.set('c', 'c1')
            assert await pipe.execute() == [True, True, True]
            assert await r.get('a') == b('a1')
            assert await r.get('b') == b('b1')
            assert await r.get('c') == b('c1')

    @pytest.mark.asyncio
    async def test_pipeline_no_transaction_watch(self, r):
        await r.flushdb()
        await r.set('a', 0)

        async with await r.pipeline(transaction=False) as pipe:
            await pipe.watch('a')
            a = await pipe.get('a')

            pipe.multi()
            await pipe.set('a', int(a) + 1)
            assert await pipe.execute() == [True]

    @pytest.mark.asyncio
    async def test_pipeline_no_transaction_watch_failure(self, r):
        await r.flushdb()
        await r.set('a', 0)

        async with await r.pipeline(transaction=False) as pipe:
            await pipe.watch('a')
            a = await pipe.get('a')

            await r.set('a', 'bad')

            pipe.multi()
            await pipe.set('a', int(a) + 1)

            with pytest.raises(WatchError):
                await pipe.execute()

            assert await r.get('a') == b('bad')

    @pytest.mark.asyncio
    async def test_exec_error_in_response(self, r):
        """
        an invalid pipeline command at exec time adds the exception instance
        to the list of returned values
        """
        await r.flushdb()
        await r.set('c', 'a')
        async with await r.pipeline() as pipe:
            await pipe.set('a', 1)
            await pipe.set('b', 2)
            await pipe.lpush('c', 3)
            await pipe.set('d', 4)
            result = await pipe.execute(raise_on_error=False)

            assert result[0]
            assert await r.get('a') == b('1')
            assert result[1]
            assert await r.get('b') == b('2')

            # we can't lpush to a key that's a string value, so this should
            # be a ResponseError exception
            assert isinstance(result[2], ResponseError)
            assert await r.get('c') == b('a')

            # since this isn't a transaction, the other commands after the
            # error are still executed
            assert result[3]
            assert await r.get('d') == b('4')

            # make sure the pipe was restored to a working state
            await pipe.set('z', 'zzz')
            assert await pipe.execute() == [True]
            assert await r.get('z') == b('zzz')

    @pytest.mark.asyncio
    async def test_exec_error_raised(self, r):
        await r.flushdb()
        await r.set('c', 'a')
        async with await r.pipeline() as pipe:
            await pipe.set('a', 1)
            await pipe.set('b', 2)
            await pipe.lpush('c', 3)
            await pipe.set('d', 4)
            with pytest.raises(ResponseError) as ex:
                await pipe.execute()

            # make sure the pipe was restored to a working state
            await pipe.set('z', 'zzz')
            assert await pipe.execute() == [True]
            assert await r.get('z') == b('zzz')

    @pytest.mark.asyncio
    async def test_parse_error_raised(self, r):
        await r.flushdb()
        async with await r.pipeline() as pipe:
            # the zrem is invalid because we don't pass any keys to it
            await pipe.set('a', 1)
            await pipe.zrem('b')
            await pipe.set('b', 2)
            with pytest.raises(ResponseError) as ex:
                await pipe.execute()

            # make sure the pipe was restored to a working state
            await pipe.set('z', 'zzz')
            assert await pipe.execute() == [True]
            assert await r.get('z') == b('zzz')

    @pytest.mark.asyncio
    async def test_watch_succeed(self, r):
        await r.flushdb()
        await r.set('a', 1)
        await r.set('b', 2)

        async with await r.pipeline() as pipe:
            await pipe.watch('a', 'b')
            assert pipe.watching
            a_value = await pipe.get('a')
            b_value = await pipe.get('b')
            assert a_value == b('1')
            assert b_value == b('2')
            pipe.multi()

            await pipe.set('c', 3)
            assert await pipe.execute() == [True]
            assert not pipe.watching

    @pytest.mark.asyncio
    async def test_watch_failure(self, r):
        await r.flushdb()
        await r.set('a', 1)
        await r.set('b', 2)

        async with await r.pipeline() as pipe:
            await pipe.watch('a', 'b')
            await r.set('b', 3)
            pipe.multi()
            await pipe.get('a')
            with pytest.raises(WatchError):
                await pipe.execute()

            assert not pipe.watching

    @pytest.mark.asyncio
    async def test_unwatch(self, r):
        await r.flushdb()
        await r.set('a', 1)
        await r.set('b', 2)

        async with await r.pipeline() as pipe:
            await pipe.watch('a', 'b')
            await r.set('b', 3)
            await pipe.unwatch()
            assert not pipe.watching
            await pipe.get('a')
            assert await pipe.execute() == [b('1')]

    @pytest.mark.asyncio
    async def test_transaction_callable(self, r):
        await r.flushdb()
        await r.set('a', 1)
        await r.set('b', 2)
        has_run = []

        async def my_transaction(pipe):
            a_value = await pipe.get('a')
            assert a_value in (b('1'), b('2'))
            b_value = await pipe.get('b')
            assert b_value == b('2')

            # silly run-once code... incr's "a" so WatchError should be raised
            # forcing this all to run again. this should incr "a" once to "2"
            if not has_run:
                await r.incr('a')
                has_run.append('it has')

            pipe.multi()
            await pipe.set('c', int(a_value) + int(b_value))

        result = await r.transaction(my_transaction, 'a', 'b')
        assert result == [True]
        assert await r.get('c') == b('4')

    @pytest.mark.asyncio
    async def test_exec_error_in_no_transaction_pipeline(self, r):
        await r.flushdb()
        await r.set('a', 1)
        async with await r.pipeline(transaction=False) as pipe:
            await pipe.llen('a')
            await pipe.expire('a', 100)

            with pytest.raises(ResponseError) as ex:
                await pipe.execute()

        assert await r.get('a') == b('1')

    @pytest.mark.asyncio
    async def test_exec_error_in_no_transaction_pipeline_unicode_command(self, r):
        key = chr(11) + 'abcd' + chr(23)
        await r.set(key, 1)
        async with await r.pipeline(transaction=False) as pipe:
            await pipe.llen(key)
            await pipe.expire(key, 100)

            with pytest.raises(ResponseError) as ex:
                await pipe.execute()

        assert await r.get(key) == b('1')
