aredis
======
|pypi-ver| |travis-status| |python-ver|

An efficient and user-friendly async redis client ported from `redis-py <https://github.com/andymccurdy/redis-py>`_
(which is a Python interface to the Redis key-value)

Installation
------------

aredis requires a running Redis server.

To install aredis, simply:

.. code-block:: bash

    $ sudo pip3 install aredis

or alternatively (you really should be using pip though):

.. code-block:: bash

    $ sudo easy_install aredis

or from source:

.. code-block:: bash

    $ sudo python setup.py install


Getting Started
---------------

.. code-block:: python

    >>> import aredis
    >>> import asyncio
    >>> r = aredis.StrictRedis(host='localhost', port=6379, db=0)
    >>> loop = asyncio.get_event_loop()
    >>> async def test():
    >>>     await r.set('foo', 'bar')
    >>>     print(await r.get('foo'))
    >>> loop.run_until_complete(test())
    b'bar'

API Reference
-------------

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

    >>> r = redis.StrictRedis(unix_socket_path='/tmp/redis.sock')

You can create your own Connection subclasses as well. This may be useful if
you want to control the socket behavior within an async framework. To
instantiate a client class using your own connection, you need to create
a connection pool, passing your class to the connection_class argument.
Other keyword parameters you pass to the pool will be passed to the class
specified during initialization.

