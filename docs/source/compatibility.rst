Command compatibilty
==========================
Redis
^^^^^

String
------

.. list-table::
    :class: command-table

    * - `APPEND <https://redis.io/commands/append>`_
      - :meth:`~coredis.StrictRedis.append`
    * - `DECR <https://redis.io/commands/decr>`_
      - :meth:`~coredis.StrictRedis.decr`
    * - `GET <https://redis.io/commands/get>`_
      - :meth:`~coredis.StrictRedis.get`
    * - `GETRANGE <https://redis.io/commands/getrange>`_
      - :meth:`~coredis.StrictRedis.getrange`
    * - `GETSET <https://redis.io/commands/getset>`_
      - :meth:`~coredis.StrictRedis.getset`
    * - `INCR <https://redis.io/commands/incr>`_
      - :meth:`~coredis.StrictRedis.incr`
    * - `INCRBY <https://redis.io/commands/incrby>`_
      - :meth:`~coredis.StrictRedis.incrby`
    * - `INCRBYFLOAT <https://redis.io/commands/incrbyfloat>`_
      - :meth:`~coredis.StrictRedis.incrbyfloat`
    * - `MGET <https://redis.io/commands/mget>`_
      - :meth:`~coredis.StrictRedis.mget`
    * - `MSET <https://redis.io/commands/mset>`_
      - :meth:`~coredis.StrictRedis.mset`
    * - `MSETNX <https://redis.io/commands/msetnx>`_
      - :meth:`~coredis.StrictRedis.msetnx`
    * - `PSETEX <https://redis.io/commands/psetex>`_
      - :meth:`~coredis.StrictRedis.psetex`
    * - `SET <https://redis.io/commands/set>`_
      - :meth:`~coredis.StrictRedis.set`
    * - `SETEX <https://redis.io/commands/setex>`_
      - :meth:`~coredis.StrictRedis.setex`
    * - `SETNX <https://redis.io/commands/setnx>`_
      - :meth:`~coredis.StrictRedis.setnx`
    * - `SETRANGE <https://redis.io/commands/setrange>`_
      - :meth:`~coredis.StrictRedis.setrange`
    * - `STRLEN <https://redis.io/commands/strlen>`_
      - :meth:`~coredis.StrictRedis.strlen`
    * - `SUBSTR <https://redis.io/commands/substr>`_
      - :meth:`~coredis.StrictRedis.substr`
    * - `DECRBY <https://redis.io/commands/decrby>`_
      - Needs porting from: :meth:`Redis.decrby`
    * - `GETDEL <https://redis.io/commands/getdel>`_
      - Needs porting from: :meth:`Redis.getdel`
    * - `GETEX <https://redis.io/commands/getex>`_
      - Needs porting from: :meth:`Redis.getex`
Bitmap
------

.. list-table::
    :class: command-table

    * - `BITCOUNT <https://redis.io/commands/bitcount>`_
      - :meth:`~coredis.StrictRedis.bitcount`
    * - `BITFIELD <https://redis.io/commands/bitfield>`_
      - :meth:`~coredis.StrictRedis.bitfield`
    * - `BITOP <https://redis.io/commands/bitop>`_
      - :meth:`~coredis.StrictRedis.bitop`
    * - `BITPOS <https://redis.io/commands/bitpos>`_
      - :meth:`~coredis.StrictRedis.bitpos`
    * - `GETBIT <https://redis.io/commands/getbit>`_
      - :meth:`~coredis.StrictRedis.getbit`
    * - `SETBIT <https://redis.io/commands/setbit>`_
      - :meth:`~coredis.StrictRedis.setbit`
List
----

.. list-table::
    :class: command-table

    * - `BLPOP <https://redis.io/commands/blpop>`_
      - :meth:`~coredis.StrictRedis.blpop`
    * - `BRPOP <https://redis.io/commands/brpop>`_
      - :meth:`~coredis.StrictRedis.brpop`
    * - `BRPOPLPUSH <https://redis.io/commands/brpoplpush>`_
      - :meth:`~coredis.StrictRedis.brpoplpush`
    * - `LINDEX <https://redis.io/commands/lindex>`_
      - :meth:`~coredis.StrictRedis.lindex`
    * - `LINSERT <https://redis.io/commands/linsert>`_
      - :meth:`~coredis.StrictRedis.linsert`
    * - `LLEN <https://redis.io/commands/llen>`_
      - :meth:`~coredis.StrictRedis.llen`
    * - `LPOP <https://redis.io/commands/lpop>`_
      - :meth:`~coredis.StrictRedis.lpop`
    * - `LPUSH <https://redis.io/commands/lpush>`_
      - :meth:`~coredis.StrictRedis.lpush`
    * - `LPUSHX <https://redis.io/commands/lpushx>`_
      - :meth:`~coredis.StrictRedis.lpushx`
    * - `LRANGE <https://redis.io/commands/lrange>`_
      - :meth:`~coredis.StrictRedis.lrange`
    * - `LREM <https://redis.io/commands/lrem>`_
      - :meth:`~coredis.StrictRedis.lrem`
    * - `LSET <https://redis.io/commands/lset>`_
      - :meth:`~coredis.StrictRedis.lset`
    * - `LTRIM <https://redis.io/commands/ltrim>`_
      - :meth:`~coredis.StrictRedis.ltrim`
    * - `RPOP <https://redis.io/commands/rpop>`_
      - :meth:`~coredis.StrictRedis.rpop`
    * - `RPOPLPUSH <https://redis.io/commands/rpoplpush>`_
      - :meth:`~coredis.StrictRedis.rpoplpush`
    * - `RPUSH <https://redis.io/commands/rpush>`_
      - :meth:`~coredis.StrictRedis.rpush`
    * - `RPUSHX <https://redis.io/commands/rpushx>`_
      - :meth:`~coredis.StrictRedis.rpushx`
    * - `BLMOVE <https://redis.io/commands/blmove>`_
      - Needs porting from: :meth:`Redis.blmove`
    * - `LMOVE <https://redis.io/commands/lmove>`_
      - Needs porting from: :meth:`Redis.lmove`
    * - `LPOS <https://redis.io/commands/lpos>`_
      - Needs porting from: :meth:`Redis.lpos`
Sorted-Set
----------

