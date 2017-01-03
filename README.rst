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

API Reference
^^^^^^^^^^^^^

The connection part is rewritten to make client async, and most API is ported from redis-py.
So most API and usage are the same as redis-py.
If you use redis-py in your code, just use async/await syntax with your code.

* iter functions are not supported now

* doc in detail is coming soon


Advantage
^^^^^^^^^

1. aredis can be used howerver you install hiredis or not.
2. aredis' API are mostly ported from redis-py, which is easy to use indeed and make it easy to port your code with asyncio
3. according to my test, aredis is efficient enough (please run benchmarks/comparation.py to see which async redis client is suitable for you)
4. aredis can be run both with asyncio and uvloop, the latter can double the speed of your async code.

Disadvantage & TODO
^^^^^^^^^^^^^^^^^^^

1. the package only support Python 3.5 and above
2. the encode part is not supported very well now (will try to fix it in next version)
3. iter functions are not supported now (will be added in Python 3.6)


Author
^^^^^^

aredis is developed and maintained by Jason Chen (jason0916phoenix@gmail.com, please use 847671011@qq.com in case your email is not responsed)

It can be found here: https://github.com/NoneGG/aredis

and most its code come from redis-py written by Andy McCurdy (sedrik@gmail.com).

It can be found here: http://github.com/andymccurdy/redis-py
