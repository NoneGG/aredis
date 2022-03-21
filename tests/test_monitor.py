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
        response = await asyncio.gather(monitor.get_command(), client.get("test2"))
        assert response[0].command == "GET"
        assert response[0].args == ("test2",)

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

    async def test_threaded_listener(self, client, mocker):
        monitor = client.monitor()
        thread = monitor.run_in_thread(lambda cmd: None)
        await asyncio.sleep(0.01)
        send_command = mocker.spy(monitor.connection, "send_command")
        thread.stop()
        await asyncio.sleep(0.01)
        send_command.assert_called_with("RESET")
