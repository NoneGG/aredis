import datetime

import pytest

from coredis.utils import b
from tests.conftest import targets


@targets("redis_basic")
@pytest.mark.asyncio()
class TestServer:
    async def slowlog(self, client):
        current_config = await client.config_get()
        old_slower_than_value = current_config["slowlog-log-slower-than"]
        old_max_length_value = current_config["slowlog-max-len"]
        await client.config_set("slowlog-log-slower-than", 0)
        await client.config_set("slowlog-max-len", 128)

        return old_slower_than_value, old_max_length_value

    async def cleanup(self, client, old_slower_than_value, old_max_legnth_value):
        await client.config_set("slowlog-log-slower-than", old_slower_than_value)
        await client.config_set("slowlog-max-len", old_max_legnth_value)

    async def test_config_get(self, client):
        data = await client.config_get()
        assert "maxmemory" in data
        assert data["maxmemory"].isdigit()

    async def test_config_resetstat(self, client):
        await client.ping()
        prior_commands_processed = int(
            (await client.info())["total_commands_processed"]
        )
        assert prior_commands_processed >= 1
        await client.config_resetstat()
        reset_commands_processed = int(
            (await client.info())["total_commands_processed"]
        )
        assert reset_commands_processed < prior_commands_processed

    async def test_config_set(self, client):
        data = await client.config_get()
        rdbname = data["dbfilename"]
        try:
            assert await client.config_set("dbfilename", "redis_py_test.rdb")
            assert (await client.config_get())["dbfilename"] == "redis_py_test.rdb"
        finally:
            assert await client.config_set("dbfilename", rdbname)

    async def test_dbsize(self, client):
        await client.set("a", "foo")
        await client.set("b", "bar")
        assert await client.dbsize() == 2

    async def test_slowlog_get(self, client):
        sl_v, length_v = await self.slowlog(client)
        await client.slowlog_reset()
        unicode_string = "3456abcd3421"
        await client.get(unicode_string)
        slowlog = await client.slowlog_get()
        assert isinstance(slowlog, list)
        commands = [log["command"] for log in slowlog]

        get_command = b(" ").join((b("GET"), unicode_string.encode("utf-8")))
        assert get_command in commands
        assert b("SLOWLOG RESET") in commands
        # the order should be ['GET <uni string>', 'SLOWLOG RESET'],
        # but if other clients are executing commands at the same time, there
        # could be commands, before, between, or after, so just check that
        # the two we care about are in the appropriate ordeclient.
        assert commands.index(get_command) < commands.index(b("SLOWLOG RESET"))

        # make sure other attributes are typed correctly
        assert isinstance(slowlog[0]["start_time"], int)
        assert isinstance(slowlog[0]["duration"], int)
        await self.cleanup(client, sl_v, length_v)

    async def test_slowlog_get_limit(self, client):
        sl_v, length_v = await self.slowlog(client)
        assert await client.slowlog_reset()
        await client.get("foo")
        await client.get("bar")
        slowlog = await client.slowlog_get(1)
        assert isinstance(slowlog, list)
        commands = [log["command"] for log in slowlog]
        assert b("GET foo") not in commands
        assert b("GET bar") in commands
        await self.cleanup(client, sl_v, length_v)

    async def test_slowlog_length(self, client, event_loop):
        sl_v, length_v = await self.slowlog(client)
        await client.get("foo")
        assert isinstance(await client.slowlog_len(), int)
        await self.cleanup(client, sl_v, length_v)

    async def test_time(self, client):
        t = await client.time()
        assert len(t) == 2
        assert isinstance(t[0], int)
        assert isinstance(t[1], int)

    async def test_info(self, client):
        await client.set("a", "foo")
        await client.set("b", "bar")
        info = await client.info()
        assert isinstance(info, dict)
        assert info["db0"]["keys"] == 2

    async def test_lastsave(self, client):
        assert isinstance(await client.lastsave(), datetime.datetime)

    @pytest.mark.min_server_version("6.0.0")
    async def test_lolwut(self, client):
        lolwut = (await client.lolwut(5)).decode("utf-8")
        assert "Redis ver." in lolwut
