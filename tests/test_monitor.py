import asyncio

import pytest

from tests.conftest import targets


@targets("redis_basic")
@pytest.mark.asyncio()
class TestMonitor:
    async def test_explicit_fetch(self, client):
        monitor = client.monitor()
        response = await asyncio.gather(monitor.get_command(), client.get("test"))
        assert response[0].command == "GET"
        assert response[0].args == ("test",)

    async def test_iterator(self, client):
        async def delayed():
            await asyncio.sleep(0.1)
            return await client.get("test")

        async def collect():
            results = []
            async for command in client.monitor():
                results.append(command)
                break
            return results

        results = await asyncio.gather(delayed(), collect())
        assert results[1][0].command == "GET"
        assert results[1][0].args == ("test",)

    async def test_threaded_listener(self, client):
        results = []

        def handler(command):
            results.append(command)

        monitor = client.monitor()
        thread = monitor.run_in_thread(handler)
        await asyncio.sleep(0.01)
        await client.get("test")
        assert len(results) == 1
        assert results[0].args == ("test",)
        thread.stop()