.. list-table::
    :class: command-table

    * - `ZADD <https://redis.io/commands/zadd>`_
      - :meth:`~coredis.StrictRedis.zadd`
    * - `ZCARD <https://redis.io/commands/zcard>`_
      - :meth:`~coredis.StrictRedis.zcard`
    * - `ZCOUNT <https://redis.io/commands/zcount>`_
      - :meth:`~coredis.StrictRedis.zcount`
    * - `ZINCRBY <https://redis.io/commands/zincrby>`_
      - :meth:`~coredis.StrictRedis.zincrby`
    * - `ZINTERSTORE <https://redis.io/commands/zinterstore>`_
      - :meth:`~coredis.StrictRedis.zinterstore`
    * - `ZLEXCOUNT <https://redis.io/commands/zlexcount>`_
      - :meth:`~coredis.StrictRedis.zlexcount`
    * - `ZRANGE <https://redis.io/commands/zrange>`_
      - :meth:`~coredis.StrictRedis.zrange`
    * - `ZRANGEBYLEX <https://redis.io/commands/zrangebylex>`_
      - :meth:`~coredis.StrictRedis.zrangebylex`
    * - `ZRANGEBYSCORE <https://redis.io/commands/zrangebyscore>`_
      - :meth:`~coredis.StrictRedis.zrangebyscore`
    * - `ZRANK <https://redis.io/commands/zrank>`_
      - :meth:`~coredis.StrictRedis.zrank`
    * - `ZREM <https://redis.io/commands/zrem>`_
      - :meth:`~coredis.StrictRedis.zrem`
    * - `ZREMRANGEBYLEX <https://redis.io/commands/zremrangebylex>`_
      - :meth:`~coredis.StrictRedis.zremrangebylex`
    * - `ZREMRANGEBYRANK <https://redis.io/commands/zremrangebyrank>`_
      - :meth:`~coredis.StrictRedis.zremrangebyrank`
    * - `ZREMRANGEBYSCORE <https://redis.io/commands/zremrangebyscore>`_
      - :meth:`~coredis.StrictRedis.zremrangebyscore`
    * - `ZREVRANGE <https://redis.io/commands/zrevrange>`_
      - :meth:`~coredis.StrictRedis.zrevrange`
    * - `ZREVRANGEBYLEX <https://redis.io/commands/zrevrangebylex>`_
      - :meth:`~coredis.StrictRedis.zrevrangebylex`
    * - `ZREVRANGEBYSCORE <https://redis.io/commands/zrevrangebyscore>`_
      - :meth:`~coredis.StrictRedis.zrevrangebyscore`
    * - `ZREVRANK <https://redis.io/commands/zrevrank>`_
      - :meth:`~coredis.StrictRedis.zrevrank`
    * - `ZSCAN <https://redis.io/commands/zscan>`_
      - :meth:`~coredis.StrictRedis.zscan`
    * - `ZSCORE <https://redis.io/commands/zscore>`_
      - :meth:`~coredis.StrictRedis.zscore`
    * - `ZUNIONSTORE <https://redis.io/commands/zunionstore>`_
      - :meth:`~coredis.StrictRedis.zunionstore`
    * - `BZPOPMAX <https://redis.io/commands/bzpopmax>`_
      - Needs porting from: :meth:`Redis.bzpopmax`
    * - `BZPOPMIN <https://redis.io/commands/bzpopmin>`_
      - Needs porting from: :meth:`Redis.bzpopmin`
    * - `ZDIFF <https://redis.io/commands/zdiff>`_
      - Needs porting from: :meth:`Redis.zdiff`
    * - `ZDIFFSTORE <https://redis.io/commands/zdiffstore>`_
      - Needs porting from: :meth:`Redis.zdiffstore`
    * - `ZINTER <https://redis.io/commands/zinter>`_
      - Needs porting from: :meth:`Redis.zinter`
    * - `ZMSCORE <https://redis.io/commands/zmscore>`_
      - Needs porting from: :meth:`Redis.zmscore`
    * - `ZPOPMAX <https://redis.io/commands/zpopmax>`_
      - Needs porting from: :meth:`Redis.zpopmax`
    * - `ZPOPMIN <https://redis.io/commands/zpopmin>`_
      - Needs porting from: :meth:`Redis.zpopmin`
    * - `ZRANDMEMBER <https://redis.io/commands/zrandmember>`_
      - Needs porting from: :meth:`Redis.zrandmember`
    * - `ZRANGESTORE <https://redis.io/commands/zrangestore>`_
      - Needs porting from: :meth:`Redis.zrangestore`
    * - `ZUNION <https://redis.io/commands/zunion>`_
      - Needs porting from: :meth:`Redis.zunion`
Generic
-------

.. list-table::
    :class: command-table

    * - `DUMP <https://redis.io/commands/dump>`_
      - :meth:`~coredis.StrictRedis.dump`
    * - `EXISTS <https://redis.io/commands/exists>`_
      - :meth:`~coredis.StrictRedis.exists`
    * - `EXPIRE <https://redis.io/commands/expire>`_
      - :meth:`~coredis.StrictRedis.expire`
    * - `EXPIREAT <https://redis.io/commands/expireat>`_
      - :meth:`~coredis.StrictRedis.expireat`
    * - `KEYS <https://redis.io/commands/keys>`_
      - :meth:`~coredis.StrictRedis.keys`
    * - `MOVE <https://redis.io/commands/move>`_
      - :meth:`~coredis.StrictRedis.move`
    * - `OBJECT <https://redis.io/commands/object>`_
      - :meth:`~coredis.StrictRedis.object`
    * - `PERSIST <https://redis.io/commands/persist>`_
      - :meth:`~coredis.StrictRedis.persist`
    * - `PEXPIRE <https://redis.io/commands/pexpire>`_
      - :meth:`~coredis.StrictRedis.pexpire`
    * - `PEXPIREAT <https://redis.io/commands/pexpireat>`_
      - :meth:`~coredis.StrictRedis.pexpireat`
    * - `PTTL <https://redis.io/commands/pttl>`_
      - :meth:`~coredis.StrictRedis.pttl`
    * - `RANDOMKEY <https://redis.io/commands/randomkey>`_
      - :meth:`~coredis.StrictRedis.randomkey`
    * - `RENAME <https://redis.io/commands/rename>`_
      - :meth:`~coredis.StrictRedis.rename`
    * - `RENAMENX <https://redis.io/commands/renamenx>`_
      - :meth:`~coredis.StrictRedis.renamenx`
    * - `RESTORE <https://redis.io/commands/restore>`_
      - :meth:`~coredis.StrictRedis.restore`
    * - `SCAN <https://redis.io/commands/scan>`_
      - :meth:`~coredis.StrictRedis.scan`
    * - `SORT <https://redis.io/commands/sort>`_
      - :meth:`~coredis.StrictRedis.sort`
    * - `TOUCH <https://redis.io/commands/touch>`_
      - :meth:`~coredis.StrictRedis.touch`
    * - `TTL <https://redis.io/commands/ttl>`_
      - :meth:`~coredis.StrictRedis.ttl`
    * - `TYPE <https://redis.io/commands/type>`_
      - :meth:`~coredis.StrictRedis.type`
    * - `UNLINK <https://redis.io/commands/unlink>`_
      - :meth:`~coredis.StrictRedis.unlink`
    * - `WAIT <https://redis.io/commands/wait>`_
      - :meth:`~coredis.StrictRedis.wait`
    * - `COPY <https://redis.io/commands/copy>`_
      - Needs porting from: :meth:`Redis.copy`
    * - `MIGRATE <https://redis.io/commands/migrate>`_
      - Needs porting from: :meth:`Redis.migrate`
Transactions
------------

.. list-table::
    :class: command-table

    * - `UNWATCH <https://redis.io/commands/unwatch>`_
      - :meth:`~coredis.StrictRedis.unwatch`
    * - `WATCH <https://redis.io/commands/watch>`_
      - :meth:`~coredis.StrictRedis.watch`
Scripting
---------

.. list-table::
    :class: command-table

    * - `EVAL <https://redis.io/commands/eval>`_
      - :meth:`~coredis.StrictRedis.eval`
    * - `EVALSHA <https://redis.io/commands/evalsha>`_
      - :meth:`~coredis.StrictRedis.evalsha`
    * - `SCRIPT EXISTS <https://redis.io/commands/script-exists>`_
      - :meth:`~coredis.StrictRedis.script_exists`
    * - `SCRIPT FLUSH <https://redis.io/commands/script-flush>`_
      - :meth:`~coredis.StrictRedis.script_flush`
    * - `SCRIPT KILL <https://redis.io/commands/script-kill>`_
      - :meth:`~coredis.StrictRedis.script_kill`
    * - `SCRIPT LOAD <https://redis.io/commands/script-load>`_
      - :meth:`~coredis.StrictRedis.script_load`
    * - `SCRIPT DEBUG <https://redis.io/commands/script-debug>`_
      - Needs porting from: :meth:`Redis.script_debug`
Geo
---

