#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
import os
import warnings
import time
import random
import threading
from itertools import chain
from urllib.parse import parse_qs, unquote, urlparse
from coredis.connection import (
    RedisSSLContext,
    Connection,
    UnixDomainSocketConnection,
    ClusterConnection,
)
from coredis.nodemanager import NodeManager
from coredis.exceptions import ConnectionError, RedisClusterException

FALSE_STRINGS = ("0", "F", "FALSE", "N", "NO")


def to_bool(value):
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.upper() in FALSE_STRINGS:
        return False
    return bool(value)


URL_QUERY_ARGUMENT_PARSERS = {
    "stream_timeout": float,
    "connect_timeout": float,
    "retry_on_timeout": to_bool,
}


class ConnectionPool:
    """Generic connection pool"""

    @classmethod
    def from_url(cls, url, db=None, decode_components=False, **kwargs):
        """
        Returns a connection pool configured from the given URL.

        For example::

        redis://[:password]@localhost:6379/0
        rediss://[:password]@localhost:6379/0
        unix://[:password]@/path/to/socket.sock?db=0

        Three URL schemes are supported:

        - ```redis://``
        <http://www.iana.org/assignments/uri-schemes/prov/redis>`_ creates a
        normal TCP socket connection
        - ```rediss://``
        <http://www.iana.org/assignments/uri-schemes/prov/rediss>`_ creates a
        SSL wrapped TCP socket connection
        - ``unix://`` creates a Unix Domain Socket connection

        There are several ways to specify a database number. The parse function
        will return the first specified option:
        1. A ``db`` querystring option, e.g. redis://localhost?db=0
        2. If using the redis:// scheme, the path argument of the url, e.g.
        redis://localhost/0
        3. The ``db`` argument to this function.

        If none of these options are specified, db=0 is used.

        The ``decode_components`` argument allows this function to work with
        percent-encoded URLs. If this argument is set to ``True`` all ``%xx``
        escapes will be replaced by their single-character equivalents after
        the URL has been parsed. This only applies to the ``hostname``,
        ``path``, and ``password`` components.

        Any additional querystring arguments and keyword arguments will be
        passed along to the ConnectionPool class's initializer. The querystring
        arguments ``connect_timeout`` and ``stream_timeout`` if supplied
        are parsed as float values. The arguments ``retry_on_timeout`` are
        parsed to boolean values that accept True/False, Yes/No values to indicate state.
        Invalid types cause a ``UserWarning`` to be raised.
        In the case of conflicting arguments, querystring arguments always win.
        """
        url = urlparse(url)
        qs = url.query

        url_options = {}

        for name, value in iter(parse_qs(qs).items()):
            if value and len(value) > 0:
                parser = URL_QUERY_ARGUMENT_PARSERS.get(name)
                if parser:
                    try:
                        url_options[name] = parser(value[0])
                    except (TypeError, ValueError):
                        warnings.warn(
                            UserWarning(
                                "Invalid value for `%s` in connection URL." % name
                            )
                        )
                else:
                    url_options[name] = value[0]

        if decode_components:
            password = unquote(url.password) if url.password else None
            path = unquote(url.path) if url.path else None
            hostname = unquote(url.hostname) if url.hostname else None
        else:
            password = url.password
            path = url.path
            hostname = url.hostname

        # We only support redis:// and unix:// schemes.
        if url.scheme == "unix":
            url_options.update(
                {
                    "password": password,
                    "path": path,
                    "connection_class": UnixDomainSocketConnection,
                }
            )

        else:
            url_options.update(
                {"host": hostname, "port": int(url.port or 6379), "password": password,}
            )

            # If there's a path argument, use it as the db argument if a
            # querystring value wasn't specified
            if "db" not in url_options and path:
                try:
                    url_options["db"] = int(path.replace("/", ""))
                except (AttributeError, ValueError):
                    pass

            if url.scheme == "rediss":
                keyfile = url_options.pop("ssl_keyfile", None)
                certfile = url_options.pop("ssl_certfile", None)
                cert_reqs = url_options.pop("ssl_cert_reqs", None)
                ca_certs = url_options.pop("ssl_ca_certs", None)
                url_options["ssl_context"] = RedisSSLContext(
                    keyfile, certfile, cert_reqs, ca_certs
                ).get()

        # last shot at the db value
        url_options["db"] = int(url_options.get("db", db or 0))

        # update the arguments from the URL values
        kwargs.update(url_options)
        return cls(**kwargs)

    def __init__(
        self,
        connection_class=Connection,
        max_connections=None,
        max_idle_time=0,
        idle_check_interval=1,
        **connection_kwargs
    ):
        """
        Creates a connection pool. If max_connections is set, then this
        object raises redis.ConnectionError when the pool's limit is reached.

        By default, TCP connections are created connection_class is specified.
        Use redis.UnixDomainSocketConnection for unix sockets.

        Any additional keyword arguments are passed to the constructor of
        connection_class.
        """
        max_connections = max_connections or 2 ** 31
        if not isinstance(max_connections, int) or max_connections < 0:
            raise ValueError('"max_connections" must be a positive integer')

        self.connection_class = connection_class
        self.connection_kwargs = connection_kwargs
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.idle_check_interval = idle_check_interval
        self.loop = self.connection_kwargs.get("loop")

        self.reset()

    def __repr__(self):
        return "{}<{}>".format(
            type(self).__name__,
            self.connection_class.description.format(**self.connection_kwargs),
        )

    async def disconnect_on_idle_time_exceeded(self, connection):
        while True:
            if (
                time.time() - connection.last_active_at > self.max_idle_time
                and not connection.awaiting_response
            ):
                connection.disconnect()
                try:
                    self._available_connections.remove(connection)
                except ValueError:
                    pass
                self._created_connections -= 1
                break
            await asyncio.sleep(self.idle_check_interval)

    def reset(self):
        self.pid = os.getpid()
        self._created_connections = 0
        self._available_connections = []
        self._in_use_connections = set()
        self._check_lock = threading.Lock()

    def _checkpid(self):
        if self.pid != os.getpid():
            with self._check_lock:
                if self.pid == os.getpid():
                    # another thread already did the work while we waited
                    # on the lock.
                    return
                self.disconnect()
                self.reset()

    def get_connection(self, *args, **kwargs):
        """Gets a connection from the pool"""
        self._checkpid()
        try:
            connection = self._available_connections.pop()
        except IndexError:
            connection = self.make_connection()
        self._in_use_connections.add(connection)
        return connection

    def make_connection(self):
        """Creates a new connection"""
        if self._created_connections >= self.max_connections:
            raise ConnectionError("Too many connections")
        self._created_connections += 1
        connection = self.connection_class(**self.connection_kwargs)
        if self.max_idle_time > self.idle_check_interval > 0:
            # do not await the future
            asyncio.ensure_future(self.disconnect_on_idle_time_exceeded(connection))
        return connection

    def release(self, connection):
        """Releases the connection back to the pool"""
        self._checkpid()
        if connection.pid != self.pid:
            return
        self._in_use_connections.remove(connection)
        # discard connection with unread response
        if connection.awaiting_response:
            connection.disconnect()
            self._created_connections -= 1
        else:
            self._available_connections.append(connection)

    def disconnect(self):
        """Closes all connections in the pool"""
        all_conns = chain(self._available_connections, self._in_use_connections)
        for connection in all_conns:
            connection.disconnect()
            self._created_connections -= 1


