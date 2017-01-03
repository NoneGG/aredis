aredis
======

An async version of `redis-py <https://github.com/andymccurdy/redis-py>`_
(which is a Python interface to the Redis key-value store).

.. image:: https://secure.travis-ci.org/NoneGG/aredis.png?branch=master
        :target: http://travis-ci.org/NoneGG/aredis

Installation
------------

aredis requires a running Redis server.

To install redis-py, simply:

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