.. code-block:: python

    >>> pool = redis.ConnectionPool(connection_class=YourConnectionClass,
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

Hiredis is available on PyPI, and can be installed via pip or easy_install
just like aredis.

.. code-block:: bash

    $ pip install hiredis

or

.. code-block:: bash

    $ easy_install hiredis

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

Cache
^^^^^

There are two kinds of cache class(Cache & HerdCache) provided.
Cache classes consists of IdentityGenerator(used to generate unique identity in redis),
Serializer(used to serialize content before compress and finally put in redis),
Compressor(used to compress cache to reduce memory usage of redis.
IdentityGenerator, Serializer, Compressor can be overwritten to meet your special needs,
and if you don't need it, just set them to None when intialize a cache:

.. code-block:: python

    >>> class CustomIdentityGenerator(IdentityGenerator):
    >>>     def generate(self, key, content):
    >>>         return key
    >>>
    >>> def expensive_work(data):
    >>> """some work that waits for io or occupy cpu"""
    >>>     return data
    >>>
    >>> async def example():
    >>>     client = aredis.StrictRedis()
    >>>     await client.flushall()
    >>>     cache = client.cache('example_cache',
    >>>             identity_generator_class=CustomIdentityGenerator)
    >>>     data = {1: 1}
    >>>     await cache.set('example_key', expensive_work(data), data)
    >>>     res = await cache.get('example_key', data)
    >>>     assert res == expensive_work(data)

For ease of use and expandability, only `set`, `set_many`, `exists`, `delete`, `delete_many`,
`ttl`, `get` APIs are realized.

HerdCache is a solution for `thundering herd problem <https://en.wikipedia.org/wiki/Thundering_herd_problem>`_
It is suitable for scene with low consistency and in which refresh cache costs a lot.
It will save redundant update work when there are multi process read cache from redis and the cache is expired.
If the cache is expired is judged by the expire time saved with each key, and the real expire time of the key
`real_expire_time = the time key is set + expire_time + herd_timeout` once a process find out that the cache is expired,
it will reset the expire time saved in redis with `new_expire_time = the time key is found expired + extend_expire_time`,
and return None(act like cache expired), so that other processes will not noticed the cache expired.

Pipelines
^^^^^^^^^

Pipelines are a subclass of the base Redis class that provide support for
buffering multiple commands to the server in a single request. They can be used
to dramatically increase the performance of groups of commands by reducing the
number of back-and-forth TCP packets between the client and server.

Pipelines are quite simple to use:

.. code-block:: python

    >>> async def example(client):
    >>>     async with await client.pipeline(transaction=True) as pipe:
    >>>     # will return self to send another command
    >>>     pipe = await (await pipe.flushdb()).set('foo', 'bar')
    >>>     # can also directly send command
    >>>     await pipe.set('bar', 'foo')
    >>>     # commands will be buffered
    >>>     await pipe.keys('*')
    >>>     res = await pipe.execute()
    >>>     # results should be in order corresponding to your command
    >>>     assert res == [True, True, True, [b'bar', b'foo']]

For ease of use, all commands being buffered into the pipeline return the
pipeline object itself. Which enable you to use it like the example provided.

In addition, pipelines can also ensure the buffered commands are executed
atomically as a group. This happens by default. If you want to disable the
atomic nature of a pipeline but still want to buffer commands, you can turn
off transactions.

.. code-block:: python

    >>> pipe = r.pipeline(transaction=False)

A common issue occurs when requiring atomic transactions but needing to
retrieve values in Redis prior for use within the transaction. For instance,
let's assume that the INCR command didn't exist and we need to build an atomic
version of INCR in Python.

The completely naive implementation could GET the value, increment it in
Python, and SET the new value back. However, this is not atomic because
multiple clients could be doing this at the same time, each getting the same
value from GET.

Enter the WATCH command. WATCH provides the ability to monitor one or more keys
prior to starting a transaction. If any of those keys change prior the
execution of that transaction, the entire transaction will be canceled and a
WatchError will be raised. To implement our own client-side INCR command, we
could do something like this:

.. code-block:: python

    >>> async def example():
    >>>     async with await r.pipeline() as pipe:
    ...         while 1:
    ...             try:
    ...                 # put a WATCH on the key that holds our sequence value
    ...                 await pipe.watch('OUR-SEQUENCE-KEY')
    ...                 # after WATCHing, the pipeline is put into immediate execution
    ...                 # mode until we tell it to start buffering commands again.
    ...                 # this allows us to get the current value of our sequence
    ...                 current_value = await pipe.get('OUR-SEQUENCE-KEY')
    ...                 next_value = int(current_value) + 1
    ...                 # now we can put the pipeline back into buffered mode with MULTI
    ...                 pipe.multi()
    ...                 pipe.set('OUR-SEQUENCE-KEY', next_value)
    ...                 # and finally, execute the pipeline (the set command)
    ...                 await pipe.execute()
    ...                 # if a WatchError wasn't raised during execution, everything
    ...                 # we just did happened atomically.
    ...                 break
    ...             except WatchError:
    ...                 # another client must have changed 'OUR-SEQUENCE-KEY' between
    ...                 # the time we started WATCHing it and the pipeline's execution.
    ...                 # our best bet is to just retry.
    ...                 continue

Note that, because the Pipeline must bind to a single connection for the
duration of a WATCH, care must be taken to ensure that the connection is
returned to the connection pool by calling the reset() method. If the
Pipeline is used as a context manager (as in the example above) reset()
will be called automatically. Of course you can do this the manual way by
explicitly calling reset():

.. code-block:: python

    >>> async def example():
    >>>     async with await r.pipeline() as pipe:
    >>>         while 1:
    ...             try:
    ...                 await pipe.watch('OUR-SEQUENCE-KEY')
    ...                 ...
    ...                 await pipe.execute()
    ...                 break
    ...             except WatchError:
    ...                 continue
    ...             finally:
    ...                 await pipe.reset()

A convenience method named "transaction" exists for handling all the
boilerplate of handling and retrying watch errors. It takes a callable that
should expect a single parameter, a pipeline object, and any number of keys to
be WATCHed. Our client-side INCR command above can be written like this,
which is much easier to read:

.. code-block:: python

    >>> async def client_side_incr(pipe):
    ...     current_value = await pipe.get('OUR-SEQUENCE-KEY')
    ...     next_value = int(current_value) + 1
    ...     pipe.multi()
    ...     await pipe.set('OUR-SEQUENCE-KEY', next_value)
    >>>
    >>> await r.transaction(client_side_incr, 'OUR-SEQUENCE-KEY')
    [True]

Publish / Subscribe
^^^^^^^^^^^^^^^^^^^

aredis includes a `PubSub` object that subscribes to channels and listens
for new messages. Creating a `PubSub` object is easy.

.. code-block:: python

    >>> r = redis.StrictRedis(...)
    >>> p = r.pubsub()

Once a `PubSub` instance is created, channels and patterns can be subscribed
to.

.. code-block:: python

    >>> await p.subscribe('my-first-channel', 'my-second-channel', ...)
    >>> await p.psubscribe('my-*', ...)

The `PubSub` instance is now subscribed to those channels/patterns. The
subscription confirmations can be seen by reading messages from the `PubSub`
instance.

.. code-block:: python

    >>> await p.get_message()
    {'pattern': None, 'type': 'subscribe', 'channel': 'my-second-channel', 'data': 1L}
    >>> await p.get_message()
    {'pattern': None, 'type': 'subscribe', 'channel': 'my-first-channel', 'data': 2L}
    >>> await p.get_message()
    {'pattern': None, 'type': 'psubscribe', 'channel': 'my-*', 'data': 3L}

Every message read from a `PubSub` instance will be a dictionary with the
following keys.

* **type**: One of the following: 'subscribe', 'unsubscribe', 'psubscribe',
  'punsubscribe', 'message', 'pmessage'
* **channel**: The channel [un]subscribed to or the channel a message was
  published to
* **pattern**: The pattern that matched a published message's channel. Will be
  `None` in all cases except for 'pmessage' types.
* **data**: The message data. With [un]subscribe messages, this value will be
  the number of channels and patterns the connection is currently subscribed
  to. With [p]message messages, this value will be the actual published
  message.

Let's send a message now.

.. code-block:: python

    # the publish method returns the number matching channel and pattern
    # subscriptions. 'my-first-channel' matches both the 'my-first-channel'
    # subscription and the 'my-*' pattern subscription, so this message will
    # be delivered to 2 channels/patterns
    >>> await r.publish('my-first-channel', 'some data')
    2
    >>> await p.get_message()
    {'channel': 'my-first-channel', 'data': 'some data', 'pattern': None, 'type': 'message'}
    >>> await p.get_message()
    {'channel': 'my-first-channel', 'data': 'some data', 'pattern': 'my-*', 'type': 'pmessage'}

Unsubscribing works just like subscribing. If no arguments are passed to
[p]unsubscribe, all channels or patterns will be unsubscribed from.

.. code-block:: python

    >>> await p.unsubscribe()
    >>> await p.punsubscribe('my-*')
    >>> await p.get_message()
    {'channel': 'my-second-channel', 'data': 2L, 'pattern': None, 'type': 'unsubscribe'}
    >>> await p.get_message()
    {'channel': 'my-first-channel', 'data': 1L, 'pattern': None, 'type': 'unsubscribe'}
    >>> await p.get_message()
    {'channel': 'my-*', 'data': 0L, 'pattern': None, 'type': 'punsubscribe'}

aredis also allows you to register callback functions to handle published
messages. Message handlers take a single argument, the message, which is a
dictionary just like the examples above. To subscribe to a channel or pattern
with a message handler, pass the channel or pattern name as a keyword argument
with its value being the callback function.

When a message is read on a channel or pattern with a message handler, the
message dictionary is created and passed to the message handler. In this case,
a `None` value is returned from get_message() since the message was already
handled.

.. code-block:: python

    >>> def my_handler(message):
    ...     print('MY HANDLER: ', message['data'])
    >>> await p.subscribe(**{'my-channel': my_handler})
    # read the subscribe confirmation message
    >>> await p.get_message()
    {'pattern': None, 'type': 'subscribe', 'channel': 'my-channel', 'data': 1L}
    >>> await r.publish('my-channel', 'awesome data')
    1
    # for the message handler to work, we need tell the instance to read data.
    # this can be done in several ways (read more below). we'll just use
    # the familiar get_message() function for now
    >>> await message = p.get_message()
    MY HANDLER:  awesome data
    # note here that the my_handler callback printed the string above.
    # `message` is None because the message was handled by our handler.
    >>> print(message)
    None

If your application is not interested in the (sometimes noisy)
subscribe/unsubscribe confirmation messages, you can ignore them by passing
`ignore_subscribe_messages=True` to `r.pubsub()`. This will cause all
subscribe/unsubscribe messages to be read, but they won't bubble up to your
application.

.. code-block:: python

    >>> p = r.pubsub(ignore_subscribe_messages=True)
    >>> await p.subscribe('my-channel')
    >>> await p.get_message()  # hides the subscribe message and returns None
    >>> await r.publish('my-channel')
    1
    >>> await p.get_message()
    {'channel': 'my-channel', 'data': 'my data', 'pattern': None, 'type': 'message'}

There are three different strategies for reading messages.

The examples above have been using `pubsub.get_message()`. Behind the scenes,
`get_message()` uses the system's 'select' module to quickly poll the
connection's socket. If there's data available to be read, `get_message()` will
read it, format the message and return it or pass it to a message handler. If
there's no data to be read, `get_message()` will immediately return None. This
makes it trivial to integrate into an existing event loop inside your
application.

.. code-block:: python

    >>> while True:
    >>>     message = await p.get_message()
    >>>     if message:
    >>>         # do something with the message
    >>>     asyncio.sleep(0.001)  # be nice to the system :)

Older versions of aredis only read messages with `pubsub.listen()`. listen()
is a generator that blocks until a message is available. If your application
doesn't need to do anything else but receive and act on messages received from
redis, listen() is an easy way to get up an running.

.. code-block:: python

    >>> for message in await p.listen():
    ...     # do something with the message

The third option runs an event loop in a separate thread.
`pubsub.run_in_thread()` creates a new thread and use the event loop in main thread.
The thread object is returned to the caller of `run_in_thread()`. The caller can
use the `thread.stop()` method to shut down the event loop and thread. Behind
the scenes, this is simply a wrapper around `get_message()` that runs in a
separate thread, and use `asyncio.run_coroutine_threadsafe()` to run coroutines.

Note: Since we're running in a separate thread, there's no way to handle
messages that aren't automatically handled with registered message handlers.
Therefore, aredis prevents you from calling `run_in_thread()` if you're
subscribed to patterns or channels that don't have message handlers attached.

.. code-block:: python

    >>> await p.subscribe(**{'my-channel': my_handler})
    >>> thread = p.run_in_thread(sleep_time=0.001)
    # the event loop is now running in the background processing messages
    # when it's time to shut it down...
    >>> thread.stop()

PubSub objects remember what channels and patterns they are subscribed to. In
the event of a disconnection such as a network error or timeout, the
PubSub object will re-subscribe to all prior channels and patterns when
reconnecting. Messages that were published while the client was disconnected
cannot be delivered. When you're finished with a PubSub object, call its
`.close()` method to shutdown the connection.

.. code-block:: python

    >>> p = r.pubsub()
    >>> ...
    >>> p.close()

The PUBSUB set of subcommands CHANNELS, NUMSUB and NUMPAT are also
supported:

.. code-block:: pycon

    >>> await r.pubsub_channels()
    ['foo', 'bar']
    >>> await r.pubsub_numsub('foo', 'bar')
    [('foo', 9001), ('bar', 42)]
    >>> await r.pubsub_numsub('baz')
    [('baz', 0)]
    >>> await r.pubsub_numpat()
    1204


LUA Scripting
^^^^^^^^^^^^^

aredis supports the EVAL, EVALSHA, and SCRIPT commands. However, there are
a number of edge cases that make these commands tedious to use in real world
scenarios. Therefore, aredis exposes a Script object that makes scripting
much easier to use.

To create a Script instance, use the `register_script` function on a client
instance passing the LUA code as the first argument. `register_script` returns
a Script instance that you can use throughout your code.

The following trivial LUA script accepts two parameters: the name of a key and
a multiplier value. The script fetches the value stored in the key, multiplies
it with the multiplier value and returns the result.

.. code-block:: pycon

    >>> r = redis.StrictRedis()
    >>> lua = """
    ... local value = redis.call('GET', KEYS[1])
    ... value = tonumber(value)
    ... return value * ARGV[1]"""
    >>> multiply = r.register_script(lua)

`multiply` is now a Script instance that is invoked by calling it like a
function. Script instances accept the following optional arguments:

* **keys**: A list of key names that the script will access. This becomes the
  KEYS list in LUA.
* **args**: A list of argument values. This becomes the ARGV list in LUA.
* **client**: A aredis Client or Pipeline instance that will invoke the
  script. If client isn't specified, the client that intiially
  created the Script instance (the one that `register_script` was
  invoked from) will be used.

Notice that the `Srcipt.__call__` is no longer useful(`async/await` can't be used in magic method),
please use `Script.register` instead

Continuing the example from above:

.. code-block:: python

    >>> await r.set('foo', 2)
    >>> await multiply.execute(keys=['foo'], args=[5])
    10

The value of key 'foo' is set to 2. When multiply is invoked, the 'foo' key is
passed to the script along with the multiplier value of 5. LUA executes the
script and returns the result, 10.

Script instances can be executed using a different client instance, even one
that points to a completely different Redis server.

.. code-block:: python

    >>> r2 = redis.StrictRedis('redis2.example.com')
    >>> await r2.set('foo', 3)
    >>> multiply.execute(keys=['foo'], args=[5], client=r2)
    15

The Script object ensures that the LUA script is loaded into Redis's script
cache. In the event of a NOSCRIPT error, it will load the script and retry
executing it.

Script objects can also be used in pipelines. The pipeline instance should be
passed as the client argument when calling the script. Care is taken to ensure
that the script is registered in Redis's script cache just prior to pipeline
execution.

.. code-block:: python

    >>> pipe = await r.pipeline()
    >>> await pipe.set('foo', 5)
    >>> await multiply(keys=['foo'], args=[5], client=pipe)
    >>> await pipe.execute()
    [True, 25]

Sentinel support
^^^^^^^^^^^^^^^^

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

Benchmark
---------
benchmark/comparation.py run on virtual machine(ubuntu, 4G memory and 2 cpu) with hiredis as parser

local redis server
^^^^^^^^^^^^^^^^^^
+-----------------+---------------+--------------+-----------------+----------------+----------------------+---------------------+--------+
|num of query/time|aredis(asyncio)|aredis(uvloop)|aioredis(asyncio)|aioredis(uvloop)|asyncio_redis(asyncio)|asyncio_redis(uvloop)|redis-py|
+=================+===============+==============+=================+================+======================+=====================+========+
|100              | 0.0190        |   0.01802    |     0.0400      |      0.01989   |       0.0391         |        0.0326       | 0.0111 |
+-----------------+---------------+--------------+-----------------+----------------+----------------------+---------------------+--------+
|1000             | 0.0917        |   0.05998    |     0.1237      |      0.05866   |       0.1838         |        0.1397       | 0.0396 |
+-----------------+---------------+--------------+-----------------+----------------+----------------------+---------------------+--------+
|10000            | 1.0614        |   0.66423    |     1.2277      |      0.62957   |       1.9061         |        1.5464       | 0.3944 |
+-----------------+---------------+--------------+-----------------+----------------+----------------------+---------------------+--------+
|100000           | 10.228        |   6.13821    |     10.400      |      6.06872   |       19.982         |        15.252       | 3.6307 |
+-----------------+---------------+--------------+-----------------+----------------+----------------------+---------------------+--------+

redis server in local area network
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Only run with uvloop, or it will be too slow.
Although it seems like that running code in synchronous way perform more well than in asynchronous way,
the point is that it won't block the other code to run.

+-----------------+--------------+----------------+---------------------+--------+
|num of query/time|aredis(uvloop)|aioredis(uvloop)|asyncio_redis(uvloop)|redis-py|
+=================+==============+================+=====================+========+
|100              |   0.06998    |      0.06019   |        0.1971       | 0.0556 |
+-----------------+--------------+----------------+---------------------+--------+
|1000             |   0.66197    |      0.61183   |        1.9330       | 0.7909 |
+-----------------+--------------+----------------+---------------------+--------+
|10000            |   5.81604    |      6.87364   |        19.186       | 7.1334 |
+-----------------+--------------+----------------+---------------------+--------+
|100000           |   58.4715    |      60.9220   |        189.06       | 58.979 |
+-----------------+--------------+----------------+---------------------+--------+

**test result may change according to your computer performance and network (you may run the sheet yourself to determine which one is the most suitable for you**

Advantage
---------

1. aredis can be used howerver you install hiredis or not.
2. aredis' API are mostly ported from redis-py, which is easy to use indeed and make it easy to port your code with asyncio
3. according to my test, aredis is efficient enough (please run benchmarks/comparation.py to see which async redis client is suitable for you)
4. aredis can be run both with asyncio and uvloop, the latter can double the speed of your async code.

TODO
----

1. add support for common cluster operation
2. support for redis 4.0


Author
------

aredis is developed and maintained by Jason Chen (jason0916phoenix@gmail.com, please use 847671011@qq.com in case your email is not responsed)

It can be found here: https://github.com/NoneGG/aredis

and most its code come from `redis-py <https://github.com/andymccurdy/redis-py>`_ written by Andy McCurdy (sedrik@gmail.com).

.. |travis-status| image:: https://travis-ci.org/NoneGG/aredis.png?branch=master
    :alt: Travis build status
    :scale: 100%
    :target: https://travis-ci.org/NoneGG/aredis

.. |pypi-ver| image::  https://img.shields.io/pypi/v/aredis.svg
    :target: https://pypi.python.org/pypi/aredis/
    :alt: Latest Version in PyPI

.. |python-ver| image:: https://img.shields.io/pypi/pyversions/aredis.svg
    :target: https://pypi.python.org/pypi/aredis/
    :alt: Supported Python versions
