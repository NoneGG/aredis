#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest
from aredis import (Connection,
                    UnixDomainSocketConnection)


@pytest.mark.asyncio(forbid_global_loop=True)
async def test_connect_tcp(event_loop):
    conn = Connection(loop=event_loop)
    assert conn.host == '127.0.0.1'
    assert conn.port == 6379
    assert str(conn) == 'Connection<host=127.0.0.1,port=6379,db=0>'
    await conn.send_command('PING')
    res = await conn.read_response()
    assert res == b'PONG'
    assert (conn._reader is not None) and (conn._writer is not None)
    conn.disconnect()
    assert (conn._reader is None) and (conn._writer is None)


# only test during dev
# @pytest.mark.asyncio(forbid_global_loop=True)
# async def test_connect_unix_socket(event_loop):
#     # to run this test case you should change your redis configuration
#     # unixsocket /var/run/redis/redis.sock
#     # unixsocketperm 777
#     path = '/var/run/redis/redis.sock'
#     conn = UnixDomainSocketConnection(path, event_loop)
#     await conn.connect()
#     assert conn.path == path
#     assert str(conn) == 'UnixDomainSocketConnection<path={},db=0>'.format(path)
#     await conn.send_command('PING')
#     res = await conn.read_response()
#     assert res == b'PONG'
#     assert (conn._reader is not None) and (conn._writer is not None)
#     conn.disconnect()
#     assert (conn._reader is None) and (conn._writer is None)
