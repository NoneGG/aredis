Testing
=======

StrictRedis
-----------

All tests are built on the base of simplest redis server with default config.

Redis server setup
^^^^^^^^^^^^^^^^^^

To test against the latest stable redis server from source, use:

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

You can also use any version of Redis installed from your OS package manager (example for OSX: ``brew install redis``), in which case starting the server is as simple as running:

.. code-block:: bash

    $ redis-server


StrictRedisCluster
------------------

All tests are currently built around a 6 redis server cluster setup (3 masters + 3 slaves).
One server must be using port 7000 for redis cluster discovery.
The easiest way to setup a cluster is to use Docker.


Redis cluster setup
^^^^^^^^^^^^^^^^^^^

A fully functional docker image can be found at https://github.com/Grokzen/docker-redis-cluster

To turn on a cluster which should pass all tests, run:

.. code-block:: bash

    $ docker run --rm -it -p7000:7000 -p7001:7001 -p7002:7002 -p7003:7003 -p7004:7004 -p7005:7005 -e IP='0.0.0.0' grokzen/redis-cluster:latest


Run test
--------

To run test you should install dependency firstly.

.. code-block:: bash

    $ pip install -r requirements/dev.txt
    $ pytest tests/
