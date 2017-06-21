from aredis.utils import (NodeFlag,
                          bool_ok,
                          nativestr)


class ConnectionCommandMixin:

    RESPONSE_CALLBACKS = {
        'AUTH': bool,
        'PING': lambda r: nativestr(r) == 'PONG',
        'SELECT': bool_ok,
    }

    async def echo(self, value):
        "Echo the string back from the server"
        return await self.execute_command('ECHO', value)

    async def ping(self):
        "Ping the Redis server"
        return await self.execute_command('PING')


class ClusterConnectionCommandMixin(ConnectionCommandMixin):

    NODES_FLAGS = {
        'PING': NodeFlag.ALL_NODES,
        'ECHO': NodeFlag.ALL_NODES
    }

    RESULT_CALLBACKS = {
        'ECHO': lambda res: res,
        'PING': lambda res: res
    }
