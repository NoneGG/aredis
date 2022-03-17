import pytest

from coredis.exceptions import ResponseError, WatchError
from tests.conftest import targets


@pytest.mark.asyncio()
@targets("redis_basic")
class TestPipeline:
    async def test_pipeline(self, client):
        async with await client.pipeline() as pipe:
            await pipe.set("a", "a1")
            await pipe.get("a")
            await pipe.zadd("z", dict(z1=1))
            await pipe.zadd("z", dict(z2=4))
            await pipe.zincrby("z", "z1", 1)
            await pipe.zrange("z", 0, 5, withscores=True)
            assert await pipe.execute() == (
                True,
                "a1",
                1,
                1,
                2.0,
                (("z1", 2.0), ("z2", 4)),
            )

    async def test_pipeline_length(self, client):
        async with await client.pipeline() as pipe:
            # Initially empty.
            assert len(pipe) == 0
            assert not pipe

            # Fill 'er up!
            await pipe.set("a", "a1")
            await pipe.set("b", "b1")
            await pipe.set("c", "c1")
            assert len(pipe) == 3
            assert pipe

            # Execute calls reset(), so empty once again.
            await pipe.execute()
            assert len(pipe) == 0
            assert not pipe

    async def test_pipeline_no_transaction(self, client):
        async with await client.pipeline(transaction=False) as pipe:
            await pipe.set("a", "a1")
            await pipe.set("b", "b1")
            await pipe.set("c", "c1")
            assert await pipe.execute() == (True, True, True)
            assert await client.get("a") == "a1"
            assert await client.get("b") == "b1"
            assert await client.get("c") == "c1"

    async def test_pipeline_no_transaction_watch(self, client):
        await client.set("a", "0")

        async with await client.pipeline(transaction=False) as pipe:
            await pipe.watch("a")
            a = await pipe.get("a")

            pipe.multi()
            await pipe.set("a", str(int(a) + 1))
            assert await pipe.execute() == (True,)

    async def test_pipeline_no_transaction_watch_failure(self, client):
        await client.set("a", "0")

        async with await client.pipeline(transaction=False) as pipe:
            await pipe.watch("a")
            a = await pipe.get("a")

            await client.set("a", "bad")

            pipe.multi()
            await pipe.set("a", str(int(a) + 1))

            with pytest.raises(WatchError):
                await pipe.execute()

            assert await client.get("a") == "bad"

    async def test_exec_error_in_response(self, client):
        """
        an invalid pipeline command at exec time adds the exception instance
        to the list of returned values
        """
        await client.set("c", "a")
        async with await client.pipeline() as pipe:
            await pipe.set("a", "1")
            await pipe.set("b", "2")
            await pipe.lpush("c", "3")
            await pipe.set("d", "4")
            result = await pipe.execute(raise_on_error=False)

            assert result[0]
            assert await client.get("a") == "1"
            assert result[1]
            assert await client.get("b") == "2"

            # we can't lpush to a key that's a string value, so this should
            # be a ResponseError exception
            assert isinstance(result[2], ResponseError)
            assert await client.get("c") == "a"

            # since this isn't a transaction, the other commands after the
            # error are still executed
            assert result[3]
            assert await client.get("d") == "4"

            # make sure the pipe was restored to a working state
            await pipe.set("z", "zzz")
            assert await pipe.execute() == (True,)
            assert await client.get("z") == "zzz"

    async def test_exec_error_raised(self, client):
        await client.set("c", "a")
        async with await client.pipeline() as pipe:
            await pipe.set("a", "1")
            await pipe.set("b", "2")
            await pipe.lpush("c", "3")
            await pipe.set("d", "4")
            with pytest.raises(ResponseError):
                await pipe.execute()

            # make sure the pipe was restored to a working state
            await pipe.set("z", "zzz")
            assert await pipe.execute() == (True,)
            assert await client.get("z") == "zzz"

    async def test_parse_error_raised(self, client):
        async with await client.pipeline() as pipe:
            # the zrem is invalid because we don't pass any keys to it
            await pipe.set("a", "1")
            await pipe.zrem("b", [])
            await pipe.set("b", "2")
            with pytest.raises(ResponseError):
                await pipe.execute()

            # make sure the pipe was restored to a working state
            await pipe.set("z", "zzz")
            assert await pipe.execute() == (True,)
            assert await client.get("z") == "zzz"

    async def test_watch_succeed(self, client):
        await client.set("a", "1")
        await client.set("b", "2")

        async with await client.pipeline() as pipe:
            await pipe.watch("a", "b")
            assert pipe.watching
            a_value = await pipe.get("a")
            b_value = await pipe.get("b")
            assert a_value == "1"
            assert b_value == "2"
            pipe.multi()

            await pipe.set("c", "3")
            assert await pipe.execute() == (True,)
            assert not pipe.watching

    async def test_watch_failure(self, client):
        await client.set("a", "1")
        await client.set("b", "2")

        async with await client.pipeline() as pipe:
            await pipe.watch("a", "b")
            await client.set("b", "3")
            pipe.multi()
            await pipe.get("a")
            with pytest.raises(WatchError):
                await pipe.execute()

            assert not pipe.watching

    async def test_unwatch(self, client):
        await client.set("a", "1")
        await client.set("b", "2")

        async with await client.pipeline() as pipe:
            await pipe.watch("a", "b")
            await client.set("b", "3")
            await pipe.unwatch()
            assert not pipe.watching
            await pipe.get("a")
            assert await pipe.execute() == ("1",)

    async def test_transaction_callable(self, client):
        await client.set("a", "1")
        await client.set("b", "2")
        has_run = []

        async def my_transaction(pipe):
            a_value = await pipe.get("a")
            assert a_value in ("1", "2")
            b_value = await pipe.get("b")
            assert b_value == "2"

            # silly run-once code... incr's "a" so WatchError should be raised
            # forcing this all to run again. this should incr "a" once to "2"

            if not has_run:
                await client.incr("a")
                has_run.append("it has")

            pipe.multi()
            await pipe.set("c", str(int(a_value) + int(b_value)))

        result = await client.transaction(my_transaction, "a", "b", watch_delay=0.01)
        assert result == (True,)
        assert await client.get("c") == "4"

    async def test_exec_error_in_no_transaction_pipeline(self, client):
        await client.set("a", "1")
        async with await client.pipeline(transaction=False) as pipe:
            await pipe.llen("a")
            await pipe.expire("a", 100)

            with pytest.raises(ResponseError):
                await pipe.execute()

        assert await client.get("a") == "1"

    async def test_exec_error_in_no_transaction_pipeline_unicode_command(self, client):
        key = chr(11) + "abcd" + chr(23)
        await client.set(key, "1")
        async with await client.pipeline(transaction=False) as pipe:
            await pipe.llen(key)
            await pipe.expire(key, 100)

            with pytest.raises(ResponseError):
                await pipe.execute()

        assert await client.get(key) == "1"
