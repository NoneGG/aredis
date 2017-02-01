import sys

from aredis.connection import UnixDomainSocketConnection
from aredis.pool import ConnectionPool
from aredis.utils import dict_merge
from aredis.exceptions import (
    ConnectionError,
    TimeoutError,
)
from aredis.commands.cluster import ClusterCommandMixin
from aredis.commands.connection import ConnectionCommandMixin
from aredis.commands.extra import ExtraCommandMixin
from aredis.commands.geo import GeoCommandMixin
from aredis.commands.hash import HashCommandMixin
from aredis.commands.hyperlog import HyperLogCommandMixin
from aredis.commands.keys import KeysCommandMixin
from aredis.commands.lists import ListsCommandMixin
from aredis.commands.pubsub import PubSubCommanMixin
from aredis.commands.scripting import ScriptingCommandMixin
from aredis.commands.sentinel import SentinelCommandMixin
from aredis.commands.server import ServerCommandMixin
from aredis.commands.sets import SetsCommandMixin
from aredis.commands.sorted_set import SortedSetCommandMixin
from aredis.commands.strings import StringsCommandMixin
from aredis.commands.transaction import TransactionCommandMixin

mixins = [
    ClusterCommandMixin, ConnectionCommandMixin, ExtraCommandMixin,
    GeoCommandMixin, HashCommandMixin, HyperLogCommandMixin,
    KeysCommandMixin, ListsCommandMixin, PubSubCommanMixin,
    ScriptingCommandMixin, SentinelCommandMixin, ServerCommandMixin,
    SetsCommandMixin, SortedSetCommandMixin, StringsCommandMixin,
    TransactionCommandMixin
]
if sys.version_info[:2] >= (3, 6):
    from aredis.commands.iter import IterCommandMixin
    mixins.append(IterCommandMixin)


class StrictRedis(*mixins):
    """
    Implementation of the Redis protocol.

    This abstract class provides a Python interface to all Redis commands
    and an implementation of the Redis protocol.

    Connection and Pipeline derive from this, implementing how
    the commands are sent and received to the Redis server
    """

    RESPONSE_CALLBACKS = dict_merge(
        *[mixin.RESPONSE_CALLBACKS for mixin in mixins]
    )

    @classmethod
    def from_url(cls, url, db=None, **kwargs):
        """
        Return a Redis client object configured from the given URL, which must
        use either `the ``redis://`` scheme
        <http://www.iana.org/assignments/uri-schemes/prov/redis>`_ for RESP
        connections or the ``unix://`` scheme for Unix domain sockets.

        For example::

            redis://[:password]@localhost:6379/0
            unix://[:password]@/path/to/socket.sock?db=0

        There are several ways to specify a database number. The parse function
        will return the first specified option:
            1. A ``db`` querystring option, e.g. redis://localhost?db=0
            2. If using the redis:// scheme, the path argument of the url, e.g.
               redis://localhost/0
            3. The ``db`` argument to this function.

        If none of these options are specified, db=0 is used.

        Any additional querystring arguments and keyword arguments will be
        passed along to the ConnectionPool class's initializer. In the case
        of conflicting arguments, querystring arguments always win.
        """
        connection_pool = ConnectionPool.from_url(url, db=db, **kwargs)
        return cls(connection_pool=connection_pool)

    def __init__(self, host='localhost', port=6379,
                 db=0, password=None, stream_timeout=None,
                 connect_timeout=None, connection_pool=None,
                 unix_socket_path=None,
                 ssl=False, ssl_keyfile=None, ssl_certfile=None,
                 ssl_cert_reqs=None, ssl_ca_certs=None,
                 max_connections=None, retry_on_timeout=False):
        if not connection_pool:
            kwargs = {
                'db': db,
                'password': password,
                'stream_timeout': stream_timeout,
                'connect_timeout': connect_timeout,
                'max_connections': max_connections,
                'retry_on_timeout': retry_on_timeout
            }
            # based on input, setup appropriate connection args
            if unix_socket_path is not None:
                kwargs.update({
                    'path': unix_socket_path,
                    'connection_class': UnixDomainSocketConnection
                })
            else:
                # TCP specific options
                kwargs.update({
                    'host': host,
                    'port': port
                })

                if ssl:
                    kwargs.update({
                        'ssl_keyfile': ssl_keyfile,
                        'ssl_certfile': ssl_certfile,
                        'ssl_cert_reqs': ssl_cert_reqs,
                        'ssl_ca_certs': ssl_ca_certs,
                    })
            connection_pool = ConnectionPool(**kwargs)
        self.connection_pool = connection_pool
        self._use_lua_lock = None

        self.response_callbacks = self.__class__.RESPONSE_CALLBACKS.copy()

    def __repr__(self):
        return "{}<{}>".format(type(self).__name__, repr(self.connection_pool))

    def set_response_callback(self, command, callback):
        "Set a custom Response Callback"
        self.response_callbacks[command] = callback

    # COMMAND EXECUTION AND PROTOCOL PARSING
    async def execute_command(self, *args, **options):
        "Execute a command and return a parsed response"
        pool = self.connection_pool
        command_name = args[0]
        connection = pool.get_connection()
        try:
            await connection.send_command(*args)
            return await self.parse_response(connection, command_name, **options)
        except (ConnectionError, TimeoutError) as e:
            connection.disconnect()
            if not connection.retry_on_timeout and isinstance(e, TimeoutError):
                raise
            await connection.send_command(*args)
            return await self.parse_response(connection, command_name, **options)
        finally:
            pool.release(connection)

    async def parse_response(self, connection, command_name, **options):
        "Parses a response from the Redis server"
        response = await connection.read_response()
        if command_name in self.response_callbacks:
            callback = self.response_callbacks[command_name]
            return callback(response, **options)
        return response
