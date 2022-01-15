coredis
=======

.. container:: badges

   .. image:: https://img.shields.io/circleci/project/github/alisaifee/coredis/master.svg?style=flat-square
      :alt: CircleCI build status
      :target: https://circleci.com/gh/alisaifee/coredis/tree/master
      :class: header-badge

   .. image::  https://img.shields.io/pypi/v/coredis.svg?style=flat-square
      :target: https://pypi.python.org/pypi/coredis/
      :alt: Latest Version in PyPI
      :class: header-badge

   .. image:: https://img.shields.io/pypi/pyversions/coredis.svg?style=flat-square
      :target: https://pypi.python.org/pypi/coredis/
      :alt: Supported Python versions
      :class: header-badge

   .. image:: https://codecov.io/gh/alisaifee/coredis/branch/master/graph/badge.svg
      :target: https://codecov.io/gh/alisaifee/coredis
      :alt: Code coverage
      :class: header-badge

coredis is a fork of `aredis <https://github.com/NoneGG/aredis>`_,
an async redis client ported from `redis-py <https://github.com/redis/redis-py>`_

Installation
------------

.. code-block:: bash

    $ pip install coredis

or

.. code-block:: bash

   $ pip install coredis[hiredis]



Getting started
---------------

Single Node client
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import asyncio
    from coredis import StrictRedis

    async def example():
        client = StrictRedis(host='127.0.0.1', port=6379, db=0)
        await client.flushdb()
        await client.set('foo', 1)
        assert await client.exists('foo') is True
        await client.incr('foo', 100)

        assert int(await client.get('foo')) == 101
        await client.expire('foo', 1)
        await asyncio.sleep(0.1)
        await client.ttl('foo')
        await asyncio.sleep(1)
        assert not await client.exists('foo')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())

Cluster client
^^^^^^^^^^^^^^

.. code-block:: python

    import asyncio
    from coredis import StrictRedisCluster

    async def example():
        client = StrictRedisCluster(host='172.17.0.2', port=7001)
        await client.flushdb()
        await client.set('foo', 1)
        await client.lpush('a', 1)
        print(await client.cluster_slots())

        await client.rpoplpush('a', 'b')
        assert await client.rpop('b') == b'1'

    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())

    # {(10923, 16383): [{'host': b'172.17.0.2', 'node_id': b'332f41962b33fa44bbc5e88f205e71276a9d64f4', 'server_type': 'master', 'port': 7002},
    # {'host': b'172.17.0.2', 'node_id': b'c02deb8726cdd412d956f0b9464a88812ef34f03', 'server_type': 'slave', 'port': 7005}],
    # (5461, 10922): [{'host': b'172.17.0.2', 'node_id': b'3d1b020fc46bf7cb2ffc36e10e7d7befca7c5533', 'server_type': 'master', 'port': 7001},
    # {'host': b'172.17.0.2', 'node_id': b'aac4799b65ff35d8dd2ad152a5515d15c0dc8ab7', 'server_type': 'slave', 'port': 7004}],
    # (0, 5460): [{'host': b'172.17.0.2', 'node_id': b'0932215036dc0d908cf662fdfca4d3614f221b01', 'server_type': 'master', 'port': 7000},
    # {'host': b'172.17.0.2', 'node_id': b'f6603ab4cb77e672de23a6361ec165f3a1a2bb42', 'server_type': 'slave', 'port': 7003}]}


Dependencies & supported python versions
----------------------------------------
coredis is tested against redis versions ``5.0.x``, ``6.0.x`` & ``6.2.x``.

hiredis and uvloop can make coredis faster, but it is up to you whether to install them or not.

- :pypi:`hiredis` >= `0.2.0`. Older versions might work but is not tested.
- :pypi:`uvloop` >= `0.8.0`. Older versions might work but is not tested.


Supported python versions
^^^^^^^^^^^^^^^^^^^^^^^^^

- 3.7
- 3.8
- 3.9
- 3.10


The API (mostly) follows :doc:`redis-py <redis-py:index>`. For a full mapping
of redis commands to API methods refer to the :ref:`compatibility:command compatibilty`
section.


Usage Guide
-----------

.. toctree::
    :maxdepth: 2

    api_reference
    pubsub
    sentinel
    scripting
    pipelines
    extra

The Community Guide
-------------------

.. toctree::
    :maxdepth: 2

    compatibility
    api
    release_notes
    testing
    authors
