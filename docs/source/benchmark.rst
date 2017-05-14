Benchmark
=========
benchmark/comparation.py run on virtual machine(ubuntu, 4G memory and 2 cpu) with hiredis as parser

local redis server
^^^^^^^^^^^^^^^^^^
+-----------------+---------------+--------------+-----------------+----------------+----------------------+---------------------+--------+
|num of query/time|aredis(asyncio)|aredis(uvloop)|aioredis(asyncio)|aioredis(uvloop)|asyncio_redis(asyncio)|asyncio_redis(uvloop)|redis-py|
+=================+===============+==============+=================+================+======================+=====================+========+
|100              | 0.0190        |   0.01802    |     0.0400      |      0.01989   |       0.0391         |        0.0326       | 0.0111 |
+-----------------+---------------+--------------+-----------------+----------------+----------------------+---------------------+--------+
|1000             | 0.0917        |   0.05998    |     0.1237      |      0.05866   |       0.1838         |        0.1397       | 0.0396 |
+-----------------+---------------+--------------+-----------------+----------------+----------------------+---------------------+--------+
|10000            | 1.0614        |   0.66423    |     1.2277      |      0.62957   |       1.9061         |        1.5464       | 0.3944 |
+-----------------+---------------+--------------+-----------------+----------------+----------------------+---------------------+--------+
|100000           | 10.228        |   6.13821    |     10.400      |      6.06872   |       19.982         |        15.252       | 3.6307 |
+-----------------+---------------+--------------+-----------------+----------------+----------------------+---------------------+--------+

redis server in local area network
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Only run with uvloop, or it will be too slow.
Although it seems like that running code in synchronous way perform more well than in asynchronous way,
the point is that it won't block the other code to run.

+-----------------+--------------+----------------+---------------------+--------+
|num of query/time|aredis(uvloop)|aioredis(uvloop)|asyncio_redis(uvloop)|redis-py|
+=================+==============+================+=====================+========+
|100              |   0.06998    |      0.06019   |        0.1971       | 0.0556 |
+-----------------+--------------+----------------+---------------------+--------+
|1000             |   0.66197    |      0.61183   |        1.9330       | 0.7909 |
+-----------------+--------------+----------------+---------------------+--------+
|10000            |   5.81604    |      6.87364   |        19.186       | 7.1334 |
+-----------------+--------------+----------------+---------------------+--------+
|100000           |   58.4715    |      60.9220   |        189.06       | 58.979 |
+-----------------+--------------+----------------+---------------------+--------+

**test result may change according to your computer performance and network (you may run the sheet yourself to determine which one is the most suitable for you)**

Advantage
^^^^^^^^^

1. aredis can be used howerver you install hiredis or not.
2. aredis' API are mostly ported from redis-py, which is easy to use indeed and make it easy to port your code with asyncio
3. according to my test, aredis is efficient enough (please run benchmarks/comparation.py to see which async redis client is suitable for you)
4. aredis can be run both with asyncio and uvloop, the latter can double the speed of your async code.