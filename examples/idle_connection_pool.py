#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
import time
from coredis import StrictRedis


async def example():
    rs = StrictRedis(host='127.0.0.1', port=6379, db=0, max_idle_time=2, idle_check_interval=0.1)
    print(await rs.info())
    print(rs.connection_pool._available_connections)
    print(rs.connection_pool._in_use_connections)
    conn = rs.connection_pool._available_connections[0]
    print(conn.last_active_at)
    await asyncio.sleep(5)
    print(conn.last_active_at)
    print(time.time() - conn.last_active_at)
    # we can see that the idle connection is removed from available conn list
    print(rs.connection_pool._available_connections)
    print(rs.connection_pool._in_use_connections)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