.. list-table::
    :class: command-table

    * - `GEOADD <https://redis.io/commands/geoadd>`_
      - :meth:`~coredis.StrictRedis.geoadd`
    * - `GEODIST <https://redis.io/commands/geodist>`_
      - :meth:`~coredis.StrictRedis.geodist`
    * - `GEOHASH <https://redis.io/commands/geohash>`_
      - :meth:`~coredis.StrictRedis.geohash`
    * - `GEOPOS <https://redis.io/commands/geopos>`_
      - :meth:`~coredis.StrictRedis.geopos`
    * - `GEORADIUS <https://redis.io/commands/georadius>`_
      - :meth:`~coredis.StrictRedis.georadius`
    * - `GEORADIUSBYMEMBER <https://redis.io/commands/georadiusbymember>`_
      - :meth:`~coredis.StrictRedis.georadiusbymember`
    * - `GEOSEARCH <https://redis.io/commands/geosearch>`_
      - Needs porting from: :meth:`Redis.geosearch`
    * - `GEOSEARCHSTORE <https://redis.io/commands/geosearchstore>`_
      - Needs porting from: :meth:`Redis.geosearchstore`
Hash
----

.. list-table::
    :class: command-table

    * - `HDEL <https://redis.io/commands/hdel>`_
      - :meth:`~coredis.StrictRedis.hdel`
    * - `HEXISTS <https://redis.io/commands/hexists>`_
      - :meth:`~coredis.StrictRedis.hexists`
    * - `HGET <https://redis.io/commands/hget>`_
      - :meth:`~coredis.StrictRedis.hget`
    * - `HGETALL <https://redis.io/commands/hgetall>`_
      - :meth:`~coredis.StrictRedis.hgetall`
    * - `HINCRBY <https://redis.io/commands/hincrby>`_
      - :meth:`~coredis.StrictRedis.hincrby`
    * - `HINCRBYFLOAT <https://redis.io/commands/hincrbyfloat>`_
      - :meth:`~coredis.StrictRedis.hincrbyfloat`
    * - `HKEYS <https://redis.io/commands/hkeys>`_
      - :meth:`~coredis.StrictRedis.hkeys`
    * - `HLEN <https://redis.io/commands/hlen>`_
      - :meth:`~coredis.StrictRedis.hlen`
    * - `HMGET <https://redis.io/commands/hmget>`_
      - :meth:`~coredis.StrictRedis.hmget`
    * - `HMSET <https://redis.io/commands/hmset>`_
      - :meth:`~coredis.StrictRedis.hmset`
    * - `HSCAN <https://redis.io/commands/hscan>`_
      - :meth:`~coredis.StrictRedis.hscan`
    * - `HSET <https://redis.io/commands/hset>`_
      - :meth:`~coredis.StrictRedis.hset`
    * - `HSETNX <https://redis.io/commands/hsetnx>`_
      - :meth:`~coredis.StrictRedis.hsetnx`
    * - `HSTRLEN <https://redis.io/commands/hstrlen>`_
      - :meth:`~coredis.StrictRedis.hstrlen`
    * - `HVALS <https://redis.io/commands/hvals>`_
      - :meth:`~coredis.StrictRedis.hvals`
    * - `HRANDFIELD <https://redis.io/commands/hrandfield>`_
      - Needs porting from: :meth:`Redis.hrandfield`
Hyperloglog
-----------

.. list-table::
    :class: command-table

    * - `PFADD <https://redis.io/commands/pfadd>`_
      - :meth:`~coredis.StrictRedis.pfadd`
    * - `PFCOUNT <https://redis.io/commands/pfcount>`_
      - :meth:`~coredis.StrictRedis.pfcount`
    * - `PFMERGE <https://redis.io/commands/pfmerge>`_
      - :meth:`~coredis.StrictRedis.pfmerge`
Pubsub
------

.. list-table::
    :class: command-table

    * - `PUBLISH <https://redis.io/commands/publish>`_
      - :meth:`~coredis.StrictRedis.publish`
    * - `PUBSUB <https://redis.io/commands/pubsub>`_
      - :meth:`~coredis.StrictRedis.pubsub`
    * - `PUBSUB CHANNELS <https://redis.io/commands/pubsub-channels>`_
      - :meth:`~coredis.StrictRedis.pubsub_channels`
    * - `PUBSUB NUMPAT <https://redis.io/commands/pubsub-numpat>`_
      - :meth:`~coredis.StrictRedis.pubsub_numpat`
    * - `PUBSUB NUMSUB <https://redis.io/commands/pubsub-numsub>`_
      - :meth:`~coredis.StrictRedis.pubsub_numsub`
Set
---

.. list-table::
    :class: command-table

    * - `SADD <https://redis.io/commands/sadd>`_
      - :meth:`~coredis.StrictRedis.sadd`
    * - `SCARD <https://redis.io/commands/scard>`_
      - :meth:`~coredis.StrictRedis.scard`
    * - `SDIFF <https://redis.io/commands/sdiff>`_
      - :meth:`~coredis.StrictRedis.sdiff`
    * - `SDIFFSTORE <https://redis.io/commands/sdiffstore>`_
      - :meth:`~coredis.StrictRedis.sdiffstore`
    * - `SINTER <https://redis.io/commands/sinter>`_
      - :meth:`~coredis.StrictRedis.sinter`
    * - `SINTERSTORE <https://redis.io/commands/sinterstore>`_
      - :meth:`~coredis.StrictRedis.sinterstore`
    * - `SISMEMBER <https://redis.io/commands/sismember>`_
      - :meth:`~coredis.StrictRedis.sismember`
    * - `SMEMBERS <https://redis.io/commands/smembers>`_
      - :meth:`~coredis.StrictRedis.smembers`
    * - `SMOVE <https://redis.io/commands/smove>`_
      - :meth:`~coredis.StrictRedis.smove`
    * - `SPOP <https://redis.io/commands/spop>`_
      - :meth:`~coredis.StrictRedis.spop`
    * - `SRANDMEMBER <https://redis.io/commands/srandmember>`_
      - :meth:`~coredis.StrictRedis.srandmember`
    * - `SREM <https://redis.io/commands/srem>`_
      - :meth:`~coredis.StrictRedis.srem`
    * - `SSCAN <https://redis.io/commands/sscan>`_
      - :meth:`~coredis.StrictRedis.sscan`
    * - `SUNION <https://redis.io/commands/sunion>`_
      - :meth:`~coredis.StrictRedis.sunion`
    * - `SUNIONSTORE <https://redis.io/commands/sunionstore>`_
      - :meth:`~coredis.StrictRedis.sunionstore`
    * - `SMISMEMBER <https://redis.io/commands/smismember>`_
      - Needs porting from: :meth:`Redis.smismember`
Stream
------

