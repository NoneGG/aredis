API Reference
=============

The connection part is rewritten to make client async, and most API is ported from redis-py.
So most API and usage are the same as redis-py.
If you use redis-py in your code, just use `async/await` syntax with your code.
`for more examples <https://github.com/NoneGG/aredis/tree/master/examples>`_

The `official Redis command documentation <http://redis.io/commands>`_ does a
great job of explaining each command in detail. aredis only shift StrictRedis
class from redis-py that implement these commands. The StrictRedis class attempts to adhere
to the official command syntax. There are a few exceptions:

* **SELECT**: Not implemented. See the explanation in the Thread Safety section
  below.
* **DEL**: 'del' is a reserved keyword in the Python syntax. Therefore aredis
  uses 'delete' instead.
* **CONFIG GET|SET**: These are implemented separately as config_get or config_set.
* **MULTI/EXEC**: These are implemented as part of the Pipeline class. The
  pipeline is wrapped with the MULTI and EXEC statements by default when it
  is executed, which can be disabled by specifying transaction=False.
  See more about Pipelines below.
* **SUBSCRIBE/LISTEN**: Similar to pipelines, PubSub is implemented as a separate
  class as it places the underlying connection in a state where it can't
  execute non-pubsub commands. Calling the pubsub method from the Redis client
  will return a PubSub instance where you can subscribe to channels and listen
  for messages. You can only call PUBLISH from the Redis client.
* **SCAN/SSCAN/HSCAN/ZSCAN**: The \*SCAN commands are implemented as they
  exist in the Redis documentation.
  In addition, each command has an equivilant iterator method.
  These are purely for convenience so the user doesn't have to keep
  track of the cursor while iterating. (Use Python 3.6 and the scan_iter/sscan_iter/hscan_iter/zscan_iter
  methods for this behavior. **iter functions are not supported in Python 3.5**)

Loop
^^^^

The event loop can be set with the loop keyword argugment. If no loop is given
the default event loop will be

**warning**

**asyncio.AbstractEventLoop** is actually not thread safe and asyncio uses **BaseDefaultEventLoopPolicy** as default
event policy(which create new event loop instead of sharing event loop between threads,
being thread safe to some degree) So the StricRedis is still thread safe if your code works with default event loop.
But if you customize event loop yourself, please make sure your event loop is thread safe(maybe you should customize
on the base of **BaseDefaultEventLoopPolicy** instead of **AbstractEventLoop**)

Detailed discussion about the problem is in `issue20 <https://github.com/NoneGG/aredis/pull/20#issuecomment-285088890>`_

.. code-block:: python

    import aredis
    import asyncio
    loop = asyncio.get_event_loop()
    r = aredis.StrictRedis(host='localhost', port=6379, db=0, loop=loop)

Decoding
^^^^^^^^

Param **encoding** and **decode_responses** are now used to support response encoding.

**encoding** is used for specifying with which encoding you want responses to be decoded.
**decode_responses** is used for tell the client whether responses should be decoded.

If decode_responses is set to True and no encoding is specified, client will use 'utf-8' by default.

Connections
^^^^^^^^^^^

ConnectionPools manage a set of Connection instances. aredis ships with two
types of Connections. The default, Connection, is a normal TCP socket based
connection. The UnixDomainSocketConnection allows for clients running on the
same device as the server to connect via a unix domain socket. To use a
UnixDomainSocketConnection connection, simply pass the unix_socket_path
argument, which is a string to the unix domain socket file. Additionally, make
sure the unixsocket parameter is defined in your redis.conf file. It's
commented out by default.

.. code-block:: python

    r = redis.StrictRedis(unix_socket_path='/tmp/redis.sock')

You can create your own Connection subclasses as well. This may be useful if
you want to control the socket behavior within an async framework. To
instantiate a client class using your own connection, you need to create
a connection pool, passing your class to the connection_class argument.
Other keyword parameters you pass to the pool will be passed to the class
specified during initialization.

.. code-block:: python

    pool = redis.ConnectionPool(connection_class=YourConnectionClass,
                                    your_arg='...', ...)

Parsers
^^^^^^^

Parser classes provide a way to control how responses from the Redis server
are parsed. aredis ships with two parser classes, the PythonParser and the
HiredisParser. By default, aredis will attempt to use the HiredisParser if
you have the hiredis module installed and will fallback to the PythonParser
otherwise.

Hiredis is a C library maintained by the core Redis team. Pieter Noordhuis was
kind enough to create Python bindings. Using Hiredis can provide up to a
10x speed improvement in parsing responses from the Redis server. The
performance increase is most noticeable when retrieving many pieces of data,
such as from LRANGE or SMEMBERS operations.


Hiredis is available on PyPI, and can be installed as an extra dependency to
aredis.


.. code-block:: bash

    $ pip install aredis[hiredis]


or

.. code-block:: bash

    $ easy_install aredis[hiredis]

Response Callbacks
^^^^^^^^^^^^^^^^^^

The client class uses a set of callbacks to cast Redis responses to the
appropriate Python type. There are a number of these callbacks defined on
the Redis client class in a dictionary called RESPONSE_CALLBACKS.

Custom callbacks can be added on a per-instance basis using the
set_response_callback method. This method accepts two arguments: a command
name and the callback. Callbacks added in this manner are only valid on the
instance the callback is added to. If you want to define or override a callback
globally, you should make a subclass of the Redis client and add your callback
to its REDIS_CALLBACKS class dictionary.

Response callbacks take at least one parameter: the response from the Redis
server. Keyword arguments may also be accepted in order to further control
how to interpret the response. These keyword arguments are specified during the
command's call to execute_command. The ZRANGE implementation demonstrates the
use of response callback keyword arguments with its "withscores" argument.

Thread Safety
^^^^^^^^^^^^^

Redis client instances can safely be shared between threads. Internally,
connection instances are only retrieved from the connection pool during
command execution, and returned to the pool directly after. Command execution
never modifies state on the client instance.

However, there is one caveat: the Redis SELECT command. The SELECT command
allows you to switch the database currently in use by the connection. That
database remains selected until another is selected or until the connection is
closed. This creates an issue in that connections could be returned to the pool
that are connected to a different database.

As a result, aredis does not implement the SELECT command on client
instances. If you use multiple Redis databases within the same application, you
should create a separate client instance (and possibly a separate connection
pool) for each database.

**It is not safe to pass PubSub or Pipeline objects between threads.**
