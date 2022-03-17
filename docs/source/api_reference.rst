API Reference
=============

**TODO**

Typing
^^^^^^
**coredis** provides type hints for the public API. These are tested using
both :pypi:`mypy` and :pypi:`pyright`.

The :class:`Redis` and :class:`RedisCluster` clients are Generic types constrained
by :class:`AnyStr`. The constructors and ``from_url`` factory methods infer
the appropriate specialization automatically.

Without decoding:

.. code-block::

    client = coredis.Redis(
        "localhost", 6379, db=0, decode_responses=False, encoding="utf-8"
    )
    await client.set("string", 1)
    await client.lpush("list", 1)
    await client.hset("hash", {"a": 1})
    await client.sadd("set", "a")
    await client.zadd("sset", {"a": 1.0, "b": 2.0})

    str_response = await client.get("string")
    list_response_ = await client.lrange("list", 0, 1)
    hash_response = await client.hgetall("hash")
    set_response = await client.smembers("set")
    sorted_set_members_only_response = await client.zrange("sset", -1, 1)

    reveal_locals()
    # note: Revealed local types are:
    # note:     client: coredis.client.Redis[builtins.bytes]
    # note:     hash_response: builtins.dict*[builtins.bytes*, builtins.bytes*]
    # note:     list_response_: builtins.list*[builtins.bytes*]
    # note:     set_response: builtins.set*[builtins.bytes*]
    # note:     sorted_set_members_only_response: builtins.tuple*[builtins.bytes*, ...]
    # note:     str_response: builtins.bytes*

With decoding:

.. code-block::

    client = coredis.Redis(
        "localhost", 6379, db=0, decode_responses=True, encoding="utf-8"
    )
    await client.set("string", 1)
    await client.lpush("list", 1)
    await client.hset("hash", {"a": 1})
    await client.sadd("set", "a")
    await client.zadd("sset", {"a": 1.0, "b": 2.0})

    str_response = await client.get("string")
    list_response_ = await client.lrange("list", 0, 1)
    hash_response = await client.hgetall("hash")
    set_response = await client.smembers("set")
    sorted_set_members_only_response = await client.zrange("sset", -1, 1)

    reveal_locals()
    # note: Revealed local types are:
    # note:     client: coredis.client.Redis[builtins.str]
    # note:     hash_response: builtins.dict*[builtins.str*, builtins.str*]
    # note:     list_response_: builtins.list*[builtins.str*]
    # note:     set_response: builtins.set*[builtins.str*]
    # note:     sorted_set_members_only_response: builtins.tuple*[builtins.str*, ...]
    # note:     str_response: builtins.str*

=====================
Runtime Type checking
=====================

.. danger:: Experimental feature

**coredis** optionally wraps all command methods with :pypi:`beartype` decorators to help
detect errors during testing (or if you are b(ea)rave enough, always).

This can be enabled by installing :pypi:`beartype` and setting the :data:`COREDIS_RUNTIME_CHECKS`
environment variable.

As an example:

.. code-block:: bash

    $ COREDIS_RUNTIME_CHECKS=1 python -c "
    import coredis
    import asyncio
    asyncio.new_event_loop().run_until_complete(coredis.Redis().set(1,1))
    """
    Traceback (most recent call last):
      File "<@beartype(coredis.commands.core.CoreCommands.set) at 0x10c403130>", line 33, in set
    beartype.roar.BeartypeCallHintParamViolation: @beartyped coroutine CoreCommands.set() parameter key=1 violates type hint typing.Union[str, bytes], as 1 not str or bytes.


Decoding
^^^^^^^^

Param :paramref:`~coredis.Redis.encoding` and :paramref:`~coredis.Redis.decode_responses`
are used to support response encoding.

``encoding`` is used for specifying with which encoding you want responses to be decoded.
``decode_responses`` is used for tell the client whether responses should be decoded.

If ``decode_responses`` is set to ``True`` and no encoding is specified, client will use ``utf-8`` by default.

Connections
^^^^^^^^^^^

ConnectionPools manage a set of Connection instances. coredis ships with two
types of Connections. The default, Connection, is a normal TCP socket based
connection. The UnixDomainSocketConnection allows for clients running on the
same device as the server to connect via a unix domain socket. To use a
UnixDomainSocketConnection connection, simply pass the unix_socket_path
argument, which is a string to the unix domain socket file. Additionally, make
sure the unixsocket parameter is defined in your redis.conf file. It's
commented out by default.

.. code-block:: python

    r = coredis.Redis(unix_socket_path='/tmp/redis.sock')

You can create your own Connection subclasses as well. This may be useful if
you want to control the socket behavior within an async framework. To
instantiate a client class using your own connection, you need to create
a connection pool, passing your class to the connection_class argument.
Other keyword parameters you pass to the pool will be passed to the class
specified during initialization.

.. code-block:: python

    pool = coredis.ConnectionPool(connection_class=YourConnectionClass,
                                    your_arg='...', ...)

Parsers
^^^^^^^

Parser classes provide a way to control how responses from the Redis server
are parsed. coredis ships with two parser classes, the PythonParser and the
HiredisParser. By default, coredis will attempt to use the HiredisParser if
you have the hiredis module installed and will fallback to the PythonParser
otherwise.

Hiredis is a C library maintained by the core Redis team. Pieter Noordhuis was
kind enough to create Python bindings. Using Hiredis can provide up to a
10x speed improvement in parsing responses from the Redis server. The
performance increase is most noticeable when retrieving many pieces of data,
such as from LRANGE or SMEMBERS operations.


Hiredis is available on PyPI, and can be installed as an extra dependency to
coredis.


.. code-block:: bash

    $ pip install coredis[hiredis]


or

.. code-block:: bash

    $ easy_install coredis[hiredis]

Response Callbacks
^^^^^^^^^^^^^^^^^^

**TODO**
