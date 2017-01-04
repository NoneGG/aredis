#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
from aredis import Connection


async def example(conn):
    # connecting process will be done automatically when commands executed
    # you may not need to use that directly
    # directly use it if you want to reconnect a connection instance
    await conn.connect()
    assert await conn.can_read()
    await conn.send_command('keys', '*')
    print(await conn.read_response())
    conn.disconnect()
    await conn.send_command('set', 'foo', 1)
    print(await conn.read_response())

if __name__ == '__main__':
    conn = Connection(host='127.0.0.1', port=6379, db=0)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example(conn))
