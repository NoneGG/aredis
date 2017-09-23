Release Notes
=============

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

