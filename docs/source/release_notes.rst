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
