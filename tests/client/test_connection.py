#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket

import pytest
from coredis import Connection, UnixDomainSocketConnection


@pytest.mark.asyncio(forbid_global_loop=True)
async def test_connect_tcp(event_loop):
    conn = Connection(loop=event_loop)
    assert conn.host == "127.0.0.1"
    assert conn.port == 6379
    assert str(conn) == "Connection<host=127.0.0.1,port=6379,db=0>"
    await conn.send_command("PING")
    res = await conn.read_response()
    assert res == b"PONG"
    assert (conn._reader is not None) and (conn._writer is not None)
    conn.disconnect()
    assert (conn._reader is None) and (conn._writer is None)


@pytest.mark.asyncio(forbid_global_loop=True)
async def test_connect_tcp_keepalive_options(event_loop):
    conn = Connection(
        loop=event_loop,
        socket_keepalive=True,
        socket_keepalive_options={
            socket.TCP_KEEPIDLE: 1,
            socket.TCP_KEEPINTVL: 1,
            socket.TCP_KEEPCNT: 3,
        },
    )
    await conn._connect()
    sock = conn._writer.transport.get_extra_info("socket")
    assert sock.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE) == 1
    for k, v in (
        (socket.TCP_KEEPIDLE, 1),
        (socket.TCP_KEEPINTVL, 1),
        (socket.TCP_KEEPCNT, 3),
    ):
        assert sock.getsockopt(socket.SOL_TCP, k) == v
    conn.disconnect()


@pytest.mark.parametrize("option", ["UNKNOWN", 999])
@pytest.mark.asyncio(forbid_global_loop=True)
async def test_connect_tcp_wrong_socket_opt_raises(event_loop, option):
    conn = Connection(
        loop=event_loop, socket_keepalive=True, socket_keepalive_options={option: 1,},
    )
    with pytest.raises((socket.error, TypeError)):
        await conn._connect()
    # verify that the connection isn't left open
    assert conn._writer.transport.is_closing()


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
