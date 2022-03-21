"""
`client reply off | on | skip` is hard to be supported by coredis gracefully because of the client pool usage.
The client is supposed to read response from server and release connection after the command being sent.
But the connection is needed to be always reused if you need to turn on | off | skip the reply,
it should always be the connection by which you send `client reply` command to server you use to send the rest commands.

However, you can use the connection by your self like the example below~
"""

from coredis import Connection
import asyncio


async def skip():
    print("skip response example::")
    conn = Connection(host="127.0.0.1", port=6379)
    await conn.send_command("flushdb")
    print(await conn.read_response())
    await conn.send_command("CLIENT REPLY", "SKIP")
    await conn.send_command("SET", "lalala", 1)
    await conn.send_command("SET", "lalala", 2)
    print(await conn.read_response())


async def off_and_on():
    print("turn off response and then turn it ")
    conn = Connection()
    await conn.send_command("flushdb")
    print(await conn.read_response())
    await conn.send_command("CLIENT REPLY", "OFF")
    await conn.send_command("SET", "lalala", 10)
    await conn.send_command("CLIENT REPLY", "ON")
    print(await conn.read_response())
    await conn.send_command("GET", "lalala")
    print(await conn.read_response())


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(skip())
    loop.run_until_complete(off_and_on())
