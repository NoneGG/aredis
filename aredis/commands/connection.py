from aredis.utils import bool_ok


class ConnectionCommandMixin:

    RESPONSE_CALLBACKS = {
        'AUTH': bool,
        'PING': lambda r: r == b'PONG',
        'SELECT': bool_ok,
    }

    async def echo(self, value):
        "Echo the string back from the server"
        return await self.execute_command('ECHO', value)

    async def ping(self):
        "Ping the Redis server"
        return await self.execute_command('PING')