.. list-table::
    :class: command-table

    * - `XACK <https://redis.io/commands/xack>`_
      - :meth:`~coredis.StrictRedis.xack`
    * - `XADD <https://redis.io/commands/xadd>`_
      - :meth:`~coredis.StrictRedis.xadd`
    * - `XCLAIM <https://redis.io/commands/xclaim>`_
      - :meth:`~coredis.StrictRedis.xclaim`
    * - `XDEL <https://redis.io/commands/xdel>`_
      - :meth:`~coredis.StrictRedis.xdel`
    * - `XGROUP CREATE <https://redis.io/commands/xgroup-create>`_
      - :meth:`~coredis.StrictRedis.xgroup_create`
    * - `XGROUP DESTROY <https://redis.io/commands/xgroup-destroy>`_
      - :meth:`~coredis.StrictRedis.xgroup_destroy`
    * - `XINFO CONSUMERS <https://redis.io/commands/xinfo-consumers>`_
      - :meth:`~coredis.StrictRedis.xinfo_consumers`
    * - `XINFO GROUPS <https://redis.io/commands/xinfo-groups>`_
      - :meth:`~coredis.StrictRedis.xinfo_groups`
    * - `XINFO STREAM <https://redis.io/commands/xinfo-stream>`_
      - :meth:`~coredis.StrictRedis.xinfo_stream`
    * - `XLEN <https://redis.io/commands/xlen>`_
      - :meth:`~coredis.StrictRedis.xlen`
    * - `XPENDING <https://redis.io/commands/xpending>`_
      - :meth:`~coredis.StrictRedis.xpending`
    * - `XRANGE <https://redis.io/commands/xrange>`_
      - :meth:`~coredis.StrictRedis.xrange`
    * - `XREAD <https://redis.io/commands/xread>`_
      - :meth:`~coredis.StrictRedis.xread`
    * - `XREADGROUP <https://redis.io/commands/xreadgroup>`_
      - :meth:`~coredis.StrictRedis.xreadgroup`
    * - `XREVRANGE <https://redis.io/commands/xrevrange>`_
      - :meth:`~coredis.StrictRedis.xrevrange`
    * - `XTRIM <https://redis.io/commands/xtrim>`_
      - :meth:`~coredis.StrictRedis.xtrim`
    * - `XAUTOCLAIM <https://redis.io/commands/xautoclaim>`_
      - Needs porting from: :meth:`Redis.xautoclaim`
    * - `XGROUP CREATECONSUMER <https://redis.io/commands/xgroup-createconsumer>`_
      - Needs porting from: :meth:`Redis.xgroup_createconsumer`
    * - `XGROUP DELCONSUMER <https://redis.io/commands/xgroup-delconsumer>`_
      - Needs porting from: :meth:`Redis.xgroup_delconsumer`
    * - `XGROUP SETID <https://redis.io/commands/xgroup-setid>`_
      - Needs porting from: :meth:`Redis.xgroup_setid`
Server
------

.. list-table::
    :class: command-table

    * - `BGREWRITEAOF <https://redis.io/commands/bgrewriteaof>`_
      - :meth:`~coredis.StrictRedis.bgrewriteaof`
    * - `BGSAVE <https://redis.io/commands/bgsave>`_
      - :meth:`~coredis.StrictRedis.bgsave`
    * - `CONFIG GET <https://redis.io/commands/config-get>`_
      - :meth:`~coredis.StrictRedis.config_get`
    * - `CONFIG RESETSTAT <https://redis.io/commands/config-resetstat>`_
      - :meth:`~coredis.StrictRedis.config_resetstat`
    * - `CONFIG REWRITE <https://redis.io/commands/config-rewrite>`_
      - :meth:`~coredis.StrictRedis.config_rewrite`
    * - `CONFIG SET <https://redis.io/commands/config-set>`_
      - :meth:`~coredis.StrictRedis.config_set`
    * - `DBSIZE <https://redis.io/commands/dbsize>`_
      - :meth:`~coredis.StrictRedis.dbsize`
    * - `FLUSHALL <https://redis.io/commands/flushall>`_
      - :meth:`~coredis.StrictRedis.flushall`
    * - `FLUSHDB <https://redis.io/commands/flushdb>`_
      - :meth:`~coredis.StrictRedis.flushdb`
    * - `INFO <https://redis.io/commands/info>`_
      - :meth:`~coredis.StrictRedis.info`
    * - `LASTSAVE <https://redis.io/commands/lastsave>`_
      - :meth:`~coredis.StrictRedis.lastsave`
    * - `ROLE <https://redis.io/commands/role>`_
      - :meth:`~coredis.StrictRedis.role`
    * - `SAVE <https://redis.io/commands/save>`_
      - :meth:`~coredis.StrictRedis.save`
    * - `SHUTDOWN <https://redis.io/commands/shutdown>`_
      - :meth:`~coredis.StrictRedis.shutdown`
    * - `SLAVEOF <https://redis.io/commands/slaveof>`_
      - :meth:`~coredis.StrictRedis.slaveof`
    * - `SLOWLOG GET <https://redis.io/commands/slowlog-get>`_
      - :meth:`~coredis.StrictRedis.slowlog_get`
    * - `SLOWLOG LEN <https://redis.io/commands/slowlog-len>`_
      - :meth:`~coredis.StrictRedis.slowlog_len`
    * - `SLOWLOG RESET <https://redis.io/commands/slowlog-reset>`_
      - :meth:`~coredis.StrictRedis.slowlog_reset`
    * - `TIME <https://redis.io/commands/time>`_
      - :meth:`~coredis.StrictRedis.time`
    * - `ACL CAT <https://redis.io/commands/acl-cat>`_
      - Needs porting from: :meth:`Redis.acl_cat`
    * - `ACL DELUSER <https://redis.io/commands/acl-deluser>`_
      - Needs porting from: :meth:`Redis.acl_deluser`
    * - `ACL GENPASS <https://redis.io/commands/acl-genpass>`_
      - Needs porting from: :meth:`Redis.acl_genpass`
    * - `ACL GETUSER <https://redis.io/commands/acl-getuser>`_
      - Needs porting from: :meth:`Redis.acl_getuser`
    * - `ACL HELP <https://redis.io/commands/acl-help>`_
      - Needs porting from: :meth:`Redis.acl_help`
    * - `ACL LIST <https://redis.io/commands/acl-list>`_
      - Needs porting from: :meth:`Redis.acl_list`
    * - `ACL LOAD <https://redis.io/commands/acl-load>`_
      - Needs porting from: :meth:`Redis.acl_load`
    * - `ACL LOG <https://redis.io/commands/acl-log>`_
      - Needs porting from: :meth:`Redis.acl_log`
    * - `ACL SAVE <https://redis.io/commands/acl-save>`_
      - Needs porting from: :meth:`Redis.acl_save`
    * - `ACL SETUSER <https://redis.io/commands/acl-setuser>`_
      - Needs porting from: :meth:`Redis.acl_setuser`
    * - `ACL USERS <https://redis.io/commands/acl-users>`_
      - Needs porting from: :meth:`Redis.acl_users`
    * - `ACL WHOAMI <https://redis.io/commands/acl-whoami>`_
      - Needs porting from: :meth:`Redis.acl_whoami`
    * - `COMMAND <https://redis.io/commands/command>`_
      - Needs porting from: :meth:`Redis.command`
    * - `COMMAND COUNT <https://redis.io/commands/command-count>`_
      - Needs porting from: :meth:`Redis.command_count`
    * - `COMMAND GETKEYS <https://redis.io/commands/command-getkeys>`_
      - Needs porting from: :meth:`Redis.command_getkeys`
    * - `COMMAND INFO <https://redis.io/commands/command-info>`_
      - Needs porting from: :meth:`Redis.command_info`
    * - `LOLWUT <https://redis.io/commands/lolwut>`_
      - Needs porting from: :meth:`Redis.lolwut`
    * - `MEMORY DOCTOR <https://redis.io/commands/memory-doctor>`_
      - Needs porting from: :meth:`Redis.memory_doctor`
    * - `MEMORY HELP <https://redis.io/commands/memory-help>`_
      - Needs porting from: :meth:`Redis.memory_help`
    * - `MEMORY PURGE <https://redis.io/commands/memory-purge>`_
      - Needs porting from: :meth:`Redis.memory_purge`
    * - `MEMORY STATS <https://redis.io/commands/memory-stats>`_
      - Needs porting from: :meth:`Redis.memory_stats`
    * - `MEMORY USAGE <https://redis.io/commands/memory-usage>`_
      - Needs porting from: :meth:`Redis.memory_usage`
    * - `MODULE LIST <https://redis.io/commands/module-list>`_
      - Needs porting from: :meth:`Redis.module_list`
    * - `MODULE LOAD <https://redis.io/commands/module-load>`_
      - Needs porting from: :meth:`Redis.module_load`
    * - `MODULE UNLOAD <https://redis.io/commands/module-unload>`_
      - Needs porting from: :meth:`Redis.module_unload`
    * - `MONITOR <https://redis.io/commands/monitor>`_
      - Needs porting from: :meth:`Redis.monitor`
    * - `PSYNC <https://redis.io/commands/psync>`_
      - Needs porting from: :meth:`Redis.psync`
    * - `REPLICAOF <https://redis.io/commands/replicaof>`_
      - Needs porting from: :meth:`Redis.replicaof`
    * - `SWAPDB <https://redis.io/commands/swapdb>`_
      - Needs porting from: :meth:`Redis.swapdb`
    * - `SYNC <https://redis.io/commands/sync>`_
      - Needs porting from: :meth:`Redis.sync`
