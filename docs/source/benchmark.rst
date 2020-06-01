Benchmark
=========
During test benchmarks/comparison.py ran on a virtual machine (Ubuntu, 4G RAM and 2 CPUs) with hiredis installed.

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
Although synchronous code may perform better than in asynchronous, asynchronous won't block other code.

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

**test results may differ depending on your workstation and networking hardware (you may run the benchmark yourself to determine which one is the most suitable for you)**

Advantages
^^^^^^^^^^

1. hiredis is an optional dependency for aredis.
2. API of aredis was mostly ported from redis-py, which is easy to use. It lets you easily port existing code to work with asyncio.
3. aredis has a decent efficiency (please run benchmarks/comparison.py to see which async redis client is suitable for you).
4. uvloop evant loop is supported by aredis, it can double the speed of your async code.