class ClusterConnectionPool(ConnectionPool):
    """Custom connection pool for rediscluster"""

    RedisClusterDefaultTimeout = None

    def __init__(
        self,
        startup_nodes=None,
        connection_class=ClusterConnection,
        max_connections=None,
        max_connections_per_node=False,
        reinitialize_steps=None,
        skip_full_coverage_check=False,
        nodemanager_follow_cluster=False,
        readonly=False,
        max_idle_time=0,
        idle_check_interval=1,
        **connection_kwargs
    ):
        """
        :skip_full_coverage_check:
            Skips the check of cluster-require-full-coverage config, useful for clusters
            without the CONFIG command (like aws)
        :nodemanager_follow_cluster:
            The node manager will during initialization try the last set of nodes that
            it was operating on. This will allow the client to drift along side the cluster
            if the cluster nodes move around alot.
        """
        super(ClusterConnectionPool, self).__init__(
            connection_class=connection_class, max_connections=max_connections
        )

        # Special case to make from_url method compliant with cluster setting.
        # from_url method will send in the ip and port through a different variable then the
        # regular startup_nodes variable.
        if startup_nodes is None:
            if "port" in connection_kwargs and "host" in connection_kwargs:
                startup_nodes = [
                    {
                        "host": connection_kwargs.pop("host"),
                        "port": str(connection_kwargs.pop("port")),
                    }
                ]

        self.max_connections = max_connections or 2 ** 31
        self.max_connections_per_node = max_connections_per_node
        self.nodes = NodeManager(
            startup_nodes,
            reinitialize_steps=reinitialize_steps,
            skip_full_coverage_check=skip_full_coverage_check,
            max_connections=self.max_connections,
            nodemanager_follow_cluster=nodemanager_follow_cluster,
            **connection_kwargs
        )
        self.initialized = False

        self.connections = {}
        self.connection_kwargs = connection_kwargs
        self.connection_kwargs["readonly"] = readonly
        self.readonly = readonly
        self.max_idle_time = max_idle_time
        self.idle_check_interval = idle_check_interval
        self.reset()

        if "stream_timeout" not in self.connection_kwargs:
            self.connection_kwargs[
                "stream_timeout"
            ] = ClusterConnectionPool.RedisClusterDefaultTimeout

    def __repr__(self):
        """
        Returns a string with all unique ip:port combinations that this pool
        is connected to
        """
        return "{0}<{1}>".format(
            type(self).__name__,
            ", ".join(
                [
                    self.connection_class.description.format(**node)
                    for node in self.nodes.startup_nodes
                ]
            ),
        )

    async def initialize(self):
        if not self.initialized:
            await self.nodes.initialize()
            self.initialized = True

    async def disconnect_on_idle_time_exceeded(self, connection):
        while True:
            if (
                time.time() - connection.last_active_at > self.max_idle_time
                and not connection.awaiting_response
            ):
                connection.disconnect()
                node = connection.node
                self._available_connections[node["name"]].remove(connection)
                self._created_connections_per_node[node["name"]] -= 1
                break
            await asyncio.sleep(self.idle_check_interval)

    def reset(self):
        """Resets the connection pool back to a clean state"""
        self.pid = os.getpid()
        self._created_connections_per_node = {}  # Dict(Node, Int)
        self._available_connections = {}  # Dict(Node, List)
        self._in_use_connections = {}  # Dict(Node, Set)
        self._check_lock = threading.Lock()
        self.initialized = False

    def _checkpid(self):
        if self.pid != os.getpid():
            with self._check_lock:
                if self.pid == os.getpid():
                    # another thread already did the work while we waited
                    # on the lockself.
                    return
                self.disconnect()
                self.reset()

    def get_connection(self, command_name, *keys, **options):
        # Only pubsub command/connection should be allowed here
        if command_name != "pubsub":
            raise RedisClusterException(
                "Only 'pubsub' commands can use get_connection()"
            )

        channel = options.pop("channel", None)

        if not channel:
            return self.get_random_connection()

        slot = self.nodes.keyslot(channel)
        node = self.get_master_node_by_slot(slot)

        self._checkpid()

        try:
            connection = self._available_connections.get(node["name"], []).pop()
        except IndexError:
            connection = self.make_connection(node)

        if node["name"] not in self._in_use_connections:
            self._in_use_connections[node["name"]] = set()

        self._in_use_connections[node["name"]].add(connection)

        return connection

    def make_connection(self, node):
        """Creates a new connection"""
        if self.count_all_num_connections(node) >= self.max_connections:
            if self.max_connections_per_node:
                raise RedisClusterException(
                    "Too many connection ({0}) for node: {1}".format(
                        self.count_all_num_connections(node), node["name"]
                    )
                )

            raise RedisClusterException("Too many connections")

        self._created_connections_per_node.setdefault(node["name"], 0)
        self._created_connections_per_node[node["name"]] += 1
        connection = self.connection_class(
            host=node["host"], port=node["port"], **self.connection_kwargs
        )

        # Must store node in the connection to make it eaiser to track
        connection.node = node
        if self.max_idle_time > self.idle_check_interval > 0:
            # do not await the future
            asyncio.ensure_future(self.disconnect_on_idle_time_exceeded(connection))
        return connection

    def release(self, connection):
        """Releases the connection back to the pool"""
        self._checkpid()
        if connection.pid != self.pid:
            return

        # Remove the current connection from _in_use_connection and add it back to the available pool
        # There is cases where the connection is to be removed but it will not exist and there
        # must be a safe way to remove
        i_c = self._in_use_connections.get(connection.node["name"], set())
        if connection in i_c:
            i_c.remove(connection)
        else:
            pass
        # discard connection with unread response
        if connection.awaiting_response:
            connection.disconnect()
            # reduce node connection count in case of too many connection error raised
            if (
                self.max_connections_per_node
                and self._created_connections_per_node.get(connection.node["name"])
            ):
                self._created_connections_per_node[connection.node["name"]] -= 1
        else:
            self._available_connections.setdefault(connection.node["name"], []).append(
                connection
            )

    def disconnect(self):
        """Closes all connectins in the pool"""
        all_conns = chain(
            self._available_connections.values(), self._in_use_connections.values(),
        )

        for node_connections in all_conns:
            for connection in node_connections:
                connection.disconnect()

    def count_all_num_connections(self, node):
        if self.max_connections_per_node:
            return self._created_connections_per_node.get(node["name"], 0)

        return sum([i for i in self._created_connections_per_node.values()])

    def get_random_connection(self):
        """Opens new connection to random redis server"""
        if self._available_connections:
            node_name = random.choice(list(self._available_connections.keys()))
            conn_list = self._available_connections[node_name]
            # check it in case of empty connection list
            if conn_list:
                return conn_list.pop()
        for node in self.nodes.random_startup_node_iter():
            connection = self.get_connection_by_node(node)

            if connection:
                return connection

        raise Exception("Cant reach a single startup node.")

    def get_connection_by_key(self, key):
        if not key:
            raise RedisClusterException(
                "No way to dispatch this command to Redis Cluster."
            )

        return self.get_connection_by_slot(self.nodes.keyslot(key))

    def get_connection_by_slot(self, slot):
        """
        Determines what server a specific slot belongs to and return a redis
        object that is connected
        """
        self._checkpid()

        try:
            return self.get_connection_by_node(self.get_node_by_slot(slot))
        except KeyError:
            return self.get_random_connection()

    def get_connection_by_node(self, node):
        """Gets a connection by node"""
        self._checkpid()
        self.nodes.set_node_name(node)

        try:
            # Try to get connection from existing pool
            connection = self._available_connections.get(node["name"], []).pop()
        except IndexError:
            connection = self.make_connection(node)

        self._in_use_connections.setdefault(node["name"], set()).add(connection)

        return connection

    def get_master_node_by_slot(self, slot):
        return self.nodes.slots[slot][0]

    def get_node_by_slot(self, slot):
        if self.readonly:
            return random.choice(self.nodes.slots[slot])
        return self.get_master_node_by_slot(slot)