Connection
----------

.. list-table::
    :class: command-table

    * - `CLIENT GETNAME <https://redis.io/commands/client-getname>`_
      - :meth:`~coredis.StrictRedis.client_getname`
    * - `CLIENT KILL <https://redis.io/commands/client-kill>`_
      - :meth:`~coredis.StrictRedis.client_kill`
    * - `CLIENT LIST <https://redis.io/commands/client-list>`_
      - :meth:`~coredis.StrictRedis.client_list`
    * - `CLIENT PAUSE <https://redis.io/commands/client-pause>`_
      - :meth:`~coredis.StrictRedis.client_pause`
    * - `CLIENT SETNAME <https://redis.io/commands/client-setname>`_
      - :meth:`~coredis.StrictRedis.client_setname`
    * - `ECHO <https://redis.io/commands/echo>`_
      - :meth:`~coredis.StrictRedis.echo`
    * - `PING <https://redis.io/commands/ping>`_
      - :meth:`~coredis.StrictRedis.ping`
    * - `CLIENT <https://redis.io/commands/client>`_
      - Needs porting from: :meth:`Redis.client`
    * - `CLIENT GETREDIR <https://redis.io/commands/client-getredir>`_
      - Needs porting from: :meth:`Redis.client_getredir`
    * - `CLIENT ID <https://redis.io/commands/client-id>`_
      - Needs porting from: :meth:`Redis.client_id`
    * - `CLIENT INFO <https://redis.io/commands/client-info>`_
      - Needs porting from: :meth:`Redis.client_info`
    * - `CLIENT REPLY <https://redis.io/commands/client-reply>`_
      - Needs porting from: :meth:`Redis.client_reply`
    * - `CLIENT TRACKING <https://redis.io/commands/client-tracking>`_
      - Needs porting from: :meth:`Redis.client_tracking`
    * - `CLIENT TRACKINGINFO <https://redis.io/commands/client-trackinginfo>`_
      - Needs porting from: :meth:`Redis.client_trackinginfo`
    * - `CLIENT UNBLOCK <https://redis.io/commands/client-unblock>`_
      - Needs porting from: :meth:`Redis.client_unblock`
    * - `CLIENT UNPAUSE <https://redis.io/commands/client-unpause>`_
      - Needs porting from: :meth:`Redis.client_unpause`
    * - `QUIT <https://redis.io/commands/quit>`_
      - Needs porting from: :meth:`Redis.quit`
    * - `RESET <https://redis.io/commands/reset>`_
      - Needs porting from: :meth:`Redis.reset`
    * - `SELECT <https://redis.io/commands/select>`_
      - Needs porting from: :meth:`Redis.select`

Redis Cluster
^^^^^^^^^^^^^

String
------

.. list-table::
    :class: command-table

    * - `APPEND <https://redis.io/commands/append>`_
      - :meth:`~coredis.StrictRedisCluster.append`
    * - `DECR <https://redis.io/commands/decr>`_
      - :meth:`~coredis.StrictRedisCluster.decr`
    * - `GET <https://redis.io/commands/get>`_
      - :meth:`~coredis.StrictRedisCluster.get`
    * - `GETRANGE <https://redis.io/commands/getrange>`_
      - :meth:`~coredis.StrictRedisCluster.getrange`
    * - `GETSET <https://redis.io/commands/getset>`_
      - :meth:`~coredis.StrictRedisCluster.getset`
    * - `INCR <https://redis.io/commands/incr>`_
      - :meth:`~coredis.StrictRedisCluster.incr`
    * - `INCRBY <https://redis.io/commands/incrby>`_
      - :meth:`~coredis.StrictRedisCluster.incrby`
    * - `INCRBYFLOAT <https://redis.io/commands/incrbyfloat>`_
      - :meth:`~coredis.StrictRedisCluster.incrbyfloat`
    * - `MGET <https://redis.io/commands/mget>`_
      - :meth:`~coredis.StrictRedisCluster.mget`
    * - `MSET <https://redis.io/commands/mset>`_
      - :meth:`~coredis.StrictRedisCluster.mset`
    * - `MSETNX <https://redis.io/commands/msetnx>`_
      - :meth:`~coredis.StrictRedisCluster.msetnx`
    * - `PSETEX <https://redis.io/commands/psetex>`_
      - :meth:`~coredis.StrictRedisCluster.psetex`
    * - `SET <https://redis.io/commands/set>`_
      - :meth:`~coredis.StrictRedisCluster.set`
    * - `SETEX <https://redis.io/commands/setex>`_
      - :meth:`~coredis.StrictRedisCluster.setex`
    * - `SETNX <https://redis.io/commands/setnx>`_
      - :meth:`~coredis.StrictRedisCluster.setnx`
    * - `SETRANGE <https://redis.io/commands/setrange>`_
      - :meth:`~coredis.StrictRedisCluster.setrange`
    * - `STRLEN <https://redis.io/commands/strlen>`_
      - :meth:`~coredis.StrictRedisCluster.strlen`
    * - `SUBSTR <https://redis.io/commands/substr>`_
      - :meth:`~coredis.StrictRedisCluster.substr`
    * - `DECRBY <https://redis.io/commands/decrby>`_
      - Needs porting from: :meth:`RedisCluster.decrby`
    * - `GETDEL <https://redis.io/commands/getdel>`_
      - Needs porting from: :meth:`RedisCluster.getdel`
    * - `GETEX <https://redis.io/commands/getex>`_
      - Needs porting from: :meth:`RedisCluster.getex`
Bitmap
------

.. list-table::
    :class: command-table

    * - `BITCOUNT <https://redis.io/commands/bitcount>`_
      - :meth:`~coredis.StrictRedisCluster.bitcount`
    * - `BITFIELD <https://redis.io/commands/bitfield>`_
      - :meth:`~coredis.StrictRedisCluster.bitfield`
    * - `BITOP <https://redis.io/commands/bitop>`_
      - :meth:`~coredis.StrictRedisCluster.bitop`
    * - `BITPOS <https://redis.io/commands/bitpos>`_
      - :meth:`~coredis.StrictRedisCluster.bitpos`
    * - `GETBIT <https://redis.io/commands/getbit>`_
      - :meth:`~coredis.StrictRedisCluster.getbit`
    * - `SETBIT <https://redis.io/commands/setbit>`_
      - :meth:`~coredis.StrictRedisCluster.setbit`
List
----

