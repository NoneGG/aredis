Sentinel support
================

aredis can be used together with `Redis Sentinel <http://redis.io/topics/sentinel>`_
to discover Redis nodes. You need to have at least one Sentinel daemon running
in order to use aredis's Sentinel support.

Connecting aredis to the Sentinel instance(s) is easy. You can use a
Sentinel connection to discover the master and slaves network addresses:

.. code-block:: python

    >>> from redis.sentinel import Sentinel
    >>> sentinel = Sentinel([('localhost', 26379)], socket_timeout=0.1)
    >>> await sentinel.discover_master('mymaster')
    ('127.0.0.1', 6379)
    >>> await sentinel.discover_slaves('mymaster')
    [('127.0.0.1', 6380)]

You can also create Redis client connections from a Sentinel instance. You can
connect to either the master (for write operations) or a slave (for read-only
operations).

.. code-block:: pycon

    >>> master = sentinel.master_for('mymaster', socket_timeout=0.1)
    >>> slave = sentinel.slave_for('mymaster', socket_timeout=0.1)
    >>> master.set('foo', 'bar')
    >>> slave.get('foo')
    'bar'

The master and slave objects are normal StrictRedis instances with their
connection pool bound to the Sentinel instance. When a Sentinel backed client
attempts to establish a connection, it first queries the Sentinel servers to
determine an appropriate host to connect to. If no server is found,
a MasterNotFoundError or SlaveNotFoundError is raised. Both exceptions are
subclasses of ConnectionError.

When trying to connect to a slave client, the Sentinel connection pool will
iterate over the list of slaves until it finds one that can be connected to.
If no slaves can be connected to, a connection will be established with the
master.

See `Guidelines for Redis clients with support for Redis Sentinel
<http://redis.io/topics/sentinel-clients>`_ to learn more about Redis Sentinel.