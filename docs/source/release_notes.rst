Release Notes
=============

master
------

    * add TCP Keep-alive support by passing use the `socket_keepalive=True`
      option. Finer grain control can be achieved using the
      `socket_keepalive_options` option which expects a dictionary with any of
      the keys (`socket.TCP_KEEPIDLE`, `socket.TCP_KEEPCNT`, `socket.TCP_KEEPINTVL`)
      and integers for values. Thanks Stefan Tjarks.

1.0.1
-----

    * add scan_iter, sscan_iter, hscan_iter, zscan_iter and corresponding unit tests
    * fix bug of `PubSub.run_in_thread`
    * add more examples
    * change `Script.register` to `Script.execute`

1.0.2
-----
    * add support for cache (Cache and HerdCache class)
    * fix bug of `PubSub.run_in_thread`

1.0.4
-----
    * add support for command `pubsub channel`, `pubsub numpat` and `pubsub numsub`
    * add support for command `client pause`
    * reconsitution of commands to make develop easier(which is transparent to user)

1.0.5
-----
    * fix bug in setup.py when using pip to install aredis

1.0.6
-----
    * bitfield set/get/incrby/overflow supported
    * new command `hstrlen` supported
    * new command `unlink` supported
    * new command `touch` supported

1.0.7
-----
    * introduce loop argument to aredis
    * add support for command `cluster slots`
    * add support for redis cluster

1.0.8
-----
    * fix initialization bug of redis cluster client
    * add example to explain how to use `client reply on | off | skip`

1.0.9
-----
    * fix bug of pubsub, in some env AssertionError is raised because connection is used again after reader stream being fed eof
    * add reponse decoding related options(`encoding` & `decode_responses`), make client easier to use
    * add support for command `cluster forget`
    * add support for command option `spop count`

1.1.0
-----
    * sync optimization of scripting from redis-py made by `bgreenberg <https://github.com/bgreenberg-eb>`_ `related pull request <https://github.com/andymccurdy/redis-py/pull/867>`_
    * sync bug fixed of `geopos` from redis-py made by `categulario <https://github.com/categulario>`_ `related pull request <https://github.com/andymccurdy/redis-py/pull/888>`_
    * fix bug which makes pipeline callback function not executed
    * fix error caused by byte decode issues in sentinel
    * add basic transaction support for single node in cluster
    * fix bug of get_random_connection reported by myrfy001

1.1.1
-----
    * fix bug: connection with unread response being released to connection pool will lead to parse error, now this kind of connection will be destructed directly. `related issue <https://github.com/NoneGG/aredis/issues/52>`_
    * fix bug: remove Connection.can_read check which may lead to block in awaiting pubsub message. Connection.can_read api will be deprecated in next release. `related issue <https://github.com/NoneGG/aredis/issues/56>`_
    * add c extension to speedup crc16, which will speedup cluster slot hashing
    * add error handling for asyncio.futures.Cancelled error, which may cause error in response parsing.
    * sync optimization of client list made by swilly22 from redis-py
    * add support for distributed lock using redis cluster

1.1.2
-----
    * fix bug: redis command encoding bug
    * optimization: sync change on acquring lock from redis-py
    * fix bug: decrement connection count on connection disconnected
    * fix bug: optimize code proceed single node slots
    * fix bug: initiation error of aws cluster client caused by not appropiate function list used
    * fix bug: use `ssl_context` instead of ssl_keyfile,ssl_certfile,ssl_cert_reqs,ssl_ca_certs in intialization of connection_pool

1.1.3
-----
    * allow use of zadd options for zadd in sorted sets
    * fix bug: use inspect.isawaitable instead of typing.Awaitable to judge if an object is awaitable
    * fix bug: implicitly disconnection on cancelled error (#84)
    * new: add support for `streams`(including commands not officially released, see `streams <http://aredis.readthedocs.io/en/latest/streams.html>`_ )

1.1.4
-----
    * fix bug: fix cluster port parsing for redis 4+(node info)
    * fix bug: wrong parse method of scan_iter in cluster mode
    * fix bug: When using "zrange" with "desc=True" parameter, it returns a coroutine without "await"
    * fix bug: do not use stream_timeout in the PubSubWorkerThread
    * opt: add socket_keepalive options
    * new: add ssl param in get_redis_link to support ssl mode
    * new: add ssl_context to StrictRedis constructor and make it higher priority than ssl parameter