.. list-table::
    :class: command-table

    * - `BLPOP <https://redis.io/commands/blpop>`_
      - :meth:`~coredis.StrictRedisCluster.blpop`
    * - `BRPOP <https://redis.io/commands/brpop>`_
      - :meth:`~coredis.StrictRedisCluster.brpop`
    * - `BRPOPLPUSH <https://redis.io/commands/brpoplpush>`_
      - :meth:`~coredis.StrictRedisCluster.brpoplpush`
    * - `LINDEX <https://redis.io/commands/lindex>`_
      - :meth:`~coredis.StrictRedisCluster.lindex`
    * - `LINSERT <https://redis.io/commands/linsert>`_
      - :meth:`~coredis.StrictRedisCluster.linsert`
    * - `LLEN <https://redis.io/commands/llen>`_
      - :meth:`~coredis.StrictRedisCluster.llen`
    * - `LPOP <https://redis.io/commands/lpop>`_
      - :meth:`~coredis.StrictRedisCluster.lpop`
    * - `LPUSH <https://redis.io/commands/lpush>`_
      - :meth:`~coredis.StrictRedisCluster.lpush`
    * - `LPUSHX <https://redis.io/commands/lpushx>`_
      - :meth:`~coredis.StrictRedisCluster.lpushx`
    * - `LRANGE <https://redis.io/commands/lrange>`_
      - :meth:`~coredis.StrictRedisCluster.lrange`
    * - `LREM <https://redis.io/commands/lrem>`_
      - :meth:`~coredis.StrictRedisCluster.lrem`
    * - `LSET <https://redis.io/commands/lset>`_
      - :meth:`~coredis.StrictRedisCluster.lset`
    * - `LTRIM <https://redis.io/commands/ltrim>`_
      - :meth:`~coredis.StrictRedisCluster.ltrim`
    * - `RPOP <https://redis.io/commands/rpop>`_
      - :meth:`~coredis.StrictRedisCluster.rpop`
    * - `RPOPLPUSH <https://redis.io/commands/rpoplpush>`_
      - :meth:`~coredis.StrictRedisCluster.rpoplpush`
    * - `RPUSH <https://redis.io/commands/rpush>`_
      - :meth:`~coredis.StrictRedisCluster.rpush`
    * - `RPUSHX <https://redis.io/commands/rpushx>`_
      - :meth:`~coredis.StrictRedisCluster.rpushx`
    * - `BLMOVE <https://redis.io/commands/blmove>`_
      - Needs porting from: :meth:`RedisCluster.blmove`
    * - `LMOVE <https://redis.io/commands/lmove>`_
      - Needs porting from: :meth:`RedisCluster.lmove`
    * - `LPOS <https://redis.io/commands/lpos>`_
      - Needs porting from: :meth:`RedisCluster.lpos`
Sorted-Set
----------

.. list-table::
    :class: command-table

    * - `ZADD <https://redis.io/commands/zadd>`_
      - :meth:`~coredis.StrictRedisCluster.zadd`
    * - `ZCARD <https://redis.io/commands/zcard>`_
      - :meth:`~coredis.StrictRedisCluster.zcard`
    * - `ZCOUNT <https://redis.io/commands/zcount>`_
      - :meth:`~coredis.StrictRedisCluster.zcount`
    * - `ZINCRBY <https://redis.io/commands/zincrby>`_
      - :meth:`~coredis.StrictRedisCluster.zincrby`
    * - `ZINTERSTORE <https://redis.io/commands/zinterstore>`_
      - :meth:`~coredis.StrictRedisCluster.zinterstore`
    * - `ZLEXCOUNT <https://redis.io/commands/zlexcount>`_
      - :meth:`~coredis.StrictRedisCluster.zlexcount`
    * - `ZRANGE <https://redis.io/commands/zrange>`_
      - :meth:`~coredis.StrictRedisCluster.zrange`
    * - `ZRANGEBYLEX <https://redis.io/commands/zrangebylex>`_
      - :meth:`~coredis.StrictRedisCluster.zrangebylex`
    * - `ZRANGEBYSCORE <https://redis.io/commands/zrangebyscore>`_
      - :meth:`~coredis.StrictRedisCluster.zrangebyscore`
    * - `ZRANK <https://redis.io/commands/zrank>`_
      - :meth:`~coredis.StrictRedisCluster.zrank`
    * - `ZREM <https://redis.io/commands/zrem>`_
      - :meth:`~coredis.StrictRedisCluster.zrem`
    * - `ZREMRANGEBYLEX <https://redis.io/commands/zremrangebylex>`_
      - :meth:`~coredis.StrictRedisCluster.zremrangebylex`
    * - `ZREMRANGEBYRANK <https://redis.io/commands/zremrangebyrank>`_
      - :meth:`~coredis.StrictRedisCluster.zremrangebyrank`
    * - `ZREMRANGEBYSCORE <https://redis.io/commands/zremrangebyscore>`_
      - :meth:`~coredis.StrictRedisCluster.zremrangebyscore`
    * - `ZREVRANGE <https://redis.io/commands/zrevrange>`_
      - :meth:`~coredis.StrictRedisCluster.zrevrange`
    * - `ZREVRANGEBYLEX <https://redis.io/commands/zrevrangebylex>`_
      - :meth:`~coredis.StrictRedisCluster.zrevrangebylex`
    * - `ZREVRANGEBYSCORE <https://redis.io/commands/zrevrangebyscore>`_
      - :meth:`~coredis.StrictRedisCluster.zrevrangebyscore`
    * - `ZREVRANK <https://redis.io/commands/zrevrank>`_
      - :meth:`~coredis.StrictRedisCluster.zrevrank`
    * - `ZSCAN <https://redis.io/commands/zscan>`_
      - :meth:`~coredis.StrictRedisCluster.zscan`
    * - `ZSCORE <https://redis.io/commands/zscore>`_
      - :meth:`~coredis.StrictRedisCluster.zscore`
    * - `ZUNIONSTORE <https://redis.io/commands/zunionstore>`_
      - :meth:`~coredis.StrictRedisCluster.zunionstore`
    * - `BZPOPMAX <https://redis.io/commands/bzpopmax>`_
      - Needs porting from: :meth:`RedisCluster.bzpopmax`
    * - `BZPOPMIN <https://redis.io/commands/bzpopmin>`_
      - Needs porting from: :meth:`RedisCluster.bzpopmin`
    * - `ZDIFF <https://redis.io/commands/zdiff>`_
      - Needs porting from: :meth:`RedisCluster.zdiff`
    * - `ZDIFFSTORE <https://redis.io/commands/zdiffstore>`_
      - Needs porting from: :meth:`RedisCluster.zdiffstore`
    * - `ZINTER <https://redis.io/commands/zinter>`_
      - Needs porting from: :meth:`RedisCluster.zinter`
    * - `ZMSCORE <https://redis.io/commands/zmscore>`_
      - Needs porting from: :meth:`RedisCluster.zmscore`
    * - `ZPOPMAX <https://redis.io/commands/zpopmax>`_
      - Needs porting from: :meth:`RedisCluster.zpopmax`
    * - `ZPOPMIN <https://redis.io/commands/zpopmin>`_
      - Needs porting from: :meth:`RedisCluster.zpopmin`
    * - `ZRANDMEMBER <https://redis.io/commands/zrandmember>`_
      - Needs porting from: :meth:`RedisCluster.zrandmember`
    * - `ZRANGESTORE <https://redis.io/commands/zrangestore>`_
      - Needs porting from: :meth:`RedisCluster.zrangestore`
    * - `ZUNION <https://redis.io/commands/zunion>`_
      - Needs porting from: :meth:`RedisCluster.zunion`
Generic
-------

