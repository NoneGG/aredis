aredis
======
|pypi-ver| |travis-status| |python-ver|

An efficient and user-friendly async redis client ported from `redis-py <https://github.com/andymccurdy/redis-py>`_
(which is a Python interface to the Redis key-value)

To get more information please read `full document`_

.. _full document: http://aredis.readthedocs.io/en/latest/

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


Getting started
---------------

`For more example`_

.. _For more example: https://github.com/NoneGG/aredis/tree/master/examples

single node client
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   >>> import asyncio
   >>> from aredis import StrictRedis
   >>>
   >>> async def example():
   >>>      client = StrictRedis(host='127.0.0.1', port=6379, db=0)
   >>>      await client.flushdb()
   >>>      await client.set('foo', 1)
   >>>      assert await client.exists('foo') is True
   >>>      await client.incr('foo', 100)
   >>>
   >>>      assert int(await client.get('foo')) == 101
   >>>      await client.expire('foo', 1)
   >>>      await asyncio.sleep(0.1)
   >>>      await client.ttl('foo')
   >>>      await asyncio.sleep(1)
   >>>      assert not await client.exists('foo')
   >>>
   >>> loop = asyncio.get_event_loop()
   >>> loop.run_until_complete(example())

cluster client
^^^^^^^^^^^^^^

.. code-block:: python

   >>> import asyncio
   >>> from aredis import StrictRedisCluster
   >>>
   >>> async def example():
   >>>      client = StrictRedisCluster(host='172.17.0.2', port=7001)
   >>>      await client.flushdb()
   >>>      await client.set('foo', 1)
   >>>      await client.lpush('a', 1)
   >>>      print(await client.cluster_slots())
   >>>
   >>>      await client.rpoplpush('a', 'b')
   >>>      assert await client.rpop('b') == b'1'
   >>>
   >>> loop = asyncio.get_event_loop()
   >>> loop.run_until_complete(example())
   {(10923, 16383): [{'host': b'172.17.0.2', 'node_id': b'332f41962b33fa44bbc5e88f205e71276a9d64f4', 'server_type': 'master', 'port': 7002},
   {'host': b'172.17.0.2', 'node_id': b'c02deb8726cdd412d956f0b9464a88812ef34f03', 'server_type': 'slave', 'port': 7005}],
   (5461, 10922): [{'host': b'172.17.0.2', 'node_id': b'3d1b020fc46bf7cb2ffc36e10e7d7befca7c5533', 'server_type': 'master', 'port': 7001},
   {'host': b'172.17.0.2', 'node_id': b'aac4799b65ff35d8dd2ad152a5515d15c0dc8ab7', 'server_type': 'slave', 'port': 7004}],
   (0, 5460): [{'host': b'172.17.0.2', 'node_id': b'0932215036dc0d908cf662fdfca4d3614f221b01', 'server_type': 'master', 'port': 7000},
   {'host': b'172.17.0.2', 'node_id': b'f6603ab4cb77e672de23a6361ec165f3a1a2bb42', 'server_type': 'slave', 'port': 7003}]}

Benchmark
---------

Please run test script in benchmarks dir to confirm the benchmark.

For benchmark in my environment please see: `benchmark`_

.. _benchmark: http://aredis.readthedocs.io/en/latest/benchmark.html

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
