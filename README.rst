.. |ci| image:: https://github.com/alisaifee/coredis/workflows/CI/badge.svg?branch=master
    :target: https://github.com/alisaifee/coredis/actions?query=branch%3Amaster+workflow%3ACI

.. |pypi-ver| image::  https://img.shields.io/pypi/v/coredis.svg
    :target: https://pypi.python.org/pypi/coredis/
    :alt: Latest Version in PyPI

.. |python-ver| image:: https://img.shields.io/pypi/pyversions/coredis.svg
    :target: https://pypi.python.org/pypi/coredis/
    :alt: Supported Python versions

.. |docs| image:: https://readthedocs.org/projects/coredis/badge/?version=stable
   :target: https://coredis.readthedocs.org

.. |codecov| image:: https://codecov.io/gh/alisaifee/coredis/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/alisaifee/coredis

coredis
=======

|docs| |codecov| |pypi-ver| |ci| |python-ver|

coredis is an async redis client with support for redis server, cluster & sentinel.


Installation
------------

To install coredis:

.. code-block:: bash

    $ pip install coredis[hiredis]

or from source:

.. code-block:: bash

    $ python setup.py install


Getting started
---------------

Single Node client
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import asyncio
    from coredis import Redis

    async def example():
        client = Redis(host='127.0.0.1', port=6379, db=0)
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

    loop = asyncio.new_event_loop()
    loop.run_until_complete(example())

Cluster client
^^^^^^^^^^^^^^

.. code-block:: python

    import asyncio
    from coredis import RedisCluster

    async def example():
        client = RedisCluster(host='172.17.0.2', port=7001)
        await client.flushdb()
        await client.set('foo', 1)
        await client.lpush('a', 1)
        print(await client.cluster_slots())

        await client.rpoplpush('a', 'b')
        assert await client.rpop('b') == b'1'

   loop = asyncio.new_event_loop()
   loop.run_until_complete(example())
   # {(10923, 16383): [{'host': b'172.17.0.2', 'node_id': b'332f41962b33fa44bbc5e88f205e71276a9d64f4', 'server_type': 'master', 'port': 7002},
   # {'host': b'172.17.0.2', 'node_id': b'c02deb8726cdd412d956f0b9464a88812ef34f03', 'server_type': 'slave', 'port': 7005}],
   # (5461, 10922): [{'host': b'172.17.0.2', 'node_id': b'3d1b020fc46bf7cb2ffc36e10e7d7befca7c5533', 'server_type': 'master', 'port': 7001},
   # {'host': b'172.17.0.2', 'node_id': b'aac4799b65ff35d8dd2ad152a5515d15c0dc8ab7', 'server_type': 'slave', 'port': 7004}],
   # (0, 5460): [{'host': b'172.17.0.2', 'node_id': b'0932215036dc0d908cf662fdfca4d3614f221b01', 'server_type': 'master', 'port': 7000},
   # {'host': b'172.17.0.2', 'node_id': b'f6603ab4cb77e672de23a6361ec165f3a1a2bb42', 'server_type': 'slave', 'port': 7003}]}

To see a full list of supported redis commands refer to the `Command compatibility`_  documentation

Links
-----

* `Documentation (Stable) <http://coredis.readthedocs.org/en/stable>`_
* `Documentation (Latest) <http://coredis.readthedocs.org/en/latest>`_
* `Changelog <http://coredis.readthedocs.org/en/stable/release_notes.html>`_

.. _Command compatibility: https://coredis.readthedocs.io/en/stable/compatibility.html
