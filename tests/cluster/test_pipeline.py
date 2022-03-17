import pytest

from coredis.exceptions import ResponseError
from tests.conftest import targets


@pytest.mark.asyncio()
@targets("redis_cluster")
class TestPipeline:
    async def test_pipeline(self, client):
        async with await client.pipeline() as pipe:
            await (
                await (await (await pipe.set("a", "a1")).get("a")).zadd("z", dict(z1=1))
            ).zadd("z", dict(z2=4))
            await (await pipe.zincrby("z", "z1", 1)).zrange("z", 0, 5, withscores=True)
            assert await pipe.execute() == (
                True,
                "a1",
                True,
                True,
                2.0,
                (("z1", 2.0), ("z2", 4)),
            )

    async def test_pipeline_length(self, client):
        async with await client.pipeline() as pipe:
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

    async def test_pipeline_no_transaction(self, client):
        async with await client.pipeline(transaction=False) as pipe:
            await (await (await pipe.set("a", "a1")).set("b", "b1")).set("c", "c1")
            assert await pipe.execute() == (
                True,
                True,
                True,
            )
            assert await client.get("a") == "a1"
            assert await client.get("b") == "b1"
            assert await client.get("c") == "c1"

    async def test_pipeline_eval(self, client):
        async with await client.pipeline(transaction=False) as pipe:
            await pipe.eval(
                "return {KEYS[1],KEYS[2],ARGV[1],ARGV[2]}",
                [
                    "A{foo}",
                    "B{foo}",
                ],
                [
                    "first",
                    "second",
                ],
            )
            res = (await pipe.execute())[0]
            assert res[0] == "A{foo}"
            assert res[1] == "B{foo}"
            assert res[2] == "first"
            assert res[3] == "second"

    async def test_exec_error_in_response(self, client):
        """
        an invalid pipeline command at exec time adds the exception instance
        to the list of returned values
        """
        await client.set("c", "a")
        async with await client.pipeline() as pipe:
            await (
                await (await (await pipe.set("a", "1")).set("b", "2")).lpush("c", "3")
            ).set("d", "4")
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
            with pytest.raises(ResponseError) as ex:
                await pipe.execute()
            assert str(ex.value).startswith(
                "Command # 3 (LPUSH c 3) of " "pipeline caused error: "
            )

            # make sure the pipe was restored to a working state
            await pipe.set("z", "zzz")
            assert await pipe.execute() == (True,)
            assert await client.get("z") == "zzz"

    async def test_parse_error_raised(self, client):
        async with await client.pipeline() as pipe:
            # the zrem is invalid because we don't pass any keys to it
            await (await (await pipe.set("a", "1")).zrem("b", [])).set("b", "2")
            with pytest.raises(ResponseError) as ex:
                await pipe.execute()

            assert str(ex.value).startswith(
                "Command # 2 (ZREM b) of pipeline caused error: "
            )

            # make sure the pipe was restored to a working state
            assert await (await pipe.set("z", "zzz")).execute() == (True,)
            assert await client.get("z") == "zzz"
