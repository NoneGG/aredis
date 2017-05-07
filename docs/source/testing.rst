Testing
=======

StrictRedis
-----------

All tests are built on the base of simplest redis server with default config.

Redis server setup
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    $ sudo apt-get update
    $ sudo apt-get install build-essential
    $ sudo apt-get install tcl8.5
    $ wget http://download.redis.io/releases/redis-stable.tar.gz
    $ tar xzf redis-stable.tar.gz
    $ cd redis-stable
    $ make test
    $ make install
    $ sudo utils/install_server.sh
    $ sudo service redis_6379 start


StrictRedisCluster
------------------

All tests are currently built around a 6 redis server cluster setup (3 masters + 3 slaves).
One server must be using port 7000 for redis cluster discovery.
The easiest way to setup a cluster is to use Docker.


Redis cluster setup
^^^^^^^^^^^^^^^^^^^

A fully functional docker image can be found at https://github.com/Grokzen/docker-redis-cluster

Run test
--------

To run test you should install dependency firstly.

.. code-block:: bash

    $ pip install -r dev_requirements.txt
    $ pytest tests/