.. list-table::
    :class: command-table

    * - `DUMP <https://redis.io/commands/dump>`_
      - :meth:`~coredis.StrictRedisCluster.dump`
    * - `EXISTS <https://redis.io/commands/exists>`_
      - :meth:`~coredis.StrictRedisCluster.exists`
    * - `EXPIRE <https://redis.io/commands/expire>`_
      - :meth:`~coredis.StrictRedisCluster.expire`
    * - `EXPIREAT <https://redis.io/commands/expireat>`_
      - :meth:`~coredis.StrictRedisCluster.expireat`
    * - `KEYS <https://redis.io/commands/keys>`_
      - :meth:`~coredis.StrictRedisCluster.keys`
    * - `MOVE <https://redis.io/commands/move>`_
      - :meth:`~coredis.StrictRedisCluster.move`
    * - `OBJECT <https://redis.io/commands/object>`_
      - :meth:`~coredis.StrictRedisCluster.object`
    * - `PERSIST <https://redis.io/commands/persist>`_
      - :meth:`~coredis.StrictRedisCluster.persist`
    * - `PEXPIRE <https://redis.io/commands/pexpire>`_
      - :meth:`~coredis.StrictRedisCluster.pexpire`
    * - `PEXPIREAT <https://redis.io/commands/pexpireat>`_
      - :meth:`~coredis.StrictRedisCluster.pexpireat`
    * - `PTTL <https://redis.io/commands/pttl>`_
      - :meth:`~coredis.StrictRedisCluster.pttl`
    * - `RANDOMKEY <https://redis.io/commands/randomkey>`_
      - :meth:`~coredis.StrictRedisCluster.randomkey`
    * - `RENAME <https://redis.io/commands/rename>`_
      - :meth:`~coredis.StrictRedisCluster.rename`
    * - `RENAMENX <https://redis.io/commands/renamenx>`_
      - :meth:`~coredis.StrictRedisCluster.renamenx`
    * - `RESTORE <https://redis.io/commands/restore>`_
      - :meth:`~coredis.StrictRedisCluster.restore`
    * - `SCAN <https://redis.io/commands/scan>`_
      - :meth:`~coredis.StrictRedisCluster.scan`
    * - `SORT <https://redis.io/commands/sort>`_
      - :meth:`~coredis.StrictRedisCluster.sort`
    * - `TOUCH <https://redis.io/commands/touch>`_
      - :meth:`~coredis.StrictRedisCluster.touch`
    * - `TTL <https://redis.io/commands/ttl>`_
      - :meth:`~coredis.StrictRedisCluster.ttl`
    * - `TYPE <https://redis.io/commands/type>`_
      - :meth:`~coredis.StrictRedisCluster.type`
    * - `UNLINK <https://redis.io/commands/unlink>`_
      - :meth:`~coredis.StrictRedisCluster.unlink`
    * - `WAIT <https://redis.io/commands/wait>`_
      - :meth:`~coredis.StrictRedisCluster.wait`
    * - `COPY <https://redis.io/commands/copy>`_
      - Needs porting from: :meth:`RedisCluster.copy`
    * - `MIGRATE <https://redis.io/commands/migrate>`_
      - Needs porting from: :meth:`RedisCluster.migrate`
Transactions
------------

.. list-table::
    :class: command-table

    * - `UNWATCH <https://redis.io/commands/unwatch>`_
      - :meth:`~coredis.StrictRedisCluster.unwatch`
    * - `WATCH <https://redis.io/commands/watch>`_
      - :meth:`~coredis.StrictRedisCluster.watch`
Scripting
---------

.. list-table::
    :class: command-table

    * - `EVAL <https://redis.io/commands/eval>`_
      - :meth:`~coredis.StrictRedisCluster.eval`
    * - `EVALSHA <https://redis.io/commands/evalsha>`_
      - :meth:`~coredis.StrictRedisCluster.evalsha`
    * - `SCRIPT EXISTS <https://redis.io/commands/script-exists>`_
      - :meth:`~coredis.StrictRedisCluster.script_exists`
    * - `SCRIPT FLUSH <https://redis.io/commands/script-flush>`_
      - :meth:`~coredis.StrictRedisCluster.script_flush`
    * - `SCRIPT KILL <https://redis.io/commands/script-kill>`_
      - :meth:`~coredis.StrictRedisCluster.script_kill`
    * - `SCRIPT LOAD <https://redis.io/commands/script-load>`_
      - :meth:`~coredis.StrictRedisCluster.script_load`
Geo
---

.. list-table::
    :class: command-table

    * - `GEOADD <https://redis.io/commands/geoadd>`_
      - :meth:`~coredis.StrictRedisCluster.geoadd`
    * - `GEODIST <https://redis.io/commands/geodist>`_
      - :meth:`~coredis.StrictRedisCluster.geodist`
    * - `GEOHASH <https://redis.io/commands/geohash>`_
      - :meth:`~coredis.StrictRedisCluster.geohash`
    * - `GEOPOS <https://redis.io/commands/geopos>`_
      - :meth:`~coredis.StrictRedisCluster.geopos`
    * - `GEORADIUS <https://redis.io/commands/georadius>`_
      - :meth:`~coredis.StrictRedisCluster.georadius`
    * - `GEORADIUSBYMEMBER <https://redis.io/commands/georadiusbymember>`_
      - :meth:`~coredis.StrictRedisCluster.georadiusbymember`
    * - `GEOSEARCH <https://redis.io/commands/geosearch>`_
      - Needs porting from: :meth:`RedisCluster.geosearch`
    * - `GEOSEARCHSTORE <https://redis.io/commands/geosearchstore>`_
      - Needs porting from: :meth:`RedisCluster.geosearchstore`
Hash
----

.. list-table::
    :class: command-table

    * - `HDEL <https://redis.io/commands/hdel>`_
      - :meth:`~coredis.StrictRedisCluster.hdel`
    * - `HEXISTS <https://redis.io/commands/hexists>`_
      - :meth:`~coredis.StrictRedisCluster.hexists`
    * - `HGET <https://redis.io/commands/hget>`_
      - :meth:`~coredis.StrictRedisCluster.hget`
    * - `HGETALL <https://redis.io/commands/hgetall>`_
      - :meth:`~coredis.StrictRedisCluster.hgetall`
    * - `HINCRBY <https://redis.io/commands/hincrby>`_
      - :meth:`~coredis.StrictRedisCluster.hincrby`
    * - `HINCRBYFLOAT <https://redis.io/commands/hincrbyfloat>`_
      - :meth:`~coredis.StrictRedisCluster.hincrbyfloat`
    * - `HKEYS <https://redis.io/commands/hkeys>`_
      - :meth:`~coredis.StrictRedisCluster.hkeys`
    * - `HLEN <https://redis.io/commands/hlen>`_
      - :meth:`~coredis.StrictRedisCluster.hlen`
    * - `HMGET <https://redis.io/commands/hmget>`_
      - :meth:`~coredis.StrictRedisCluster.hmget`
    * - `HMSET <https://redis.io/commands/hmset>`_
      - :meth:`~coredis.StrictRedisCluster.hmset`
    * - `HSCAN <https://redis.io/commands/hscan>`_
      - :meth:`~coredis.StrictRedisCluster.hscan`
    * - `HSET <https://redis.io/commands/hset>`_
      - :meth:`~coredis.StrictRedisCluster.hset`
    * - `HSETNX <https://redis.io/commands/hsetnx>`_
      - :meth:`~coredis.StrictRedisCluster.hsetnx`
    * - `HSTRLEN <https://redis.io/commands/hstrlen>`_
      - :meth:`~coredis.StrictRedisCluster.hstrlen`
    * - `HVALS <https://redis.io/commands/hvals>`_
      - :meth:`~coredis.StrictRedisCluster.hvals`
    * - `HRANDFIELD <https://redis.io/commands/hrandfield>`_
      - Needs porting from: :meth:`RedisCluster.hrandfield`
Hyperloglog
-----------

.. list-table::
    :class: command-table

    * - `PFADD <https://redis.io/commands/pfadd>`_
      - :meth:`~coredis.StrictRedisCluster.pfadd`
    * - `PFCOUNT <https://redis.io/commands/pfcount>`_
      - :meth:`~coredis.StrictRedisCluster.pfcount`
    * - `PFMERGE <https://redis.io/commands/pfmerge>`_
      - :meth:`~coredis.StrictRedisCluster.pfmerge`
Pubsub
------

