import asyncio
import datetime
from aredis.exceptions import RedisError
from aredis.utils import (b, bool_ok,
                          dict_merge,
                          string_keys_to_dict,
                          pairs_to_dict)


def parse_slowlog_get(response, **options):
    return [{
        'id': item[0],
        'start_time': int(item[1]),
        'duration': int(item[2]),
        'command': b(' ').join(item[3])
    } for item in response]


def parse_client_list(response, **options):
    clients = []
    for c in response.decode().splitlines():
        clients.append(dict([pair.split('=') for pair in c.split(' ')]))
    return clients


def parse_config_get(response, **options):
    response = [i.decode() if i is not None else None for i in response]
    return response and pairs_to_dict(response) or {}


def timestamp_to_datetime(response):
    "Converts a unix timestamp to a Python datetime object"
    if not response:
        return None
    try:
        response = int(response)
    except ValueError:
        return None
    return datetime.datetime.fromtimestamp(response)


def parse_debug_object(response):
    "Parse the results of Redis's DEBUG OBJECT command into a Python dict"
    # The 'type' of the object is the first item in the response, but isn't
    # prefixed with a name
    response = response.decode()
    response = 'type:' + response
    response = dict([kv.split(':') for kv in response.split()])

    # parse some expected int values from the string response
    # note: this cmd isn't spec'd so these may not appear in all redis versions
    int_fields = ('refcount', 'serializedlength', 'lru', 'lru_seconds_idle')
    for field in int_fields:
        if field in response:
            response[field] = int(response[field])

    return response


def parse_info(response):
    "Parse the result of Redis's INFO command into a Python dict"
    info = {}
    response = response.decode()

    def get_value(value):
        if ',' not in value or '=' not in value:
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                return value
        else:
            sub_dict = {}
            for item in value.split(','):
                k, v = item.rsplit('=', 1)
                sub_dict[k] = get_value(v)
            return sub_dict

    for line in response.splitlines():
        if line and not line.startswith('#'):
            if line.find(':') != -1:
                key, value = line.split(':', 1)
                info[key] = get_value(value)
            else:
                # if the line isn't splittable, append it to the "__raw__" key
                info.setdefault('__raw__', []).append(line)

    return info


class ServerCommandMixin:

    RESPONSE_CALLBACKS = dict_merge(
        string_keys_to_dict('BGREWRITEAOF BGSAVE', lambda r: True),
        string_keys_to_dict(
            'FLUSHALL FLUSHDB SAVE '
            'SHUTDOWN SLAVEOF', bool_ok
        ),
        {
            'SLOWLOG GET': parse_slowlog_get,
            'SLOWLOG LEN': int,
            'SLOWLOG RESET': bool_ok,
            'CLIENT GETNAME': lambda r: r and r.decode(),
            'CLIENT KILL': bool_ok,
            'CLIENT LIST': parse_client_list,
            'CLIENT SETNAME': bool_ok,
            'CLIENT PAUSE': bool_ok,
            # 'CLIENT REPLY': lambda r: r == b'OK' if r else None,
            'CONFIG GET': parse_config_get,
            'CONFIG RESETSTAT': bool_ok,
            'CONFIG SET': bool_ok,
            'DEBUG OBJECT': parse_debug_object,
            'INFO': parse_info,
            'LASTSAVE': timestamp_to_datetime,
            'TIME': lambda x: (int(x[0]), int(x[1])),
        }
    )

    async def bgrewriteaof(self):
        "Tell the Redis server to rewrite the AOF file from data in memory."
        return await self.execute_command('BGREWRITEAOF')

    async def bgsave(self):
        """
        Tell the Redis server to save its data to disk.  Unlike save(),
        this method is asynchronous and returns immediately.
        """
        return await self.execute_command('BGSAVE')

    async def client_kill(self, address):
        "Disconnects the client at ``address`` (ip:port)"
        return await self.execute_command('CLIENT KILL', address)

    async def client_list(self):
        "Returns a list of currently connected clients"
        return await self.execute_command('CLIENT LIST')

    async def client_getname(self):
        "Returns the current connection name"
        return await self.execute_command('CLIENT GETNAME')

    async def client_setname(self, name):
        "Sets the current connection name"
        return await self.execute_command('CLIENT SETNAME', name)

    async def client_pause(self, timeout=0):
        """suspend all the Redis clients for the
        specified amount of time (in milliseconds)."""
        return await self.execute_command('CLIENT PAUSE', timeout)

    async def config_get(self, pattern="*"):
        "Return a dictionary of configuration based on the ``pattern``"
        return await self.execute_command('CONFIG GET', pattern)

    async def config_set(self, name, value):
        "Set config item ``name`` with ``value``"
        return await self.execute_command('CONFIG SET', name, value)

    async def config_resetstat(self):
        "Reset runtime statistics"
        return await self.execute_command('CONFIG RESETSTAT')

    async def config_rewrite(self):
        "Rewrite config file with the minimal change to reflect running config"
        return await self.execute_command('CONFIG REWRITE')

    async def dbsize(self):
        "Returns the number of keys in the current database"
        return await self.execute_command('DBSIZE')

    async def debug_object(self, key):
        "Returns version specific meta information about a given key"
        return await self.execute_command('DEBUG OBJECT', key)

    async def flushall(self):
        "Delete all keys in all databases on the current host"
        return await self.execute_command('FLUSHALL')

    async def flushdb(self):
        "Delete all keys in the current database"
        return await self.execute_command('FLUSHDB')

    async def info(self, section=None):
        """
        Returns a dictionary containing information about the Redis server

        The ``section`` option can be used to select a specific section
        of information

        The section option is not supported by older versions of Redis Server,
        and will generate ResponseError
        """
        if section is None:
            return await self.execute_command('INFO')
        else:
            return await self.execute_command('INFO', section)

    async def lastsave(self):
        """
        Return a Python datetime object representing the last time the
        Redis database was saved to disk
        """
        return await self.execute_command('LASTSAVE')

    async def save(self):
        """
        Tell the Redis server to save its data to disk,
        blocking until the save is complete
        """
        return await self.execute_command('SAVE')

    async def shutdown(self):
        "Shutdown the server"
        try:
            await self.execute_command('SHUTDOWN')
        except ConnectionError:
            # a ConnectionError here is expected
            return
        raise RedisError("SHUTDOWN seems to have failed.")

    async def slaveof(self, host=None, port=None):
        """
        Set the server to be a replicated slave of the instance identified
        by the ``host`` and ``port``. If called without arguments, the
        instance is promoted to a master instead.
        """
        if host is None and port is None:
            return await self.execute_command('SLAVEOF', b('NO'), b('ONE'))
        return await self.execute_command('SLAVEOF', host, port)

    async def slowlog_get(self, num=None):
        """
        Get the entries from the slowlog. If ``num`` is specified, get the
        most recent ``num`` items.
        """
        args = ['SLOWLOG GET']
        if num is not None:
            args.append(num)
        return await self.execute_command(*args)

    async def slowlog_len(self):
        "Get the number of items in the slowlog"
        return await self.execute_command('SLOWLOG LEN')

    async def slowlog_reset(self):
        "Remove all items in the slowlog"
        return await self.execute_command('SLOWLOG RESET')

    async def time(self):
        """
        Returns the server time as a 2-item tuple of ints:
        (seconds since epoch, microseconds into this second).
        """
        return await self.execute_command('TIME')

    # todo
    async def role(self):
        pass
