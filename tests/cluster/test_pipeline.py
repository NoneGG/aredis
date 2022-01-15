# -*- coding: utf-8 -*-

# python std lib
from __future__ import with_statement

# 3rd party imports
import pytest

# rediscluster imports
from coredis.exceptions import ResponseError, WatchError
from coredis.utils import b


class TestPipeline:
    """ """

    @pytest.mark.asyncio()
    async def test_pipeline(self, r):
        async with await r.pipeline() as pipe:
            await (
                await (await (await pipe.set("a", "a1")).get("a")).zadd("z", z1=1)
            ).zadd("z", z2=4)
            await (await pipe.zincrby("z", "z1")).zrange("z", 0, 5, withscores=True)
            assert await pipe.execute() == [
                True,
                b("a1"),
                True,
                True,
                2.0,
                [(b("z1"), 2.0), (b("z2"), 4)],
            ]

    @pytest.mark.asyncio()
    async def test_pipeline_length(self, r):
        async with await r.pipeline() as pipe:
            # Initially empty.
            assert len(pipe) == 0
            assert not pipe

            # Fill 'er up!
            await (await (await pipe.set("a", "a1")).set("b", "b1")).set("c", "c1")
            assert len(pipe) == 3
            assert pipe

            # Execute calls reset(), so empty once again.
            await pipe.execute()
            assert len(pipe) == 0
            assert not pipe

    @pytest.mark.asyncio()
    async def test_pipeline_no_transaction(self, r):
        async with await r.pipeline(transaction=False) as pipe:
            await (await (await pipe.set("a", "a1")).set("b", "b1")).set("c", "c1")
            assert await pipe.execute() == [True, True, True]
            assert await r.get("a") == b("a1")
            assert await r.get("b") == b("b1")
            assert await r.get("c") == b("c1")

    @pytest.mark.asyncio()
    async def test_pipeline_eval(self, r):
        async with await r.pipeline(transaction=False) as pipe:
            await pipe.eval(
                "return {KEYS[1],KEYS[2],ARGV[1],ARGV[2]}",
                2,
                "A{foo}",
                "B{foo}",
                "first",
                "second",
            )
            res = (await pipe.execute())[0]
            assert res[0] == b("A{foo}")
            assert res[1] == b("B{foo}")
            assert res[2] == b("first")
            assert res[3] == b("second")

    @pytest.mark.asyncio()
    @pytest.mark.xfail(reason="unsupported command: watch")
    async def test_pipeline_no_transaction_watch(self, r):
        await r.set("a", 0)

        async with await r.pipeline(transaction=False) as pipe:
            await pipe.watch("a")
            a = await pipe.get("a")

            await pipe.multi()
            await pipe.set("a", int(a) + 1)
            assert await pipe.execute() == [True]

    @pytest.mark.asyncio()
    @pytest.mark.xfail(reason="unsupported command: watch")
    async def test_pipeline_no_transaction_watch_failure(self, r):
        await r.set("a", 0)

        async with await r.pipeline(transaction=False) as pipe:
            await pipe.watch("a")
            a = await pipe.get("a")

            await r.set("a", "bad")

            await pipe.multi()
            await pipe.set("a", int(a) + 1)

            with pytest.raises(WatchError):
                await pipe.execute()

            assert await r.get("a") == b("bad")

    @pytest.mark.asyncio()
    async def test_exec_error_in_response(self, r):
        """
        an invalid pipeline command at exec time adds the exception instance
        to the list of returned values
        """
        await r.set("c", "a")
        async with await r.pipeline() as pipe:
            await (
                await (await (await pipe.set("a", 1)).set("b", 2)).lpush("c", 3)
            ).set("d", 4)
            result = await pipe.execute(raise_on_error=False)

            assert result[0]
            assert await r.get("a") == b("1")
            assert result[1]
            assert await r.get("b") == b("2")

            # we can't lpush to a key that's a string value, so this should
            # be a ResponseError exception
            assert isinstance(result[2], ResponseError)
            assert await r.get("c") == b("a")

            # since this isn't a transaction, the other commands after the
            # error are still executed
            assert result[3]
            assert await r.get("d") == b("4")

            # make sure the pipe was restored to a working state
            await pipe.set("z", "zzz")
            assert await pipe.execute() == [True]
            assert await r.get("z") == b("zzz")

    @pytest.mark.asyncio()
    async def test_exec_error_raised(self, r):
        await r.set("c", "a")
        async with await r.pipeline() as pipe:
            await pipe.set("a", 1)
            await pipe.set("b", 2)
            await pipe.lpush("c", 3)
            await pipe.set("d", 4)
            with pytest.raises(ResponseError) as ex:
                await pipe.execute()
            assert str(ex.value).startswith(
                "Command # 3 (LPUSH c 3) of " "pipeline caused error: "
            )

            # make sure the pipe was restored to a working state
            await pipe.set("z", "zzz")
            assert await pipe.execute() == [True]
            assert await r.get("z") == b("zzz")

    @pytest.mark.asyncio()
    async def test_parse_error_raised(self, r):
        async with await r.pipeline() as pipe:
            # the zrem is invalid because we don't pass any keys to it
            await (await (await pipe.set("a", 1)).zrem("b")).set("b", 2)
            with pytest.raises(ResponseError) as ex:
                await pipe.execute()

            assert str(ex.value).startswith(
                "Command # 2 (ZREM b) of pipeline caused error: "
            )

            # make sure the pipe was restored to a working state
            assert await (await pipe.set("z", "zzz")).execute() == [True]
            assert await r.get("z") == b("zzz")

    @pytest.mark.asyncio()
    @pytest.mark.xfail(reason="unsupported command: watch")
    async def test_watch_succeed(self, r):
        await r.set("a", 1)
        await r.set("b", 2)

        async with await r.pipeline() as pipe:
            await pipe.watch("a", "b")
            assert pipe.watching
            a_value = await pipe.get("a")
            b_value = await pipe.get("b")
            assert a_value == b("1")
            assert b_value == b("2")
            await pipe.multi()

            await pipe.set("c", 3)
            assert await pipe.execute() == [True]
            assert not pipe.watching

    @pytest.mark.asyncio()
    @pytest.mark.xfail(reason="unsupported command: watch")
    async def test_watch_failure(self, r):
        await r.set("a", 1)
        await r.set("b", 2)

        async with await r.pipeline() as pipe:
            await pipe.watch("a", "b")
            r["b"] = 3
            await pipe.multi()
            await pipe.get("a")
            with pytest.raises(WatchError):
                await pipe.execute()

            assert not pipe.watching

    @pytest.mark.asyncio()
    @pytest.mark.xfail(reason="unsupported command: watch")
    async def test_unwatch(self, r):
        await r.set("a", 1)
        await r.set("b", 2)

        async with await r.pipeline() as pipe:
            await pipe.watch("a", "b")
            r["b"] = 3
            await pipe.unwatch()
            assert not pipe.watching
            await pipe.get("a")
            assert await pipe.execute() == [b("1")]

    @pytest.mark.asyncio()
    @pytest.mark.xfail(reason="unsupported command: watch")
    async def test_transaction_callable(self, r):
        await r.set("a", 1)
        await r.set("b", 2)
        has_run = []

        async def my_transaction(pipe):
            a_value = pipe.get("a")
            assert a_value in (b("1"), b("2"))
            b_value = pipe.get("b")
            assert b_value == b("2")

            # silly run-once code... incr's "a" so WatchError should be raised
            # forcing this all to run again. this should incr "a" once to "2"

            if not has_run:
                await r.incr("a")
                has_run.append("it has")

            await pipe.multi()
            await pipe.set("c", int(a_value) + int(b_value))

        result = await r.transaction(my_transaction, "a", "b")
        assert result == [True]
        assert await r.get("c") == b("4")