.. list-table::
    :class: command-table

    * - `PUBLISH <https://redis.io/commands/publish>`_
      - :meth:`~coredis.StrictRedisCluster.publish`
    * - `PUBSUB <https://redis.io/commands/pubsub>`_
      - :meth:`~coredis.StrictRedisCluster.pubsub`
    * - `PUBSUB CHANNELS <https://redis.io/commands/pubsub-channels>`_
      - :meth:`~coredis.StrictRedisCluster.pubsub_channels`
    * - `PUBSUB NUMPAT <https://redis.io/commands/pubsub-numpat>`_
      - :meth:`~coredis.StrictRedisCluster.pubsub_numpat`
    * - `PUBSUB NUMSUB <https://redis.io/commands/pubsub-numsub>`_
      - :meth:`~coredis.StrictRedisCluster.pubsub_numsub`
Set
---

.. list-table::
    :class: command-table

    * - `SADD <https://redis.io/commands/sadd>`_
      - :meth:`~coredis.StrictRedisCluster.sadd`
    * - `SCARD <https://redis.io/commands/scard>`_
      - :meth:`~coredis.StrictRedisCluster.scard`
    * - `SDIFF <https://redis.io/commands/sdiff>`_
      - :meth:`~coredis.StrictRedisCluster.sdiff`
    * - `SDIFFSTORE <https://redis.io/commands/sdiffstore>`_
      - :meth:`~coredis.StrictRedisCluster.sdiffstore`
    * - `SINTER <https://redis.io/commands/sinter>`_
      - :meth:`~coredis.StrictRedisCluster.sinter`
    * - `SINTERSTORE <https://redis.io/commands/sinterstore>`_
      - :meth:`~coredis.StrictRedisCluster.sinterstore`
    * - `SISMEMBER <https://redis.io/commands/sismember>`_
      - :meth:`~coredis.StrictRedisCluster.sismember`
    * - `SMEMBERS <https://redis.io/commands/smembers>`_
      - :meth:`~coredis.StrictRedisCluster.smembers`
    * - `SMOVE <https://redis.io/commands/smove>`_
      - :meth:`~coredis.StrictRedisCluster.smove`
    * - `SPOP <https://redis.io/commands/spop>`_
      - :meth:`~coredis.StrictRedisCluster.spop`
    * - `SRANDMEMBER <https://redis.io/commands/srandmember>`_
      - :meth:`~coredis.StrictRedisCluster.srandmember`
    * - `SREM <https://redis.io/commands/srem>`_
      - :meth:`~coredis.StrictRedisCluster.srem`
    * - `SSCAN <https://redis.io/commands/sscan>`_
      - :meth:`~coredis.StrictRedisCluster.sscan`
    * - `SUNION <https://redis.io/commands/sunion>`_
      - :meth:`~coredis.StrictRedisCluster.sunion`
    * - `SUNIONSTORE <https://redis.io/commands/sunionstore>`_
      - :meth:`~coredis.StrictRedisCluster.sunionstore`
    * - `SMISMEMBER <https://redis.io/commands/smismember>`_
      - Needs porting from: :meth:`RedisCluster.smismember`
Stream
------

.. list-table::
    :class: command-table

    * - `XACK <https://redis.io/commands/xack>`_
      - :meth:`~coredis.StrictRedisCluster.xack`
    * - `XADD <https://redis.io/commands/xadd>`_
      - :meth:`~coredis.StrictRedisCluster.xadd`
    * - `XCLAIM <https://redis.io/commands/xclaim>`_
      - :meth:`~coredis.StrictRedisCluster.xclaim`
    * - `XDEL <https://redis.io/commands/xdel>`_
      - :meth:`~coredis.StrictRedisCluster.xdel`
    * - `XGROUP CREATE <https://redis.io/commands/xgroup-create>`_
      - :meth:`~coredis.StrictRedisCluster.xgroup_create`
    * - `XGROUP DESTROY <https://redis.io/commands/xgroup-destroy>`_
      - :meth:`~coredis.StrictRedisCluster.xgroup_destroy`
    * - `XINFO CONSUMERS <https://redis.io/commands/xinfo-consumers>`_
      - :meth:`~coredis.StrictRedisCluster.xinfo_consumers`
    * - `XINFO GROUPS <https://redis.io/commands/xinfo-groups>`_
      - :meth:`~coredis.StrictRedisCluster.xinfo_groups`
    * - `XINFO STREAM <https://redis.io/commands/xinfo-stream>`_
      - :meth:`~coredis.StrictRedisCluster.xinfo_stream`
    * - `XLEN <https://redis.io/commands/xlen>`_
      - :meth:`~coredis.StrictRedisCluster.xlen`
    * - `XPENDING <https://redis.io/commands/xpending>`_
      - :meth:`~coredis.StrictRedisCluster.xpending`
    * - `XRANGE <https://redis.io/commands/xrange>`_
      - :meth:`~coredis.StrictRedisCluster.xrange`
    * - `XREAD <https://redis.io/commands/xread>`_
      - :meth:`~coredis.StrictRedisCluster.xread`
    * - `XREADGROUP <https://redis.io/commands/xreadgroup>`_
      - :meth:`~coredis.StrictRedisCluster.xreadgroup`
    * - `XREVRANGE <https://redis.io/commands/xrevrange>`_
      - :meth:`~coredis.StrictRedisCluster.xrevrange`
    * - `XTRIM <https://redis.io/commands/xtrim>`_
      - :meth:`~coredis.StrictRedisCluster.xtrim`
    * - `XAUTOCLAIM <https://redis.io/commands/xautoclaim>`_
      - Needs porting from: :meth:`RedisCluster.xautoclaim`
    * - `XGROUP CREATECONSUMER <https://redis.io/commands/xgroup-createconsumer>`_
      - Needs porting from: :meth:`RedisCluster.xgroup_createconsumer`
    * - `XGROUP DELCONSUMER <https://redis.io/commands/xgroup-delconsumer>`_
      - Needs porting from: :meth:`RedisCluster.xgroup_delconsumer`
    * - `XGROUP SETID <https://redis.io/commands/xgroup-setid>`_
      - Needs porting from: :meth:`RedisCluster.xgroup_setid`
Cluster
-------

.. list-table::
    :class: command-table

    * - `CLUSTER ADDSLOTS <https://redis.io/commands/cluster-addslots>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_addslots`
    * - `CLUSTER COUNTKEYSINSLOT <https://redis.io/commands/cluster-countkeysinslot>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_countkeysinslot`
    * - `CLUSTER DELSLOTS <https://redis.io/commands/cluster-delslots>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_delslots`
    * - `CLUSTER FAILOVER <https://redis.io/commands/cluster-failover>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_failover`
    * - `CLUSTER FORGET <https://redis.io/commands/cluster-forget>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_forget`
    * - `CLUSTER INFO <https://redis.io/commands/cluster-info>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_info`
    * - `CLUSTER KEYSLOT <https://redis.io/commands/cluster-keyslot>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_keyslot`
    * - `CLUSTER MEET <https://redis.io/commands/cluster-meet>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_meet`
    * - `CLUSTER NODES <https://redis.io/commands/cluster-nodes>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_nodes`
    * - `CLUSTER REPLICATE <https://redis.io/commands/cluster-replicate>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_replicate`
    * - `CLUSTER RESET <https://redis.io/commands/cluster-reset>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_reset`
    * - `CLUSTER SETSLOT <https://redis.io/commands/cluster-setslot>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_setslot`
    * - `CLUSTER SLAVES <https://redis.io/commands/cluster-slaves>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_slaves`
    * - `CLUSTER SLOTS <https://redis.io/commands/cluster-slots>`_
      - :meth:`~coredis.StrictRedisCluster.cluster_slots`
    * - `CLUSTER REPLICAS <https://redis.io/commands/cluster-replicas>`_
      - Needs porting from: :meth:`RedisCluster.cluster_replicas`
    * - `READONLY <https://redis.io/commands/readonly>`_
      - Needs porting from: :meth:`RedisCluster.readonly`
    * - `READWRITE <https://redis.io/commands/readwrite>`_
      - Needs porting from: :meth:`RedisCluster.readwrite`

