Command compatibility
=====================
Redis Client
^^^^^^^^^^^^

String
------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `APPEND <https://redis.io/commands/append>`_

        Append a value to a key
      - :meth:`~coredis.StrictRedis.append`

        
        
        
        


      
            

    * - `DECR <https://redis.io/commands/decr>`_

        Decrement the integer value of a key by one
      - :meth:`~coredis.StrictRedis.decr`

        
        
        
        


      
            

    * - `DECRBY <https://redis.io/commands/decrby>`_

        Decrement the integer value of a key by the given number
      - :meth:`~coredis.StrictRedis.decrby`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `GET <https://redis.io/commands/get>`_

        Get the value of a key
      - :meth:`~coredis.StrictRedis.get`

        
        
        
        


      
            

    * - `GETDEL <https://redis.io/commands/getdel>`_

        Get the value of a key and delete the key
      - :meth:`~coredis.StrictRedis.getdel`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `GETEX <https://redis.io/commands/getex>`_

        Get the value of a key and optionally set its expiration
      - :meth:`~coredis.StrictRedis.getex`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `GETRANGE <https://redis.io/commands/getrange>`_

        Get a substring of the string stored at a key
      - :meth:`~coredis.StrictRedis.getrange`

        
        
        
        


      
            

    * - `GETSET <https://redis.io/commands/getset>`_

        Set the string value of a key and return its old value
      - :meth:`~coredis.StrictRedis.getset`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedis.set`  with the ``!GET`` argument
        


      
            

    * - `INCR <https://redis.io/commands/incr>`_

        Increment the integer value of a key by one
      - :meth:`~coredis.StrictRedis.incr`

        
        
        
        


      
            

    * - `INCRBY <https://redis.io/commands/incrby>`_

        Increment the integer value of a key by the given amount
      - :meth:`~coredis.StrictRedis.incrby`

        
        
        
        


      
            

    * - `INCRBYFLOAT <https://redis.io/commands/incrbyfloat>`_

        Increment the float value of a key by the given amount
      - :meth:`~coredis.StrictRedis.incrbyfloat`

        
        
        
        


      
            

    * - `MGET <https://redis.io/commands/mget>`_

        Get the values of all the given keys
      - :meth:`~coredis.StrictRedis.mget`

        
        
        
        


      
            

    * - `MSET <https://redis.io/commands/mset>`_

        Set multiple keys to multiple values
      - :meth:`~coredis.StrictRedis.mset`

        
        
        
        


      
            

    * - `MSETNX <https://redis.io/commands/msetnx>`_

        Set multiple keys to multiple values, only if none of the keys exist
      - :meth:`~coredis.StrictRedis.msetnx`

        
        
        
        


      
            

    * - `PSETEX <https://redis.io/commands/psetex>`_

        Set the value and expiration in milliseconds of a key
      - :meth:`~coredis.StrictRedis.psetex`

        
        
        
        


      
            

    * - `SET <https://redis.io/commands/set>`_

        Set the string value of a key
      - :meth:`~coredis.StrictRedis.set`

        
        
        
        


      
            

    * - `SETEX <https://redis.io/commands/setex>`_

        Set the value and expiration of a key
      - :meth:`~coredis.StrictRedis.setex`

        
        
        
        


      
            

    * - `SETNX <https://redis.io/commands/setnx>`_

        Set the value of a key, only if the key does not exist
      - :meth:`~coredis.StrictRedis.setnx`

        
        
        
        


      
            

    * - `SETRANGE <https://redis.io/commands/setrange>`_

        Overwrite part of a string at key starting at the specified offset
      - :meth:`~coredis.StrictRedis.setrange`

        
        
        
        


      
            

    * - `STRLEN <https://redis.io/commands/strlen>`_

        Get the length of the value stored in a key
      - :meth:`~coredis.StrictRedis.strlen`

        
        
        
        


      
            

    * - `SUBSTR <https://redis.io/commands/substr>`_

        Get a substring of the string stored at a key
      - :meth:`~coredis.StrictRedis.substr`

        
        - ☠️ Deprecated in redis: 2.0.0.
        - Use :meth:`~coredis.StrictRedis.getrange` 
        


      
            

Bitmap
------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `BITCOUNT <https://redis.io/commands/bitcount>`_

        Count set bits in a string
      - :meth:`~coredis.StrictRedis.bitcount`

        
        
        
        


      
            

    * - `BITFIELD <https://redis.io/commands/bitfield>`_

        Perform arbitrary bitfield integer operations on strings
      - :meth:`~coredis.StrictRedis.bitfield`

        
        
        
        


      
            

    * - `BITFIELD_RO <https://redis.io/commands/bitfield_ro>`_

        Perform arbitrary bitfield integer operations on strings. Read-only variant of BITFIELD
      - :meth:`~coredis.StrictRedis.bitfield_ro`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `BITOP <https://redis.io/commands/bitop>`_

        Perform bitwise operations between strings
      - :meth:`~coredis.StrictRedis.bitop`

        
        
        
        


      
            

    * - `BITPOS <https://redis.io/commands/bitpos>`_

        Find first bit set or clear in a string
      - :meth:`~coredis.StrictRedis.bitpos`

        
        
        
        


      
            

    * - `GETBIT <https://redis.io/commands/getbit>`_

        Returns the bit value at offset in the string value stored at key
      - :meth:`~coredis.StrictRedis.getbit`

        
        
        
        


      
            

    * - `SETBIT <https://redis.io/commands/setbit>`_

        Sets or clears the bit at offset in the string value stored at key
      - :meth:`~coredis.StrictRedis.setbit`

        
        
        
        


      
            

List
----

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `BLMOVE <https://redis.io/commands/blmove>`_

        Pop an element from a list, push it to another list and return it; or block until one is available
      - :meth:`~coredis.StrictRedis.blmove`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `BLPOP <https://redis.io/commands/blpop>`_

        Remove and get the first element in a list, or block until one is available
      - :meth:`~coredis.StrictRedis.blpop`

        
        
        
        


      
            

    * - `BRPOP <https://redis.io/commands/brpop>`_

        Remove and get the last element in a list, or block until one is available
      - :meth:`~coredis.StrictRedis.brpop`

        
        
        
        


      
            

    * - `BRPOPLPUSH <https://redis.io/commands/brpoplpush>`_

        Pop an element from a list, push it to another list and return it; or block until one is available
      - :meth:`~coredis.StrictRedis.brpoplpush`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedis.blmove`  with the ``RIGHT`` and ``LEFT`` arguments
        


      
            

    * - `LINDEX <https://redis.io/commands/lindex>`_

        Get an element from a list by its index
      - :meth:`~coredis.StrictRedis.lindex`

        
        
        
        


      
            

    * - `LINSERT <https://redis.io/commands/linsert>`_

        Insert an element before or after another element in a list
      - :meth:`~coredis.StrictRedis.linsert`

        
        
        
        


      
            

    * - `LLEN <https://redis.io/commands/llen>`_

        Get the length of a list
      - :meth:`~coredis.StrictRedis.llen`

        
        
        
        


      
            

    * - `LMOVE <https://redis.io/commands/lmove>`_

        Pop an element from a list, push it to another list and return it
      - :meth:`~coredis.StrictRedis.lmove`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `LPOP <https://redis.io/commands/lpop>`_

        Remove and get the first elements in a list
      - :meth:`~coredis.StrictRedis.lpop`

        
        
        
        


      
            

    * - `LPOS <https://redis.io/commands/lpos>`_

        Return the index of matching elements on a list
      - :meth:`~coredis.StrictRedis.lpos`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.0.6


      
            

    * - `LPUSH <https://redis.io/commands/lpush>`_

        Prepend one or multiple elements to a list
      - :meth:`~coredis.StrictRedis.lpush`

        
        
        
        


      
            

    * - `LPUSHX <https://redis.io/commands/lpushx>`_

        Prepend an element to a list, only if the list exists
      - :meth:`~coredis.StrictRedis.lpushx`

        
        
        
        


      
            

    * - `LRANGE <https://redis.io/commands/lrange>`_

        Get a range of elements from a list
      - :meth:`~coredis.StrictRedis.lrange`

        
        
        
        


      
            

    * - `LREM <https://redis.io/commands/lrem>`_

        Remove elements from a list
      - :meth:`~coredis.StrictRedis.lrem`

        
        
        
        


      
            

    * - `LSET <https://redis.io/commands/lset>`_

        Set the value of an element in a list by its index
      - :meth:`~coredis.StrictRedis.lset`

        
        
        
        


      
            

    * - `LTRIM <https://redis.io/commands/ltrim>`_

        Trim a list to the specified range
      - :meth:`~coredis.StrictRedis.ltrim`

        
        
        
        


      
            

    * - `RPOP <https://redis.io/commands/rpop>`_

        Remove and get the last elements in a list
      - :meth:`~coredis.StrictRedis.rpop`

        
        
        
        


      
            

    * - `RPOPLPUSH <https://redis.io/commands/rpoplpush>`_

        Remove the last element in a list, prepend it to another list and return it
      - :meth:`~coredis.StrictRedis.rpoplpush`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedis.lmove`  with the ``RIGHT`` and ``LEFT`` arguments
        


      
            

    * - `RPUSH <https://redis.io/commands/rpush>`_

        Append one or multiple elements to a list
      - :meth:`~coredis.StrictRedis.rpush`

        
        
        
        


      
            

    * - `RPUSHX <https://redis.io/commands/rpushx>`_

        Append an element to a list, only if the list exists
      - :meth:`~coredis.StrictRedis.rpushx`

        
        
        
        


      
            

Sorted-Set
----------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `BZPOPMAX <https://redis.io/commands/bzpopmax>`_

        Remove and return the member with the highest score from one or more sorted sets, or block until one is available
      - :meth:`~coredis.StrictRedis.bzpopmax`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `BZPOPMIN <https://redis.io/commands/bzpopmin>`_

        Remove and return the member with the lowest score from one or more sorted sets, or block until one is available
      - :meth:`~coredis.StrictRedis.bzpopmin`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `ZADD <https://redis.io/commands/zadd>`_

        Add one or more members to a sorted set, or update its score if it already exists
      - :meth:`~coredis.StrictRedis.zadd`

        
        
        
        


      
            

    * - `ZCARD <https://redis.io/commands/zcard>`_

        Get the number of members in a sorted set
      - :meth:`~coredis.StrictRedis.zcard`

        
        
        
        


      
            

    * - `ZCOUNT <https://redis.io/commands/zcount>`_

        Count the members in a sorted set with scores within the given values
      - :meth:`~coredis.StrictRedis.zcount`

        
        
        
        


      
            

    * - `ZDIFF <https://redis.io/commands/zdiff>`_

        Subtract multiple sorted sets
      - :meth:`~coredis.StrictRedis.zdiff`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZDIFFSTORE <https://redis.io/commands/zdiffstore>`_

        Subtract multiple sorted sets and store the resulting sorted set in a new key
      - :meth:`~coredis.StrictRedis.zdiffstore`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZINCRBY <https://redis.io/commands/zincrby>`_

        Increment the score of a member in a sorted set
      - :meth:`~coredis.StrictRedis.zincrby`

        
        
        
        


      
            

    * - `ZINTER <https://redis.io/commands/zinter>`_

        Intersect multiple sorted sets
      - :meth:`~coredis.StrictRedis.zinter`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZINTERSTORE <https://redis.io/commands/zinterstore>`_

        Intersect multiple sorted sets and store the resulting sorted set in a new key
      - :meth:`~coredis.StrictRedis.zinterstore`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `ZLEXCOUNT <https://redis.io/commands/zlexcount>`_

        Count the number of members in a sorted set between a given lexicographical range
      - :meth:`~coredis.StrictRedis.zlexcount`

        
        
        
        


      
            

    * - `ZMSCORE <https://redis.io/commands/zmscore>`_

        Get the score associated with the given members in a sorted set
      - :meth:`~coredis.StrictRedis.zmscore`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZPOPMAX <https://redis.io/commands/zpopmax>`_

        Remove and return members with the highest scores in a sorted set
      - :meth:`~coredis.StrictRedis.zpopmax`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `ZPOPMIN <https://redis.io/commands/zpopmin>`_

        Remove and return members with the lowest scores in a sorted set
      - :meth:`~coredis.StrictRedis.zpopmin`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `ZRANDMEMBER <https://redis.io/commands/zrandmember>`_

        Get one or multiple random elements from a sorted set
      - :meth:`~coredis.StrictRedis.zrandmember`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZRANGE <https://redis.io/commands/zrange>`_

        Return a range of members in a sorted set
      - :meth:`~coredis.StrictRedis.zrange`

        
        
        
        


      
            

    * - `ZRANGEBYLEX <https://redis.io/commands/zrangebylex>`_

        Return a range of members in a sorted set, by lexicographical range
      - :meth:`~coredis.StrictRedis.zrangebylex`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedis.zrange`  with the ``BYSCORE`` argument
        


      
            

    * - `ZRANGEBYSCORE <https://redis.io/commands/zrangebyscore>`_

        Return a range of members in a sorted set, by score
      - :meth:`~coredis.StrictRedis.zrangebyscore`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedis.zrange`  with the ``BYSCORE`` argument
        


      
            

    * - `ZRANGESTORE <https://redis.io/commands/zrangestore>`_

        Store a range of members from sorted set into another key
      - :meth:`~coredis.StrictRedis.zrangestore`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZRANK <https://redis.io/commands/zrank>`_

        Determine the index of a member in a sorted set
      - :meth:`~coredis.StrictRedis.zrank`

        
        
        
        


      
            

    * - `ZREM <https://redis.io/commands/zrem>`_

        Remove one or more members from a sorted set
      - :meth:`~coredis.StrictRedis.zrem`

        
        
        
        


      
            

    * - `ZREMRANGEBYLEX <https://redis.io/commands/zremrangebylex>`_

        Remove all members in a sorted set between the given lexicographical range
      - :meth:`~coredis.StrictRedis.zremrangebylex`

        
        
        
        


      
            

    * - `ZREMRANGEBYRANK <https://redis.io/commands/zremrangebyrank>`_

        Remove all members in a sorted set within the given indexes
      - :meth:`~coredis.StrictRedis.zremrangebyrank`

        
        
        
        


      
            

    * - `ZREMRANGEBYSCORE <https://redis.io/commands/zremrangebyscore>`_

        Remove all members in a sorted set within the given scores
      - :meth:`~coredis.StrictRedis.zremrangebyscore`

        
        
        
        


      
            

    * - `ZREVRANGE <https://redis.io/commands/zrevrange>`_

        Return a range of members in a sorted set, by index, with scores ordered from high to low
      - :meth:`~coredis.StrictRedis.zrevrange`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedis.zrange`  with the ``REV`` argument
        


      
            

    * - `ZREVRANGEBYLEX <https://redis.io/commands/zrevrangebylex>`_

        Return a range of members in a sorted set, by lexicographical range, ordered from higher to lower strings.
      - :meth:`~coredis.StrictRedis.zrevrangebylex`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedis.zrange`  with the ``REV`` and ``BYLEX`` arguments
        


      
            

    * - `ZREVRANGEBYSCORE <https://redis.io/commands/zrevrangebyscore>`_

        Return a range of members in a sorted set, by score, with scores ordered from high to low
      - :meth:`~coredis.StrictRedis.zrevrangebyscore`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedis.zrange`  with the ``REV`` and ``BYSCORE`` arguments
        


      
            

    * - `ZREVRANK <https://redis.io/commands/zrevrank>`_

        Determine the index of a member in a sorted set, with scores ordered from high to low
      - :meth:`~coredis.StrictRedis.zrevrank`

        
        
        
        


      
            

    * - `ZSCAN <https://redis.io/commands/zscan>`_

        Incrementally iterate sorted sets elements and associated scores
      - :meth:`~coredis.StrictRedis.zscan`

        
        
        
        


      
            

    * - `ZSCORE <https://redis.io/commands/zscore>`_

        Get the score associated with the given member in a sorted set
      - :meth:`~coredis.StrictRedis.zscore`

        
        
        
        


      
            

    * - `ZUNION <https://redis.io/commands/zunion>`_

        Add multiple sorted sets
      - :meth:`~coredis.StrictRedis.zunion`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZUNIONSTORE <https://redis.io/commands/zunionstore>`_

        Add multiple sorted sets and store the resulting sorted set in a new key
      - :meth:`~coredis.StrictRedis.zunionstore`

        
        
        
        


      
            

Generic
-------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `DEL <https://redis.io/commands/del>`_

        Delete a key
      - :meth:`~coredis.StrictRedis.delete`

        
        
        
        


      
            

    * - `DUMP <https://redis.io/commands/dump>`_

        Return a serialized version of the value stored at the specified key.
      - :meth:`~coredis.StrictRedis.dump`

        
        
        
        


      
            

    * - `EXISTS <https://redis.io/commands/exists>`_

        Determine if a key exists
      - :meth:`~coredis.StrictRedis.exists`

        
        
        
        


      
            

    * - `EXPIRE <https://redis.io/commands/expire>`_

        Set a key's time to live in seconds
      - :meth:`~coredis.StrictRedis.expire`

        
        
        
        


      
            

    * - `EXPIREAT <https://redis.io/commands/expireat>`_

        Set the expiration for a key as a UNIX timestamp
      - :meth:`~coredis.StrictRedis.expireat`

        
        
        
        


      
            

    * - `KEYS <https://redis.io/commands/keys>`_

        Find all keys matching the given pattern
      - :meth:`~coredis.StrictRedis.keys`

        
        
        
        


      
            

    * - `MOVE <https://redis.io/commands/move>`_

        Move a key to another database
      - :meth:`~coredis.StrictRedis.move`

        
        
        
        


      
            

    * - `OBJECT ENCODING <https://redis.io/commands/object-encoding>`_

        Inspect the internal encoding of a Redis object
      - :meth:`~coredis.StrictRedis.object_encoding`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `OBJECT FREQ <https://redis.io/commands/object-freq>`_

        Get the logarithmic access frequency counter of a Redis object
      - :meth:`~coredis.StrictRedis.object_freq`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `OBJECT IDLETIME <https://redis.io/commands/object-idletime>`_

        Get the time since a Redis object was last accessed
      - :meth:`~coredis.StrictRedis.object_idletime`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `OBJECT REFCOUNT <https://redis.io/commands/object-refcount>`_

        Get the number of references to the value of the key
      - :meth:`~coredis.StrictRedis.object_refcount`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `PERSIST <https://redis.io/commands/persist>`_

        Remove the expiration from a key
      - :meth:`~coredis.StrictRedis.persist`

        
        
        
        


      
            

    * - `PEXPIRE <https://redis.io/commands/pexpire>`_

        Set a key's time to live in milliseconds
      - :meth:`~coredis.StrictRedis.pexpire`

        
        
        
        


      
            

    * - `PEXPIREAT <https://redis.io/commands/pexpireat>`_

        Set the expiration for a key as a UNIX timestamp specified in milliseconds
      - :meth:`~coredis.StrictRedis.pexpireat`

        
        
        
        


      
            

    * - `PTTL <https://redis.io/commands/pttl>`_

        Get the time to live for a key in milliseconds
      - :meth:`~coredis.StrictRedis.pttl`

        
        
        
        


      
            

    * - `RANDOMKEY <https://redis.io/commands/randomkey>`_

        Return a random key from the keyspace
      - :meth:`~coredis.StrictRedis.randomkey`

        
        
        
        


      
            

    * - `RENAME <https://redis.io/commands/rename>`_

        Rename a key
      - :meth:`~coredis.StrictRedis.rename`

        
        
        
        


      
            

    * - `RENAMENX <https://redis.io/commands/renamenx>`_

        Rename a key, only if the new key does not exist
      - :meth:`~coredis.StrictRedis.renamenx`

        
        
        
        


      
            

    * - `RESTORE <https://redis.io/commands/restore>`_

        Create a key using the provided serialized value, previously obtained using DUMP.
      - :meth:`~coredis.StrictRedis.restore`

        
        
        
        


      
            

    * - `SCAN <https://redis.io/commands/scan>`_

        Incrementally iterate the keys space
      - :meth:`~coredis.StrictRedis.scan`

        
        
        
        


      
            

    * - `SORT <https://redis.io/commands/sort>`_

        Sort the elements in a list, set or sorted set
      - :meth:`~coredis.StrictRedis.sort`

        
        
        
        


      
            

    * - `TOUCH <https://redis.io/commands/touch>`_

        Alters the last access time of a key(s). Returns the number of existing keys specified.
      - :meth:`~coredis.StrictRedis.touch`

        
        
        
        


      
            

    * - `TTL <https://redis.io/commands/ttl>`_

        Get the time to live for a key in seconds
      - :meth:`~coredis.StrictRedis.ttl`

        
        
        
        


      
            

    * - `TYPE <https://redis.io/commands/type>`_

        Determine the type stored at key
      - :meth:`~coredis.StrictRedis.type`

        
        
        
        


      
            

    * - `UNLINK <https://redis.io/commands/unlink>`_

        Delete a key asynchronously in another thread. Otherwise it is just as DEL, but non blocking.
      - :meth:`~coredis.StrictRedis.unlink`

        
        
        
        


      
            

    * - `WAIT <https://redis.io/commands/wait>`_

        Wait for the synchronous replication of all the write commands sent in the context of the current connection
      - :meth:`~coredis.StrictRedis.wait`

        
        
        
        


      
            

    * - `COPY <https://redis.io/commands/copy>`_

        Copy a key
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.copy`
        
        🎉 New in redis: 6.2.0
      
                    

    * - `MIGRATE <https://redis.io/commands/migrate>`_

        Atomically transfer a key from a Redis instance to another one.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.migrate`
        
        
      
                    

Transactions
------------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `UNWATCH <https://redis.io/commands/unwatch>`_

        Forget about all watched keys
      - :meth:`~coredis.StrictRedis.unwatch`

        
        
        
        


      
            

    * - `WATCH <https://redis.io/commands/watch>`_

        Watch the given keys to determine execution of the MULTI/EXEC block
      - :meth:`~coredis.StrictRedis.watch`

        
        
        
        


      
            

    * - `DISCARD <https://redis.io/commands/discard>`_

        Discard all commands issued after MULTI
      - Not Implemented.

        
        
      
       

    * - `EXEC <https://redis.io/commands/exec>`_

        Execute all commands issued after MULTI
      - Not Implemented.

        
        
      
       

    * - `MULTI <https://redis.io/commands/multi>`_

        Mark the start of a transaction block
      - Not Implemented.

        
        
      
       

Scripting
---------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `EVAL <https://redis.io/commands/eval>`_

        Execute a Lua script server side
      - :meth:`~coredis.StrictRedis.eval`

        
        
        
        


      
            

    * - `EVALSHA <https://redis.io/commands/evalsha>`_

        Execute a Lua script server side
      - :meth:`~coredis.StrictRedis.evalsha`

        
        
        
        


      
            

    * - `SCRIPT EXISTS <https://redis.io/commands/script-exists>`_

        Check existence of scripts in the script cache.
      - :meth:`~coredis.StrictRedis.script_exists`

        
        
        
        


      
            

    * - `SCRIPT FLUSH <https://redis.io/commands/script-flush>`_

        Remove all the scripts from the script cache.
      - :meth:`~coredis.StrictRedis.script_flush`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `SCRIPT KILL <https://redis.io/commands/script-kill>`_

        Kill the script currently in execution.
      - :meth:`~coredis.StrictRedis.script_kill`

        
        
        
        


      
            

    * - `SCRIPT LOAD <https://redis.io/commands/script-load>`_

        Load the specified Lua script into the script cache.
      - :meth:`~coredis.StrictRedis.script_load`

        
        
        
        


      
            

    * - `SCRIPT DEBUG <https://redis.io/commands/script-debug>`_

        Set the debug mode for executed scripts.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.script_debug`
        
        
      
                    

Geo
---

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `GEOADD <https://redis.io/commands/geoadd>`_

        Add one or more geospatial items in the geospatial index represented using a sorted set
      - :meth:`~coredis.StrictRedis.geoadd`

        
        
        
        


      
            

    * - `GEODIST <https://redis.io/commands/geodist>`_

        Returns the distance between two members of a geospatial index
      - :meth:`~coredis.StrictRedis.geodist`

        
        
        
        


      
            

    * - `GEOHASH <https://redis.io/commands/geohash>`_

        Returns members of a geospatial index as standard geohash strings
      - :meth:`~coredis.StrictRedis.geohash`

        
        
        
        


      
            

    * - `GEOPOS <https://redis.io/commands/geopos>`_

        Returns longitude and latitude of members of a geospatial index
      - :meth:`~coredis.StrictRedis.geopos`

        
        
        
        


      
            

    * - `GEORADIUS <https://redis.io/commands/georadius>`_

        Query a sorted set representing a geospatial index to fetch members matching a given maximum distance from a point
      - :meth:`~coredis.StrictRedis.georadius`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedis.geosearch`  and ``GEOSEARCHSTORE`` with the ``BYRADIUS`` argument
        


      
            

    * - `GEORADIUSBYMEMBER <https://redis.io/commands/georadiusbymember>`_

        Query a sorted set representing a geospatial index to fetch members matching a given maximum distance from a member
      - :meth:`~coredis.StrictRedis.georadiusbymember`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedis.geosearch`  and ``GEOSEARCHSTORE`` with the ``BYRADIUS`` and ``FROMMEMBER`` arguments
        


      
            

    * - `GEOSEARCH <https://redis.io/commands/geosearch>`_

        Query a sorted set representing a geospatial index to fetch members inside an area of a box or a circle.
      - :meth:`~coredis.StrictRedis.geosearch`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `GEOSEARCHSTORE <https://redis.io/commands/geosearchstore>`_

        Query a sorted set representing a geospatial index to fetch members inside an area of a box or a circle, and store the result in another key.
      - :meth:`~coredis.StrictRedis.geosearchstore`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

Hash
----

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `HDEL <https://redis.io/commands/hdel>`_

        Delete one or more hash fields
      - :meth:`~coredis.StrictRedis.hdel`

        
        
        
        


      
            

    * - `HEXISTS <https://redis.io/commands/hexists>`_

        Determine if a hash field exists
      - :meth:`~coredis.StrictRedis.hexists`

        
        
        
        


      
            

    * - `HGET <https://redis.io/commands/hget>`_

        Get the value of a hash field
      - :meth:`~coredis.StrictRedis.hget`

        
        
        
        


      
            

    * - `HGETALL <https://redis.io/commands/hgetall>`_

        Get all the fields and values in a hash
      - :meth:`~coredis.StrictRedis.hgetall`

        
        
        
        


      
            

    * - `HINCRBY <https://redis.io/commands/hincrby>`_

        Increment the integer value of a hash field by the given number
      - :meth:`~coredis.StrictRedis.hincrby`

        
        
        
        


      
            

    * - `HINCRBYFLOAT <https://redis.io/commands/hincrbyfloat>`_

        Increment the float value of a hash field by the given amount
      - :meth:`~coredis.StrictRedis.hincrbyfloat`

        
        
        
        


      
            

    * - `HKEYS <https://redis.io/commands/hkeys>`_

        Get all the fields in a hash
      - :meth:`~coredis.StrictRedis.hkeys`

        
        
        
        


      
            

    * - `HLEN <https://redis.io/commands/hlen>`_

        Get the number of fields in a hash
      - :meth:`~coredis.StrictRedis.hlen`

        
        
        
        


      
            

    * - `HMGET <https://redis.io/commands/hmget>`_

        Get the values of all the given hash fields
      - :meth:`~coredis.StrictRedis.hmget`

        
        
        
        


      
            

    * - `HMSET <https://redis.io/commands/hmset>`_

        Set multiple hash fields to multiple values
      - :meth:`~coredis.StrictRedis.hmset`

        
        - ☠️ Deprecated in redis: 4.0.0.
        - Use :meth:`~coredis.StrictRedis.hset`  with multiple field-value pairs
        


      
            

    * - `HRANDFIELD <https://redis.io/commands/hrandfield>`_

        Get one or multiple random fields from a hash
      - :meth:`~coredis.StrictRedis.hrandfield`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `HSCAN <https://redis.io/commands/hscan>`_

        Incrementally iterate hash fields and associated values
      - :meth:`~coredis.StrictRedis.hscan`

        
        
        
        


      
            

    * - `HSET <https://redis.io/commands/hset>`_

        Set the string value of a hash field
      - :meth:`~coredis.StrictRedis.hset`

        
        
        
        


      
            

    * - `HSETNX <https://redis.io/commands/hsetnx>`_

        Set the value of a hash field, only if the field does not exist
      - :meth:`~coredis.StrictRedis.hsetnx`

        
        
        
        


      
            

    * - `HSTRLEN <https://redis.io/commands/hstrlen>`_

        Get the length of the value of a hash field
      - :meth:`~coredis.StrictRedis.hstrlen`

        
        
        
        


      
            

    * - `HVALS <https://redis.io/commands/hvals>`_

        Get all the values in a hash
      - :meth:`~coredis.StrictRedis.hvals`

        
        
        
        


      
            

Hyperloglog
-----------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `PFADD <https://redis.io/commands/pfadd>`_

        Adds the specified elements to the specified HyperLogLog.
      - :meth:`~coredis.StrictRedis.pfadd`

        
        
        
        


      
            

    * - `PFCOUNT <https://redis.io/commands/pfcount>`_

        Return the approximated cardinality of the set(s) observed by the HyperLogLog at key(s).
      - :meth:`~coredis.StrictRedis.pfcount`

        
        
        
        


      
            

    * - `PFMERGE <https://redis.io/commands/pfmerge>`_

        Merge N different HyperLogLogs into a single one.
      - :meth:`~coredis.StrictRedis.pfmerge`

        
        
        
        


      
            

    * - `PFDEBUG <https://redis.io/commands/pfdebug>`_

        Internal commands for debugging HyperLogLog values
      - Not Implemented.

        
        
      
       

    * - `PFSELFTEST <https://redis.io/commands/pfselftest>`_

        An internal command for testing HyperLogLog values
      - Not Implemented.

        
        
      
       

Pubsub
------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `PUBLISH <https://redis.io/commands/publish>`_

        Post a message to a channel
      - :meth:`~coredis.StrictRedis.publish`

        
        
        
        


      
            

    * - `PUBSUB CHANNELS <https://redis.io/commands/pubsub-channels>`_

        List active channels
      - :meth:`~coredis.StrictRedis.pubsub_channels`

        
        
        
        


      
            

    * - `PUBSUB NUMPAT <https://redis.io/commands/pubsub-numpat>`_

        Get the count of unique patterns pattern subscriptions
      - :meth:`~coredis.StrictRedis.pubsub_numpat`

        
        
        
        


      
            

    * - `PUBSUB NUMSUB <https://redis.io/commands/pubsub-numsub>`_

        Get the count of subscribers for channels
      - :meth:`~coredis.StrictRedis.pubsub_numsub`

        
        
        
        


      
            

    * - `PSUBSCRIBE <https://redis.io/commands/psubscribe>`_

        Listen for messages published to channels matching the given patterns
      - Not Implemented.

        
        
      
       

    * - `PUNSUBSCRIBE <https://redis.io/commands/punsubscribe>`_

        Stop listening for messages posted to channels matching the given patterns
      - Not Implemented.

        
        
      
       

    * - `SUBSCRIBE <https://redis.io/commands/subscribe>`_

        Listen for messages published to the given channels
      - Not Implemented.

        
        
      
       

    * - `UNSUBSCRIBE <https://redis.io/commands/unsubscribe>`_

        Stop listening for messages posted to the given channels
      - Not Implemented.

        
        
      
       

Set
---

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `SADD <https://redis.io/commands/sadd>`_

        Add one or more members to a set
      - :meth:`~coredis.StrictRedis.sadd`

        
        
        
        


      
            

    * - `SCARD <https://redis.io/commands/scard>`_

        Get the number of members in a set
      - :meth:`~coredis.StrictRedis.scard`

        
        
        
        


      
            

    * - `SDIFF <https://redis.io/commands/sdiff>`_

        Subtract multiple sets
      - :meth:`~coredis.StrictRedis.sdiff`

        
        
        
        


      
            

    * - `SDIFFSTORE <https://redis.io/commands/sdiffstore>`_

        Subtract multiple sets and store the resulting set in a key
      - :meth:`~coredis.StrictRedis.sdiffstore`

        
        
        
        


      
            

    * - `SINTER <https://redis.io/commands/sinter>`_

        Intersect multiple sets
      - :meth:`~coredis.StrictRedis.sinter`

        
        
        
        


      
            

    * - `SINTERSTORE <https://redis.io/commands/sinterstore>`_

        Intersect multiple sets and store the resulting set in a key
      - :meth:`~coredis.StrictRedis.sinterstore`

        
        
        
        


      
            

    * - `SISMEMBER <https://redis.io/commands/sismember>`_

        Determine if a given value is a member of a set
      - :meth:`~coredis.StrictRedis.sismember`

        
        
        
        


      
            

    * - `SMEMBERS <https://redis.io/commands/smembers>`_

        Get all the members in a set
      - :meth:`~coredis.StrictRedis.smembers`

        
        
        
        


      
            

    * - `SMISMEMBER <https://redis.io/commands/smismember>`_

        Returns the membership associated with the given elements for a set
      - :meth:`~coredis.StrictRedis.smismember`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `SMOVE <https://redis.io/commands/smove>`_

        Move a member from one set to another
      - :meth:`~coredis.StrictRedis.smove`

        
        
        
        


      
            

    * - `SPOP <https://redis.io/commands/spop>`_

        Remove and return one or multiple random members from a set
      - :meth:`~coredis.StrictRedis.spop`

        
        
        
        


      
            

    * - `SRANDMEMBER <https://redis.io/commands/srandmember>`_

        Get one or multiple random members from a set
      - :meth:`~coredis.StrictRedis.srandmember`

        
        
        
        


      
            

    * - `SREM <https://redis.io/commands/srem>`_

        Remove one or more members from a set
      - :meth:`~coredis.StrictRedis.srem`

        
        
        
        


      
            

    * - `SSCAN <https://redis.io/commands/sscan>`_

        Incrementally iterate Set elements
      - :meth:`~coredis.StrictRedis.sscan`

        
        
        
        


      
            

    * - `SUNION <https://redis.io/commands/sunion>`_

        Add multiple sets
      - :meth:`~coredis.StrictRedis.sunion`

        
        
        
        


      
            

    * - `SUNIONSTORE <https://redis.io/commands/sunionstore>`_

        Add multiple sets and store the resulting set in a key
      - :meth:`~coredis.StrictRedis.sunionstore`

        
        
        
        


      
            

Stream
------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `XACK <https://redis.io/commands/xack>`_

        Marks a pending message as correctly processed, effectively removing it from the pending entries list of the consumer group. Return value of the command is the number of messages successfully acknowledged, that is, the IDs we were actually able to resolve in the PEL.
      - :meth:`~coredis.StrictRedis.xack`

        
        
        
        


      
            

    * - `XADD <https://redis.io/commands/xadd>`_

        Appends a new entry to a stream
      - :meth:`~coredis.StrictRedis.xadd`

        
        
        
        


      
            

    * - `XCLAIM <https://redis.io/commands/xclaim>`_

        Changes (or acquires) ownership of a message in a consumer group, as if the message was delivered to the specified consumer.
      - :meth:`~coredis.StrictRedis.xclaim`

        
        
        
        


      
            

    * - `XDEL <https://redis.io/commands/xdel>`_

        Removes the specified entries from the stream. Returns the number of items actually deleted, that may be different from the number of IDs passed in case certain IDs do not exist.
      - :meth:`~coredis.StrictRedis.xdel`

        
        
        
        


      
            

    * - `XGROUP CREATE <https://redis.io/commands/xgroup-create>`_

        Create a consumer group.
      - :meth:`~coredis.StrictRedis.xgroup_create`

        
        
        
        


      
            

    * - `XGROUP DESTROY <https://redis.io/commands/xgroup-destroy>`_

        Destroy a consumer group.
      - :meth:`~coredis.StrictRedis.xgroup_destroy`

        
        
        
        


      
            

    * - `XINFO CONSUMERS <https://redis.io/commands/xinfo-consumers>`_

        List the consumers in a consumer group
      - :meth:`~coredis.StrictRedis.xinfo_consumers`

        
        
        
        


      
            

    * - `XINFO GROUPS <https://redis.io/commands/xinfo-groups>`_

        List the consumer groups of a stream
      - :meth:`~coredis.StrictRedis.xinfo_groups`

        
        
        
        


      
            

    * - `XINFO STREAM <https://redis.io/commands/xinfo-stream>`_

        Get information about a stream
      - :meth:`~coredis.StrictRedis.xinfo_stream`

        
        
        
        


      
            

    * - `XLEN <https://redis.io/commands/xlen>`_

        Return the number of entries in a stream
      - :meth:`~coredis.StrictRedis.xlen`

        
        
        
        


      
            

    * - `XPENDING <https://redis.io/commands/xpending>`_

        Return information and entries from a stream consumer group pending entries list, that are messages fetched but never acknowledged.
      - :meth:`~coredis.StrictRedis.xpending`

        
        
        
        


      
            

    * - `XRANGE <https://redis.io/commands/xrange>`_

        Return a range of elements in a stream, with IDs matching the specified IDs interval
      - :meth:`~coredis.StrictRedis.xrange`

        
        
        
        


      
            

    * - `XREAD <https://redis.io/commands/xread>`_

        Return never seen elements in multiple streams, with IDs greater than the ones reported by the caller for each stream. Can block.
      - :meth:`~coredis.StrictRedis.xread`

        
        
        
        


      
            

    * - `XREADGROUP <https://redis.io/commands/xreadgroup>`_

        Return new entries from a stream using a consumer group, or access the history of the pending entries for a given consumer. Can block.
      - :meth:`~coredis.StrictRedis.xreadgroup`

        
        
        
        


      
            

    * - `XREVRANGE <https://redis.io/commands/xrevrange>`_

        Return a range of elements in a stream, with IDs matching the specified IDs interval, in reverse order (from greater to smaller IDs) compared to XRANGE
      - :meth:`~coredis.StrictRedis.xrevrange`

        
        
        
        


      
            

    * - `XTRIM <https://redis.io/commands/xtrim>`_

        Trims the stream to (approximately if '~' is passed) a certain size
      - :meth:`~coredis.StrictRedis.xtrim`

        
        
        
        


      
            

    * - `XAUTOCLAIM <https://redis.io/commands/xautoclaim>`_

        Changes (or acquires) ownership of messages in a consumer group, as if the messages were delivered to the specified consumer.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.xautoclaim`
        
        🎉 New in redis: 6.2.0
      
                    

    * - `XGROUP CREATECONSUMER <https://redis.io/commands/xgroup-createconsumer>`_

        Create a consumer in a consumer group.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.xgroup_createconsumer`
        
        🎉 New in redis: 6.2.0
      
                    

    * - `XGROUP DELCONSUMER <https://redis.io/commands/xgroup-delconsumer>`_

        Delete a consumer from a consumer group.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.xgroup_delconsumer`
        
        
      
                    

    * - `XGROUP SETID <https://redis.io/commands/xgroup-setid>`_

        Set a consumer group to an arbitrary last delivered ID value.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.xgroup_setid`
        
        
      
                    

    * - `XSETID <https://redis.io/commands/xsetid>`_

        An internal command for replicating stream values
      - Not Implemented.

        
        
      
       

Server
------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `BGREWRITEAOF <https://redis.io/commands/bgrewriteaof>`_

        Asynchronously rewrite the append-only file
      - :meth:`~coredis.StrictRedis.bgrewriteaof`

        
        
        
        


      
            

    * - `BGSAVE <https://redis.io/commands/bgsave>`_

        Asynchronously save the dataset to disk
      - :meth:`~coredis.StrictRedis.bgsave`

        
        
        
        


      
            

    * - `CONFIG GET <https://redis.io/commands/config-get>`_

        Get the values of configuration parameters
      - :meth:`~coredis.StrictRedis.config_get`

        
        
        
        


      
            

    * - `CONFIG RESETSTAT <https://redis.io/commands/config-resetstat>`_

        Reset the stats returned by INFO
      - :meth:`~coredis.StrictRedis.config_resetstat`

        
        
        
        


      
            

    * - `CONFIG REWRITE <https://redis.io/commands/config-rewrite>`_

        Rewrite the configuration file with the in memory configuration
      - :meth:`~coredis.StrictRedis.config_rewrite`

        
        
        
        


      
            

    * - `CONFIG SET <https://redis.io/commands/config-set>`_

        Set configuration parameters to the given values
      - :meth:`~coredis.StrictRedis.config_set`

        
        
        
        


      
            

    * - `DBSIZE <https://redis.io/commands/dbsize>`_

        Return the number of keys in the selected database
      - :meth:`~coredis.StrictRedis.dbsize`

        
        
        
        


      
            

    * - `FLUSHALL <https://redis.io/commands/flushall>`_

        Remove all keys from all databases
      - :meth:`~coredis.StrictRedis.flushall`

        
        
        
        


      
            

    * - `FLUSHDB <https://redis.io/commands/flushdb>`_

        Remove all keys from the current database
      - :meth:`~coredis.StrictRedis.flushdb`

        
        
        
        


      
            

    * - `INFO <https://redis.io/commands/info>`_

        Get information and statistics about the server
      - :meth:`~coredis.StrictRedis.info`

        
        
        
        


      
            

    * - `LASTSAVE <https://redis.io/commands/lastsave>`_

        Get the UNIX time stamp of the last successful save to disk
      - :meth:`~coredis.StrictRedis.lastsave`

        
        
        
        


      
            

    * - `LOLWUT <https://redis.io/commands/lolwut>`_

        Display some computer art and the Redis version
      - :meth:`~coredis.StrictRedis.lolwut`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `ROLE <https://redis.io/commands/role>`_

        Return the role of the instance in the context of replication
      - :meth:`~coredis.StrictRedis.role`

        
        
        
        


      
            

    * - `SAVE <https://redis.io/commands/save>`_

        Synchronously save the dataset to disk
      - :meth:`~coredis.StrictRedis.save`

        
        
        
        


      
            

    * - `SHUTDOWN <https://redis.io/commands/shutdown>`_

        Synchronously save the dataset to disk and then shut down the server
      - :meth:`~coredis.StrictRedis.shutdown`

        
        
        
        


      
            

    * - `SLAVEOF <https://redis.io/commands/slaveof>`_

        Make the server a replica of another instance, or promote it as master. Deprecated starting with Redis 5. Use REPLICAOF instead.
      - :meth:`~coredis.StrictRedis.slaveof`

        
        
        
        


      
            

    * - `SLOWLOG GET <https://redis.io/commands/slowlog-get>`_

        Get the slow log's entries
      - :meth:`~coredis.StrictRedis.slowlog_get`

        
        
        
        


      
            

    * - `SLOWLOG LEN <https://redis.io/commands/slowlog-len>`_

        Get the slow log's length
      - :meth:`~coredis.StrictRedis.slowlog_len`

        
        
        
        


      
            

    * - `SLOWLOG RESET <https://redis.io/commands/slowlog-reset>`_

        Clear all entries from the slow log
      - :meth:`~coredis.StrictRedis.slowlog_reset`

        
        
        
        


      
            

    * - `TIME <https://redis.io/commands/time>`_

        Return the current server time
      - :meth:`~coredis.StrictRedis.time`

        
        
        
        


      
            

    * - `ACL CAT <https://redis.io/commands/acl-cat>`_

        List the ACL categories or the commands inside a category
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.acl_cat`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `ACL DELUSER <https://redis.io/commands/acl-deluser>`_

        Remove the specified ACL users and the associated rules
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.acl_deluser`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `ACL GENPASS <https://redis.io/commands/acl-genpass>`_

        Generate a pseudorandom secure password to use for ACL users
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.acl_genpass`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `ACL GETUSER <https://redis.io/commands/acl-getuser>`_

        Get the rules for a specific ACL user
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.acl_getuser`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `ACL LIST <https://redis.io/commands/acl-list>`_

        List the current ACL rules in ACL config file format
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.acl_list`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `ACL LOAD <https://redis.io/commands/acl-load>`_

        Reload the ACLs from the configured ACL file
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.acl_load`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `ACL LOG <https://redis.io/commands/acl-log>`_

        List latest events denied because of ACLs in place
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.acl_log`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `ACL SAVE <https://redis.io/commands/acl-save>`_

        Save the current ACL rules in the configured ACL file
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.acl_save`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `ACL SETUSER <https://redis.io/commands/acl-setuser>`_

        Modify or create the rules for a specific ACL user
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.acl_setuser`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `ACL USERS <https://redis.io/commands/acl-users>`_

        List the username of all the configured ACL rules
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.acl_users`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `ACL WHOAMI <https://redis.io/commands/acl-whoami>`_

        Return the name of the user associated to the current connection
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.acl_whoami`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `COMMAND <https://redis.io/commands/command>`_

        Get array of Redis command details
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.command`
        
        
      
                    

    * - `COMMAND COUNT <https://redis.io/commands/command-count>`_

        Get total number of Redis commands
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.command_count`
        
        
      
                    

    * - `COMMAND GETKEYS <https://redis.io/commands/command-getkeys>`_

        Extract keys given a full Redis command
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.command_getkeys`
        
        
      
                    

    * - `COMMAND INFO <https://redis.io/commands/command-info>`_

        Get array of specific Redis command details, or all when no argument is given.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.command_info`
        
        
      
                    

    * - `MEMORY DOCTOR <https://redis.io/commands/memory-doctor>`_

        Outputs memory problems report
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.memory_doctor`
        
        
      
                    

    * - `MEMORY MALLOC-STATS <https://redis.io/commands/memory-malloc-stats>`_

        Show allocator internal stats
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.memory_malloc_stats`
        
        
      
                    

    * - `MEMORY PURGE <https://redis.io/commands/memory-purge>`_

        Ask the allocator to release memory
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.memory_purge`
        
        
      
                    

    * - `MEMORY STATS <https://redis.io/commands/memory-stats>`_

        Show memory usage details
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.memory_stats`
        
        
      
                    

    * - `MEMORY USAGE <https://redis.io/commands/memory-usage>`_

        Estimate the memory usage of a key
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.memory_usage`
        
        
      
                    

    * - `MODULE LIST <https://redis.io/commands/module-list>`_

        List all modules loaded by the server
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.module_list`
        
        
      
                    

    * - `MODULE LOAD <https://redis.io/commands/module-load>`_

        Load a module
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.module_load`
        
        
      
                    

    * - `MODULE UNLOAD <https://redis.io/commands/module-unload>`_

        Unload a module
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.module_unload`
        
        
      
                    

    * - `MONITOR <https://redis.io/commands/monitor>`_

        Listen for all requests received by the server in real time
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.monitor`
        
        
      
                    

    * - `PSYNC <https://redis.io/commands/psync>`_

        Internal command used for replication
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.psync`
        
        
      
                    

    * - `REPLICAOF <https://redis.io/commands/replicaof>`_

        Make the server a replica of another instance, or promote it as master.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.replicaof`
        
        
      
                    

    * - `SWAPDB <https://redis.io/commands/swapdb>`_

        Swaps two Redis databases
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.swapdb`
        
        
      
                    

    * - `SYNC <https://redis.io/commands/sync>`_

        Internal command used for replication
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.sync`
        
        
      
                    

    * - `FAILOVER <https://redis.io/commands/failover>`_

        Start a coordinated failover between this server and one of its replicas.
      - Not Implemented.

        🎉 New in redis: 6.2.0
        
      
       

    * - `LATENCY DOCTOR <https://redis.io/commands/latency-doctor>`_

        Return a human readable latency analysis report.
      - Not Implemented.

        
        
      
       

    * - `LATENCY GRAPH <https://redis.io/commands/latency-graph>`_

        Return a latency graph for the event.
      - Not Implemented.

        
        
      
       

    * - `LATENCY HISTORY <https://redis.io/commands/latency-history>`_

        Return timestamp-latency samples for the event.
      - Not Implemented.

        
        
      
       

    * - `LATENCY LATEST <https://redis.io/commands/latency-latest>`_

        Return the latest latency samples for all events.
      - Not Implemented.

        
        
      
       

    * - `LATENCY RESET <https://redis.io/commands/latency-reset>`_

        Reset latency data for one or more events.
      - Not Implemented.

        
        
      
       

    * - `REPLCONF <https://redis.io/commands/replconf>`_

        An internal command for configuring the replication stream
      - Not Implemented.

        
        
      
       

    * - `RESTORE-ASKING <https://redis.io/commands/restore-asking>`_

        An internal command for migrating keys in a cluster
      - Not Implemented.

        
        
      
       

Connection
----------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `CLIENT GETNAME <https://redis.io/commands/client-getname>`_

        Get the current connection name
      - :meth:`~coredis.StrictRedis.client_getname`

        
        
        
        


      
            

    * - `CLIENT KILL <https://redis.io/commands/client-kill>`_

        Kill the connection of a client
      - :meth:`~coredis.StrictRedis.client_kill`

        
        
        
        


      
            

    * - `CLIENT LIST <https://redis.io/commands/client-list>`_

        Get the list of client connections
      - :meth:`~coredis.StrictRedis.client_list`

        
        
        
        


      
            

    * - `CLIENT PAUSE <https://redis.io/commands/client-pause>`_

        Stop processing commands from clients for some time
      - :meth:`~coredis.StrictRedis.client_pause`

        
        
        
        


      
            

    * - `CLIENT SETNAME <https://redis.io/commands/client-setname>`_

        Set the current connection name
      - :meth:`~coredis.StrictRedis.client_setname`

        
        
        
        


      
            

    * - `ECHO <https://redis.io/commands/echo>`_

        Echo the given string
      - :meth:`~coredis.StrictRedis.echo`

        
        
        
        


      
            

    * - `PING <https://redis.io/commands/ping>`_

        Ping the server
      - :meth:`~coredis.StrictRedis.ping`

        
        
        
        


      
            

    * - `CLIENT GETREDIR <https://redis.io/commands/client-getredir>`_

        Get tracking notifications redirection client ID if any
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.client_getredir`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `CLIENT ID <https://redis.io/commands/client-id>`_

        Returns the client ID for the current connection
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.client_id`
        
        
      
                    

    * - `CLIENT INFO <https://redis.io/commands/client-info>`_

        Returns information about the current client connection.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.client_info`
        
        🎉 New in redis: 6.2.0
      
                    

    * - `CLIENT REPLY <https://redis.io/commands/client-reply>`_

        Instruct the server whether to reply to commands
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.client_reply`
        
        
      
                    

    * - `CLIENT TRACKING <https://redis.io/commands/client-tracking>`_

        Enable or disable server assisted client side caching support
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.client_tracking`
        
        🎉 New in redis: 6.0.0
      
                    

    * - `CLIENT TRACKINGINFO <https://redis.io/commands/client-trackinginfo>`_

        Return information about server assisted client side caching for the current connection
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.client_trackinginfo`
        
        🎉 New in redis: 6.2.0
      
                    

    * - `CLIENT UNBLOCK <https://redis.io/commands/client-unblock>`_

        Unblock a client blocked in a blocking command from a different connection
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.client_unblock`
        
        
      
                    

    * - `CLIENT UNPAUSE <https://redis.io/commands/client-unpause>`_

        Resume processing of clients that were paused
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.client_unpause`
        
        🎉 New in redis: 6.2.0
      
                    

    * - `QUIT <https://redis.io/commands/quit>`_

        Close the connection
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.quit`
        
        
      
                    

    * - `RESET <https://redis.io/commands/reset>`_

        Reset the connection
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.reset`
        
        🎉 New in redis: 6.2.0
      
                    

    * - `SELECT <https://redis.io/commands/select>`_

        Change the selected database for the current connection
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.core.CoreCommands.select`
        
        
      
                    

    * - `AUTH <https://redis.io/commands/auth>`_

        Authenticate to the server
      - Not Implemented.

        
        
      
       

    * - `CLIENT CACHING <https://redis.io/commands/client-caching>`_

        Instruct the server about tracking or not keys in the next request
      - Not Implemented.

        🎉 New in redis: 6.0.0
        
      
       

    * - `HELLO <https://redis.io/commands/hello>`_

        Handshake with Redis
      - Not Implemented.

        🎉 New in redis: 6.0.0
        
      
       


Redis Cluster Client
^^^^^^^^^^^^^^^^^^^^

String
------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `APPEND <https://redis.io/commands/append>`_

        Append a value to a key
      - :meth:`~coredis.StrictRedisCluster.append`

        
        
        
        


      
            

    * - `DECR <https://redis.io/commands/decr>`_

        Decrement the integer value of a key by one
      - :meth:`~coredis.StrictRedisCluster.decr`

        
        
        
        


      
            

    * - `DECRBY <https://redis.io/commands/decrby>`_

        Decrement the integer value of a key by the given number
      - :meth:`~coredis.StrictRedisCluster.decrby`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `GET <https://redis.io/commands/get>`_

        Get the value of a key
      - :meth:`~coredis.StrictRedisCluster.get`

        
        
        
        


      
            

    * - `GETDEL <https://redis.io/commands/getdel>`_

        Get the value of a key and delete the key
      - :meth:`~coredis.StrictRedisCluster.getdel`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `GETEX <https://redis.io/commands/getex>`_

        Get the value of a key and optionally set its expiration
      - :meth:`~coredis.StrictRedisCluster.getex`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `GETRANGE <https://redis.io/commands/getrange>`_

        Get a substring of the string stored at a key
      - :meth:`~coredis.StrictRedisCluster.getrange`

        
        
        
        


      
            

    * - `GETSET <https://redis.io/commands/getset>`_

        Set the string value of a key and return its old value
      - :meth:`~coredis.StrictRedisCluster.getset`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedisCluster.set`  with the ``!GET`` argument
        


      
            

    * - `INCR <https://redis.io/commands/incr>`_

        Increment the integer value of a key by one
      - :meth:`~coredis.StrictRedisCluster.incr`

        
        
        
        


      
            

    * - `INCRBY <https://redis.io/commands/incrby>`_

        Increment the integer value of a key by the given amount
      - :meth:`~coredis.StrictRedisCluster.incrby`

        
        
        
        


      
            

    * - `INCRBYFLOAT <https://redis.io/commands/incrbyfloat>`_

        Increment the float value of a key by the given amount
      - :meth:`~coredis.StrictRedisCluster.incrbyfloat`

        
        
        
        


      
            

    * - `MGET <https://redis.io/commands/mget>`_

        Get the values of all the given keys
      - :meth:`~coredis.StrictRedisCluster.mget`

        
        
        
        


      
            

    * - `MSET <https://redis.io/commands/mset>`_

        Set multiple keys to multiple values
      - :meth:`~coredis.StrictRedisCluster.mset`

        
        
        
        


      
            

    * - `MSETNX <https://redis.io/commands/msetnx>`_

        Set multiple keys to multiple values, only if none of the keys exist
      - :meth:`~coredis.StrictRedisCluster.msetnx`

        
        
        
        


      
            

    * - `PSETEX <https://redis.io/commands/psetex>`_

        Set the value and expiration in milliseconds of a key
      - :meth:`~coredis.StrictRedisCluster.psetex`

        
        
        
        


      
            

    * - `SET <https://redis.io/commands/set>`_

        Set the string value of a key
      - :meth:`~coredis.StrictRedisCluster.set`

        
        
        
        


      
            

    * - `SETEX <https://redis.io/commands/setex>`_

        Set the value and expiration of a key
      - :meth:`~coredis.StrictRedisCluster.setex`

        
        
        
        


      
            

    * - `SETNX <https://redis.io/commands/setnx>`_

        Set the value of a key, only if the key does not exist
      - :meth:`~coredis.StrictRedisCluster.setnx`

        
        
        
        


      
            

    * - `SETRANGE <https://redis.io/commands/setrange>`_

        Overwrite part of a string at key starting at the specified offset
      - :meth:`~coredis.StrictRedisCluster.setrange`

        
        
        
        


      
            

    * - `STRLEN <https://redis.io/commands/strlen>`_

        Get the length of the value stored in a key
      - :meth:`~coredis.StrictRedisCluster.strlen`

        
        
        
        


      
            

    * - `SUBSTR <https://redis.io/commands/substr>`_

        Get a substring of the string stored at a key
      - :meth:`~coredis.StrictRedisCluster.substr`

        
        - ☠️ Deprecated in redis: 2.0.0.
        - Use :meth:`~coredis.StrictRedisCluster.getrange` 
        


      
            

Bitmap
------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `BITCOUNT <https://redis.io/commands/bitcount>`_

        Count set bits in a string
      - :meth:`~coredis.StrictRedisCluster.bitcount`

        
        
        
        


      
            

    * - `BITFIELD <https://redis.io/commands/bitfield>`_

        Perform arbitrary bitfield integer operations on strings
      - :meth:`~coredis.StrictRedisCluster.bitfield`

        
        
        
        


      
            

    * - `BITFIELD_RO <https://redis.io/commands/bitfield_ro>`_

        Perform arbitrary bitfield integer operations on strings. Read-only variant of BITFIELD
      - :meth:`~coredis.StrictRedisCluster.bitfield_ro`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `BITOP <https://redis.io/commands/bitop>`_

        Perform bitwise operations between strings
      - :meth:`~coredis.StrictRedisCluster.bitop`

        
        
        
        


      
            

    * - `BITPOS <https://redis.io/commands/bitpos>`_

        Find first bit set or clear in a string
      - :meth:`~coredis.StrictRedisCluster.bitpos`

        
        
        
        


      
            

    * - `GETBIT <https://redis.io/commands/getbit>`_

        Returns the bit value at offset in the string value stored at key
      - :meth:`~coredis.StrictRedisCluster.getbit`

        
        
        
        


      
            

    * - `SETBIT <https://redis.io/commands/setbit>`_

        Sets or clears the bit at offset in the string value stored at key
      - :meth:`~coredis.StrictRedisCluster.setbit`

        
        
        
        


      
            

List
----

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `BLMOVE <https://redis.io/commands/blmove>`_

        Pop an element from a list, push it to another list and return it; or block until one is available
      - :meth:`~coredis.StrictRedisCluster.blmove`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `BLPOP <https://redis.io/commands/blpop>`_

        Remove and get the first element in a list, or block until one is available
      - :meth:`~coredis.StrictRedisCluster.blpop`

        
        
        
        


      
            

    * - `BRPOP <https://redis.io/commands/brpop>`_

        Remove and get the last element in a list, or block until one is available
      - :meth:`~coredis.StrictRedisCluster.brpop`

        
        
        
        


      
            

    * - `BRPOPLPUSH <https://redis.io/commands/brpoplpush>`_

        Pop an element from a list, push it to another list and return it; or block until one is available
      - :meth:`~coredis.StrictRedisCluster.brpoplpush`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedisCluster.blmove`  with the ``RIGHT`` and ``LEFT`` arguments
        


      
            

    * - `LINDEX <https://redis.io/commands/lindex>`_

        Get an element from a list by its index
      - :meth:`~coredis.StrictRedisCluster.lindex`

        
        
        
        


      
            

    * - `LINSERT <https://redis.io/commands/linsert>`_

        Insert an element before or after another element in a list
      - :meth:`~coredis.StrictRedisCluster.linsert`

        
        
        
        


      
            

    * - `LLEN <https://redis.io/commands/llen>`_

        Get the length of a list
      - :meth:`~coredis.StrictRedisCluster.llen`

        
        
        
        


      
            

    * - `LMOVE <https://redis.io/commands/lmove>`_

        Pop an element from a list, push it to another list and return it
      - :meth:`~coredis.StrictRedisCluster.lmove`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `LPOP <https://redis.io/commands/lpop>`_

        Remove and get the first elements in a list
      - :meth:`~coredis.StrictRedisCluster.lpop`

        
        
        
        


      
            

    * - `LPOS <https://redis.io/commands/lpos>`_

        Return the index of matching elements on a list
      - :meth:`~coredis.StrictRedisCluster.lpos`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.0.6


      
            

    * - `LPUSH <https://redis.io/commands/lpush>`_

        Prepend one or multiple elements to a list
      - :meth:`~coredis.StrictRedisCluster.lpush`

        
        
        
        


      
            

    * - `LPUSHX <https://redis.io/commands/lpushx>`_

        Prepend an element to a list, only if the list exists
      - :meth:`~coredis.StrictRedisCluster.lpushx`

        
        
        
        


      
            

    * - `LRANGE <https://redis.io/commands/lrange>`_

        Get a range of elements from a list
      - :meth:`~coredis.StrictRedisCluster.lrange`

        
        
        
        


      
            

    * - `LREM <https://redis.io/commands/lrem>`_

        Remove elements from a list
      - :meth:`~coredis.StrictRedisCluster.lrem`

        
        
        
        


      
            

    * - `LSET <https://redis.io/commands/lset>`_

        Set the value of an element in a list by its index
      - :meth:`~coredis.StrictRedisCluster.lset`

        
        
        
        


      
            

    * - `LTRIM <https://redis.io/commands/ltrim>`_

        Trim a list to the specified range
      - :meth:`~coredis.StrictRedisCluster.ltrim`

        
        
        
        


      
            

    * - `RPOP <https://redis.io/commands/rpop>`_

        Remove and get the last elements in a list
      - :meth:`~coredis.StrictRedisCluster.rpop`

        
        
        
        


      
            

    * - `RPOPLPUSH <https://redis.io/commands/rpoplpush>`_

        Remove the last element in a list, prepend it to another list and return it
      - :meth:`~coredis.StrictRedisCluster.rpoplpush`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedisCluster.lmove`  with the ``RIGHT`` and ``LEFT`` arguments
        


      
            

    * - `RPUSH <https://redis.io/commands/rpush>`_

        Append one or multiple elements to a list
      - :meth:`~coredis.StrictRedisCluster.rpush`

        
        
        
        


      
            

    * - `RPUSHX <https://redis.io/commands/rpushx>`_

        Append an element to a list, only if the list exists
      - :meth:`~coredis.StrictRedisCluster.rpushx`

        
        
        
        


      
            

Sorted-Set
----------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `BZPOPMAX <https://redis.io/commands/bzpopmax>`_

        Remove and return the member with the highest score from one or more sorted sets, or block until one is available
      - :meth:`~coredis.StrictRedisCluster.bzpopmax`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `BZPOPMIN <https://redis.io/commands/bzpopmin>`_

        Remove and return the member with the lowest score from one or more sorted sets, or block until one is available
      - :meth:`~coredis.StrictRedisCluster.bzpopmin`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `ZADD <https://redis.io/commands/zadd>`_

        Add one or more members to a sorted set, or update its score if it already exists
      - :meth:`~coredis.StrictRedisCluster.zadd`

        
        
        
        


      
            

    * - `ZCARD <https://redis.io/commands/zcard>`_

        Get the number of members in a sorted set
      - :meth:`~coredis.StrictRedisCluster.zcard`

        
        
        
        


      
            

    * - `ZCOUNT <https://redis.io/commands/zcount>`_

        Count the members in a sorted set with scores within the given values
      - :meth:`~coredis.StrictRedisCluster.zcount`

        
        
        
        


      
            

    * - `ZDIFF <https://redis.io/commands/zdiff>`_

        Subtract multiple sorted sets
      - :meth:`~coredis.StrictRedisCluster.zdiff`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZDIFFSTORE <https://redis.io/commands/zdiffstore>`_

        Subtract multiple sorted sets and store the resulting sorted set in a new key
      - :meth:`~coredis.StrictRedisCluster.zdiffstore`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZINCRBY <https://redis.io/commands/zincrby>`_

        Increment the score of a member in a sorted set
      - :meth:`~coredis.StrictRedisCluster.zincrby`

        
        
        
        


      
            

    * - `ZINTER <https://redis.io/commands/zinter>`_

        Intersect multiple sorted sets
      - :meth:`~coredis.StrictRedisCluster.zinter`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZINTERSTORE <https://redis.io/commands/zinterstore>`_

        Intersect multiple sorted sets and store the resulting sorted set in a new key
      - :meth:`~coredis.StrictRedisCluster.zinterstore`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `ZLEXCOUNT <https://redis.io/commands/zlexcount>`_

        Count the number of members in a sorted set between a given lexicographical range
      - :meth:`~coredis.StrictRedisCluster.zlexcount`

        
        
        
        


      
            

    * - `ZMSCORE <https://redis.io/commands/zmscore>`_

        Get the score associated with the given members in a sorted set
      - :meth:`~coredis.StrictRedisCluster.zmscore`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZPOPMAX <https://redis.io/commands/zpopmax>`_

        Remove and return members with the highest scores in a sorted set
      - :meth:`~coredis.StrictRedisCluster.zpopmax`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `ZPOPMIN <https://redis.io/commands/zpopmin>`_

        Remove and return members with the lowest scores in a sorted set
      - :meth:`~coredis.StrictRedisCluster.zpopmin`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `ZRANDMEMBER <https://redis.io/commands/zrandmember>`_

        Get one or multiple random elements from a sorted set
      - :meth:`~coredis.StrictRedisCluster.zrandmember`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZRANGE <https://redis.io/commands/zrange>`_

        Return a range of members in a sorted set
      - :meth:`~coredis.StrictRedisCluster.zrange`

        
        
        
        


      
            

    * - `ZRANGEBYLEX <https://redis.io/commands/zrangebylex>`_

        Return a range of members in a sorted set, by lexicographical range
      - :meth:`~coredis.StrictRedisCluster.zrangebylex`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedisCluster.zrange`  with the ``BYSCORE`` argument
        


      
            

    * - `ZRANGEBYSCORE <https://redis.io/commands/zrangebyscore>`_

        Return a range of members in a sorted set, by score
      - :meth:`~coredis.StrictRedisCluster.zrangebyscore`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedisCluster.zrange`  with the ``BYSCORE`` argument
        


      
            

    * - `ZRANGESTORE <https://redis.io/commands/zrangestore>`_

        Store a range of members from sorted set into another key
      - :meth:`~coredis.StrictRedisCluster.zrangestore`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZRANK <https://redis.io/commands/zrank>`_

        Determine the index of a member in a sorted set
      - :meth:`~coredis.StrictRedisCluster.zrank`

        
        
        
        


      
            

    * - `ZREM <https://redis.io/commands/zrem>`_

        Remove one or more members from a sorted set
      - :meth:`~coredis.StrictRedisCluster.zrem`

        
        
        
        


      
            

    * - `ZREMRANGEBYLEX <https://redis.io/commands/zremrangebylex>`_

        Remove all members in a sorted set between the given lexicographical range
      - :meth:`~coredis.StrictRedisCluster.zremrangebylex`

        
        
        
        


      
            

    * - `ZREMRANGEBYRANK <https://redis.io/commands/zremrangebyrank>`_

        Remove all members in a sorted set within the given indexes
      - :meth:`~coredis.StrictRedisCluster.zremrangebyrank`

        
        
        
        


      
            

    * - `ZREMRANGEBYSCORE <https://redis.io/commands/zremrangebyscore>`_

        Remove all members in a sorted set within the given scores
      - :meth:`~coredis.StrictRedisCluster.zremrangebyscore`

        
        
        
        


      
            

    * - `ZREVRANGE <https://redis.io/commands/zrevrange>`_

        Return a range of members in a sorted set, by index, with scores ordered from high to low
      - :meth:`~coredis.StrictRedisCluster.zrevrange`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedisCluster.zrange`  with the ``REV`` argument
        


      
            

    * - `ZREVRANGEBYLEX <https://redis.io/commands/zrevrangebylex>`_

        Return a range of members in a sorted set, by lexicographical range, ordered from higher to lower strings.
      - :meth:`~coredis.StrictRedisCluster.zrevrangebylex`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedisCluster.zrange`  with the ``REV`` and ``BYLEX`` arguments
        


      
            

    * - `ZREVRANGEBYSCORE <https://redis.io/commands/zrevrangebyscore>`_

        Return a range of members in a sorted set, by score, with scores ordered from high to low
      - :meth:`~coredis.StrictRedisCluster.zrevrangebyscore`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedisCluster.zrange`  with the ``REV`` and ``BYSCORE`` arguments
        


      
            

    * - `ZREVRANK <https://redis.io/commands/zrevrank>`_

        Determine the index of a member in a sorted set, with scores ordered from high to low
      - :meth:`~coredis.StrictRedisCluster.zrevrank`

        
        
        
        


      
            

    * - `ZSCAN <https://redis.io/commands/zscan>`_

        Incrementally iterate sorted sets elements and associated scores
      - :meth:`~coredis.StrictRedisCluster.zscan`

        
        
        
        


      
            

    * - `ZSCORE <https://redis.io/commands/zscore>`_

        Get the score associated with the given member in a sorted set
      - :meth:`~coredis.StrictRedisCluster.zscore`

        
        
        
        


      
            

    * - `ZUNION <https://redis.io/commands/zunion>`_

        Add multiple sorted sets
      - :meth:`~coredis.StrictRedisCluster.zunion`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `ZUNIONSTORE <https://redis.io/commands/zunionstore>`_

        Add multiple sorted sets and store the resulting sorted set in a new key
      - :meth:`~coredis.StrictRedisCluster.zunionstore`

        
        
        
        


      
            

Generic
-------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `DEL <https://redis.io/commands/del>`_

        Delete a key
      - :meth:`~coredis.StrictRedisCluster.delete`

        
        
        
        


      
            

    * - `DUMP <https://redis.io/commands/dump>`_

        Return a serialized version of the value stored at the specified key.
      - :meth:`~coredis.StrictRedisCluster.dump`

        
        
        
        


      
            

    * - `EXISTS <https://redis.io/commands/exists>`_

        Determine if a key exists
      - :meth:`~coredis.StrictRedisCluster.exists`

        
        
        
        


      
            

    * - `EXPIRE <https://redis.io/commands/expire>`_

        Set a key's time to live in seconds
      - :meth:`~coredis.StrictRedisCluster.expire`

        
        
        
        


      
            

    * - `EXPIREAT <https://redis.io/commands/expireat>`_

        Set the expiration for a key as a UNIX timestamp
      - :meth:`~coredis.StrictRedisCluster.expireat`

        
        
        
        


      
            

    * - `KEYS <https://redis.io/commands/keys>`_

        Find all keys matching the given pattern
      - :meth:`~coredis.StrictRedisCluster.keys`

        
        
        
        


      
            

    * - `MOVE <https://redis.io/commands/move>`_

        Move a key to another database
      - :meth:`~coredis.StrictRedisCluster.move`

        
        
        
        


      
            

    * - `OBJECT ENCODING <https://redis.io/commands/object-encoding>`_

        Inspect the internal encoding of a Redis object
      - :meth:`~coredis.StrictRedisCluster.object_encoding`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `OBJECT FREQ <https://redis.io/commands/object-freq>`_

        Get the logarithmic access frequency counter of a Redis object
      - :meth:`~coredis.StrictRedisCluster.object_freq`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `OBJECT IDLETIME <https://redis.io/commands/object-idletime>`_

        Get the time since a Redis object was last accessed
      - :meth:`~coredis.StrictRedisCluster.object_idletime`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `OBJECT REFCOUNT <https://redis.io/commands/object-refcount>`_

        Get the number of references to the value of the key
      - :meth:`~coredis.StrictRedisCluster.object_refcount`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `PERSIST <https://redis.io/commands/persist>`_

        Remove the expiration from a key
      - :meth:`~coredis.StrictRedisCluster.persist`

        
        
        
        


      
            

    * - `PEXPIRE <https://redis.io/commands/pexpire>`_

        Set a key's time to live in milliseconds
      - :meth:`~coredis.StrictRedisCluster.pexpire`

        
        
        
        


      
            

    * - `PEXPIREAT <https://redis.io/commands/pexpireat>`_

        Set the expiration for a key as a UNIX timestamp specified in milliseconds
      - :meth:`~coredis.StrictRedisCluster.pexpireat`

        
        
        
        


      
            

    * - `PTTL <https://redis.io/commands/pttl>`_

        Get the time to live for a key in milliseconds
      - :meth:`~coredis.StrictRedisCluster.pttl`

        
        
        
        


      
            

    * - `RANDOMKEY <https://redis.io/commands/randomkey>`_

        Return a random key from the keyspace
      - :meth:`~coredis.StrictRedisCluster.randomkey`

        
        
        
        


      
            

    * - `RENAME <https://redis.io/commands/rename>`_

        Rename a key
      - :meth:`~coredis.StrictRedisCluster.rename`

        
        
        
        


      
            

    * - `RENAMENX <https://redis.io/commands/renamenx>`_

        Rename a key, only if the new key does not exist
      - :meth:`~coredis.StrictRedisCluster.renamenx`

        
        
        
        


      
            

    * - `RESTORE <https://redis.io/commands/restore>`_

        Create a key using the provided serialized value, previously obtained using DUMP.
      - :meth:`~coredis.StrictRedisCluster.restore`

        
        
        
        


      
            

    * - `SCAN <https://redis.io/commands/scan>`_

        Incrementally iterate the keys space
      - :meth:`~coredis.StrictRedisCluster.scan`

        
        
        
        


      
            

    * - `SORT <https://redis.io/commands/sort>`_

        Sort the elements in a list, set or sorted set
      - :meth:`~coredis.StrictRedisCluster.sort`

        
        
        
        


      
            

    * - `TOUCH <https://redis.io/commands/touch>`_

        Alters the last access time of a key(s). Returns the number of existing keys specified.
      - :meth:`~coredis.StrictRedisCluster.touch`

        
        
        
        


      
            

    * - `TTL <https://redis.io/commands/ttl>`_

        Get the time to live for a key in seconds
      - :meth:`~coredis.StrictRedisCluster.ttl`

        
        
        
        


      
            

    * - `TYPE <https://redis.io/commands/type>`_

        Determine the type stored at key
      - :meth:`~coredis.StrictRedisCluster.type`

        
        
        
        


      
            

    * - `UNLINK <https://redis.io/commands/unlink>`_

        Delete a key asynchronously in another thread. Otherwise it is just as DEL, but non blocking.
      - :meth:`~coredis.StrictRedisCluster.unlink`

        
        
        
        


      
            

    * - `WAIT <https://redis.io/commands/wait>`_

        Wait for the synchronous replication of all the write commands sent in the context of the current connection
      - :meth:`~coredis.StrictRedisCluster.wait`

        
        
        
        


      
            

    * - `COPY <https://redis.io/commands/copy>`_

        Copy a key
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.cluster.RedisClusterCommands.copy`
        
        🎉 New in redis: 6.2.0
      
                    

    * - `MIGRATE <https://redis.io/commands/migrate>`_

        Atomically transfer a key from a Redis instance to another one.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.cluster.RedisClusterCommands.migrate`
        
        
      
                    

Transactions
------------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `UNWATCH <https://redis.io/commands/unwatch>`_

        Forget about all watched keys
      - :meth:`~coredis.StrictRedisCluster.unwatch`

        
        
        
        


      
            

    * - `WATCH <https://redis.io/commands/watch>`_

        Watch the given keys to determine execution of the MULTI/EXEC block
      - :meth:`~coredis.StrictRedisCluster.watch`

        
        
        
        


      
            

    * - `DISCARD <https://redis.io/commands/discard>`_

        Discard all commands issued after MULTI
      - Not Implemented.

        
        
      
       

    * - `EXEC <https://redis.io/commands/exec>`_

        Execute all commands issued after MULTI
      - Not Implemented.

        
        
      
       

    * - `MULTI <https://redis.io/commands/multi>`_

        Mark the start of a transaction block
      - Not Implemented.

        
        
      
       

Scripting
---------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `EVAL <https://redis.io/commands/eval>`_

        Execute a Lua script server side
      - :meth:`~coredis.StrictRedisCluster.eval`

        
        
        
        


      
            

    * - `EVALSHA <https://redis.io/commands/evalsha>`_

        Execute a Lua script server side
      - :meth:`~coredis.StrictRedisCluster.evalsha`

        
        
        
        


      
            

    * - `SCRIPT EXISTS <https://redis.io/commands/script-exists>`_

        Check existence of scripts in the script cache.
      - :meth:`~coredis.StrictRedisCluster.script_exists`

        
        
        
        


      
            

    * - `SCRIPT FLUSH <https://redis.io/commands/script-flush>`_

        Remove all the scripts from the script cache.
      - :meth:`~coredis.StrictRedisCluster.script_flush`

        - .. versionadded:: 2.1.0
        
        
        


      
            

    * - `SCRIPT KILL <https://redis.io/commands/script-kill>`_

        Kill the script currently in execution.
      - :meth:`~coredis.StrictRedisCluster.script_kill`

        
        
        
        


      
            

    * - `SCRIPT LOAD <https://redis.io/commands/script-load>`_

        Load the specified Lua script into the script cache.
      - :meth:`~coredis.StrictRedisCluster.script_load`

        
        
        
        


      
            

    * - `SCRIPT DEBUG <https://redis.io/commands/script-debug>`_

        Set the debug mode for executed scripts.
      - Not Implemented.

        
        
      
       

Geo
---

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `GEOADD <https://redis.io/commands/geoadd>`_

        Add one or more geospatial items in the geospatial index represented using a sorted set
      - :meth:`~coredis.StrictRedisCluster.geoadd`

        
        
        
        


      
            

    * - `GEODIST <https://redis.io/commands/geodist>`_

        Returns the distance between two members of a geospatial index
      - :meth:`~coredis.StrictRedisCluster.geodist`

        
        
        
        


      
            

    * - `GEOHASH <https://redis.io/commands/geohash>`_

        Returns members of a geospatial index as standard geohash strings
      - :meth:`~coredis.StrictRedisCluster.geohash`

        
        
        
        


      
            

    * - `GEOPOS <https://redis.io/commands/geopos>`_

        Returns longitude and latitude of members of a geospatial index
      - :meth:`~coredis.StrictRedisCluster.geopos`

        
        
        
        


      
            

    * - `GEORADIUS <https://redis.io/commands/georadius>`_

        Query a sorted set representing a geospatial index to fetch members matching a given maximum distance from a point
      - :meth:`~coredis.StrictRedisCluster.georadius`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedisCluster.geosearch`  and ``GEOSEARCHSTORE`` with the ``BYRADIUS`` argument
        


      
            

    * - `GEORADIUSBYMEMBER <https://redis.io/commands/georadiusbymember>`_

        Query a sorted set representing a geospatial index to fetch members matching a given maximum distance from a member
      - :meth:`~coredis.StrictRedisCluster.georadiusbymember`

        
        - ☠️ Deprecated in redis: 6.2.0.
        - Use :meth:`~coredis.StrictRedisCluster.geosearch`  and ``GEOSEARCHSTORE`` with the ``BYRADIUS`` and ``FROMMEMBER`` arguments
        


      
            

    * - `GEOSEARCH <https://redis.io/commands/geosearch>`_

        Query a sorted set representing a geospatial index to fetch members inside an area of a box or a circle.
      - :meth:`~coredis.StrictRedisCluster.geosearch`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `GEOSEARCHSTORE <https://redis.io/commands/geosearchstore>`_

        Query a sorted set representing a geospatial index to fetch members inside an area of a box or a circle, and store the result in another key.
      - :meth:`~coredis.StrictRedisCluster.geosearchstore`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

Hash
----

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `HDEL <https://redis.io/commands/hdel>`_

        Delete one or more hash fields
      - :meth:`~coredis.StrictRedisCluster.hdel`

        
        
        
        


      
            

    * - `HEXISTS <https://redis.io/commands/hexists>`_

        Determine if a hash field exists
      - :meth:`~coredis.StrictRedisCluster.hexists`

        
        
        
        


      
            

    * - `HGET <https://redis.io/commands/hget>`_

        Get the value of a hash field
      - :meth:`~coredis.StrictRedisCluster.hget`

        
        
        
        


      
            

    * - `HGETALL <https://redis.io/commands/hgetall>`_

        Get all the fields and values in a hash
      - :meth:`~coredis.StrictRedisCluster.hgetall`

        
        
        
        


      
            

    * - `HINCRBY <https://redis.io/commands/hincrby>`_

        Increment the integer value of a hash field by the given number
      - :meth:`~coredis.StrictRedisCluster.hincrby`

        
        
        
        


      
            

    * - `HINCRBYFLOAT <https://redis.io/commands/hincrbyfloat>`_

        Increment the float value of a hash field by the given amount
      - :meth:`~coredis.StrictRedisCluster.hincrbyfloat`

        
        
        
        


      
            

    * - `HKEYS <https://redis.io/commands/hkeys>`_

        Get all the fields in a hash
      - :meth:`~coredis.StrictRedisCluster.hkeys`

        
        
        
        


      
            

    * - `HLEN <https://redis.io/commands/hlen>`_

        Get the number of fields in a hash
      - :meth:`~coredis.StrictRedisCluster.hlen`

        
        
        
        


      
            

    * - `HMGET <https://redis.io/commands/hmget>`_

        Get the values of all the given hash fields
      - :meth:`~coredis.StrictRedisCluster.hmget`

        
        
        
        


      
            

    * - `HMSET <https://redis.io/commands/hmset>`_

        Set multiple hash fields to multiple values
      - :meth:`~coredis.StrictRedisCluster.hmset`

        
        - ☠️ Deprecated in redis: 4.0.0.
        - Use :meth:`~coredis.StrictRedisCluster.hset`  with multiple field-value pairs
        


      
            

    * - `HRANDFIELD <https://redis.io/commands/hrandfield>`_

        Get one or multiple random fields from a hash
      - :meth:`~coredis.StrictRedisCluster.hrandfield`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `HSCAN <https://redis.io/commands/hscan>`_

        Incrementally iterate hash fields and associated values
      - :meth:`~coredis.StrictRedisCluster.hscan`

        
        
        
        


      
            

    * - `HSET <https://redis.io/commands/hset>`_

        Set the string value of a hash field
      - :meth:`~coredis.StrictRedisCluster.hset`

        
        
        
        


      
            

    * - `HSETNX <https://redis.io/commands/hsetnx>`_

        Set the value of a hash field, only if the field does not exist
      - :meth:`~coredis.StrictRedisCluster.hsetnx`

        
        
        
        


      
            

    * - `HSTRLEN <https://redis.io/commands/hstrlen>`_

        Get the length of the value of a hash field
      - :meth:`~coredis.StrictRedisCluster.hstrlen`

        
        
        
        


      
            

    * - `HVALS <https://redis.io/commands/hvals>`_

        Get all the values in a hash
      - :meth:`~coredis.StrictRedisCluster.hvals`

        
        
        
        


      
            

Hyperloglog
-----------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `PFADD <https://redis.io/commands/pfadd>`_

        Adds the specified elements to the specified HyperLogLog.
      - :meth:`~coredis.StrictRedisCluster.pfadd`

        
        
        
        


      
            

    * - `PFCOUNT <https://redis.io/commands/pfcount>`_

        Return the approximated cardinality of the set(s) observed by the HyperLogLog at key(s).
      - :meth:`~coredis.StrictRedisCluster.pfcount`

        
        
        
        


      
            

    * - `PFMERGE <https://redis.io/commands/pfmerge>`_

        Merge N different HyperLogLogs into a single one.
      - :meth:`~coredis.StrictRedisCluster.pfmerge`

        
        
        
        


      
            

    * - `PFDEBUG <https://redis.io/commands/pfdebug>`_

        Internal commands for debugging HyperLogLog values
      - Not Implemented.

        
        
      
       

    * - `PFSELFTEST <https://redis.io/commands/pfselftest>`_

        An internal command for testing HyperLogLog values
      - Not Implemented.

        
        
      
       

Pubsub
------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `PUBLISH <https://redis.io/commands/publish>`_

        Post a message to a channel
      - :meth:`~coredis.StrictRedisCluster.publish`

        
        
        
        


      
            

    * - `PUBSUB CHANNELS <https://redis.io/commands/pubsub-channels>`_

        List active channels
      - :meth:`~coredis.StrictRedisCluster.pubsub_channels`

        
        
        
        


      
            

    * - `PUBSUB NUMPAT <https://redis.io/commands/pubsub-numpat>`_

        Get the count of unique patterns pattern subscriptions
      - :meth:`~coredis.StrictRedisCluster.pubsub_numpat`

        
        
        
        


      
            

    * - `PUBSUB NUMSUB <https://redis.io/commands/pubsub-numsub>`_

        Get the count of subscribers for channels
      - :meth:`~coredis.StrictRedisCluster.pubsub_numsub`

        
        
        
        


      
            

    * - `PSUBSCRIBE <https://redis.io/commands/psubscribe>`_

        Listen for messages published to channels matching the given patterns
      - Not Implemented.

        
        
      
       

    * - `PUNSUBSCRIBE <https://redis.io/commands/punsubscribe>`_

        Stop listening for messages posted to channels matching the given patterns
      - Not Implemented.

        
        
      
       

    * - `SUBSCRIBE <https://redis.io/commands/subscribe>`_

        Listen for messages published to the given channels
      - Not Implemented.

        
        
      
       

    * - `UNSUBSCRIBE <https://redis.io/commands/unsubscribe>`_

        Stop listening for messages posted to the given channels
      - Not Implemented.

        
        
      
       

Set
---

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `SADD <https://redis.io/commands/sadd>`_

        Add one or more members to a set
      - :meth:`~coredis.StrictRedisCluster.sadd`

        
        
        
        


      
            

    * - `SCARD <https://redis.io/commands/scard>`_

        Get the number of members in a set
      - :meth:`~coredis.StrictRedisCluster.scard`

        
        
        
        


      
            

    * - `SDIFF <https://redis.io/commands/sdiff>`_

        Subtract multiple sets
      - :meth:`~coredis.StrictRedisCluster.sdiff`

        
        
        
        


      
            

    * - `SDIFFSTORE <https://redis.io/commands/sdiffstore>`_

        Subtract multiple sets and store the resulting set in a key
      - :meth:`~coredis.StrictRedisCluster.sdiffstore`

        
        
        
        


      
            

    * - `SINTER <https://redis.io/commands/sinter>`_

        Intersect multiple sets
      - :meth:`~coredis.StrictRedisCluster.sinter`

        
        
        
        


      
            

    * - `SINTERSTORE <https://redis.io/commands/sinterstore>`_

        Intersect multiple sets and store the resulting set in a key
      - :meth:`~coredis.StrictRedisCluster.sinterstore`

        
        
        
        


      
            

    * - `SISMEMBER <https://redis.io/commands/sismember>`_

        Determine if a given value is a member of a set
      - :meth:`~coredis.StrictRedisCluster.sismember`

        
        
        
        


      
            

    * - `SMEMBERS <https://redis.io/commands/smembers>`_

        Get all the members in a set
      - :meth:`~coredis.StrictRedisCluster.smembers`

        
        
        
        


      
            

    * - `SMISMEMBER <https://redis.io/commands/smismember>`_

        Returns the membership associated with the given elements for a set
      - :meth:`~coredis.StrictRedisCluster.smismember`

        - .. versionadded:: 2.1.0
        
        
        - 🎉 New in redis: 6.2.0


      
            

    * - `SMOVE <https://redis.io/commands/smove>`_

        Move a member from one set to another
      - :meth:`~coredis.StrictRedisCluster.smove`

        
        
        
        


      
            

    * - `SPOP <https://redis.io/commands/spop>`_

        Remove and return one or multiple random members from a set
      - :meth:`~coredis.StrictRedisCluster.spop`

        
        
        
        


      
            

    * - `SRANDMEMBER <https://redis.io/commands/srandmember>`_

        Get one or multiple random members from a set
      - :meth:`~coredis.StrictRedisCluster.srandmember`

        
        
        
        


      
            

    * - `SREM <https://redis.io/commands/srem>`_

        Remove one or more members from a set
      - :meth:`~coredis.StrictRedisCluster.srem`

        
        
        
        


      
            

    * - `SSCAN <https://redis.io/commands/sscan>`_

        Incrementally iterate Set elements
      - :meth:`~coredis.StrictRedisCluster.sscan`

        
        
        
        


      
            

    * - `SUNION <https://redis.io/commands/sunion>`_

        Add multiple sets
      - :meth:`~coredis.StrictRedisCluster.sunion`

        
        
        
        


      
            

    * - `SUNIONSTORE <https://redis.io/commands/sunionstore>`_

        Add multiple sets and store the resulting set in a key
      - :meth:`~coredis.StrictRedisCluster.sunionstore`

        
        
        
        


      
            

Stream
------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `XACK <https://redis.io/commands/xack>`_

        Marks a pending message as correctly processed, effectively removing it from the pending entries list of the consumer group. Return value of the command is the number of messages successfully acknowledged, that is, the IDs we were actually able to resolve in the PEL.
      - :meth:`~coredis.StrictRedisCluster.xack`

        
        
        
        


      
            

    * - `XADD <https://redis.io/commands/xadd>`_

        Appends a new entry to a stream
      - :meth:`~coredis.StrictRedisCluster.xadd`

        
        
        
        


      
            

    * - `XCLAIM <https://redis.io/commands/xclaim>`_

        Changes (or acquires) ownership of a message in a consumer group, as if the message was delivered to the specified consumer.
      - :meth:`~coredis.StrictRedisCluster.xclaim`

        
        
        
        


      
            

    * - `XDEL <https://redis.io/commands/xdel>`_

        Removes the specified entries from the stream. Returns the number of items actually deleted, that may be different from the number of IDs passed in case certain IDs do not exist.
      - :meth:`~coredis.StrictRedisCluster.xdel`

        
        
        
        


      
            

    * - `XGROUP CREATE <https://redis.io/commands/xgroup-create>`_

        Create a consumer group.
      - :meth:`~coredis.StrictRedisCluster.xgroup_create`

        
        
        
        


      
            

    * - `XGROUP DESTROY <https://redis.io/commands/xgroup-destroy>`_

        Destroy a consumer group.
      - :meth:`~coredis.StrictRedisCluster.xgroup_destroy`

        
        
        
        


      
            

    * - `XINFO CONSUMERS <https://redis.io/commands/xinfo-consumers>`_

        List the consumers in a consumer group
      - :meth:`~coredis.StrictRedisCluster.xinfo_consumers`

        
        
        
        


      
            

    * - `XINFO GROUPS <https://redis.io/commands/xinfo-groups>`_

        List the consumer groups of a stream
      - :meth:`~coredis.StrictRedisCluster.xinfo_groups`

        
        
        
        


      
            

    * - `XINFO STREAM <https://redis.io/commands/xinfo-stream>`_

        Get information about a stream
      - :meth:`~coredis.StrictRedisCluster.xinfo_stream`

        
        
        
        


      
            

    * - `XLEN <https://redis.io/commands/xlen>`_

        Return the number of entries in a stream
      - :meth:`~coredis.StrictRedisCluster.xlen`

        
        
        
        


      
            

    * - `XPENDING <https://redis.io/commands/xpending>`_

        Return information and entries from a stream consumer group pending entries list, that are messages fetched but never acknowledged.
      - :meth:`~coredis.StrictRedisCluster.xpending`

        
        
        
        


      
            

    * - `XRANGE <https://redis.io/commands/xrange>`_

        Return a range of elements in a stream, with IDs matching the specified IDs interval
      - :meth:`~coredis.StrictRedisCluster.xrange`

        
        
        
        


      
            

    * - `XREAD <https://redis.io/commands/xread>`_

        Return never seen elements in multiple streams, with IDs greater than the ones reported by the caller for each stream. Can block.
      - :meth:`~coredis.StrictRedisCluster.xread`

        
        
        
        


      
            

    * - `XREADGROUP <https://redis.io/commands/xreadgroup>`_

        Return new entries from a stream using a consumer group, or access the history of the pending entries for a given consumer. Can block.
      - :meth:`~coredis.StrictRedisCluster.xreadgroup`

        
        
        
        


      
            

    * - `XREVRANGE <https://redis.io/commands/xrevrange>`_

        Return a range of elements in a stream, with IDs matching the specified IDs interval, in reverse order (from greater to smaller IDs) compared to XRANGE
      - :meth:`~coredis.StrictRedisCluster.xrevrange`

        
        
        
        


      
            

    * - `XTRIM <https://redis.io/commands/xtrim>`_

        Trims the stream to (approximately if '~' is passed) a certain size
      - :meth:`~coredis.StrictRedisCluster.xtrim`

        
        
        
        


      
            

    * - `XAUTOCLAIM <https://redis.io/commands/xautoclaim>`_

        Changes (or acquires) ownership of messages in a consumer group, as if the messages were delivered to the specified consumer.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.cluster.RedisClusterCommands.xautoclaim`
        
        🎉 New in redis: 6.2.0
      
                    

    * - `XGROUP CREATECONSUMER <https://redis.io/commands/xgroup-createconsumer>`_

        Create a consumer in a consumer group.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.cluster.RedisClusterCommands.xgroup_createconsumer`
        
        🎉 New in redis: 6.2.0
      
                    

    * - `XGROUP DELCONSUMER <https://redis.io/commands/xgroup-delconsumer>`_

        Delete a consumer from a consumer group.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.cluster.RedisClusterCommands.xgroup_delconsumer`
        
        
      
                    

    * - `XGROUP SETID <https://redis.io/commands/xgroup-setid>`_

        Set a consumer group to an arbitrary last delivered ID value.
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.cluster.RedisClusterCommands.xgroup_setid`
        
        
      
                    

    * - `XSETID <https://redis.io/commands/xsetid>`_

        An internal command for replicating stream values
      - Not Implemented.

        
        
      
       

Cluster
-------

.. list-table::
    :header-rows: 1
    :class: command-table


    * - Redis Command
      - Compatibility

    * - `CLUSTER ADDSLOTS <https://redis.io/commands/cluster-addslots>`_

        Assign new hash slots to receiving node
      - :meth:`~coredis.StrictRedisCluster.cluster_addslots`

        
        
        
        


      
            

    * - `CLUSTER COUNTKEYSINSLOT <https://redis.io/commands/cluster-countkeysinslot>`_

        Return the number of local keys in the specified hash slot
      - :meth:`~coredis.StrictRedisCluster.cluster_countkeysinslot`

        
        
        
        


      
            

    * - `CLUSTER DELSLOTS <https://redis.io/commands/cluster-delslots>`_

        Set hash slots as unbound in receiving node
      - :meth:`~coredis.StrictRedisCluster.cluster_delslots`

        
        
        
        


      
            

    * - `CLUSTER FAILOVER <https://redis.io/commands/cluster-failover>`_

        Forces a replica to perform a manual failover of its master.
      - :meth:`~coredis.StrictRedisCluster.cluster_failover`

        
        
        
        


      
            

    * - `CLUSTER FORGET <https://redis.io/commands/cluster-forget>`_

        Remove a node from the nodes table
      - :meth:`~coredis.StrictRedisCluster.cluster_forget`

        
        
        
        


      
            

    * - `CLUSTER INFO <https://redis.io/commands/cluster-info>`_

        Provides info about Redis Cluster node state
      - :meth:`~coredis.StrictRedisCluster.cluster_info`

        
        
        
        


      
            

    * - `CLUSTER KEYSLOT <https://redis.io/commands/cluster-keyslot>`_

        Returns the hash slot of the specified key
      - :meth:`~coredis.StrictRedisCluster.cluster_keyslot`

        
        
        
        


      
            

    * - `CLUSTER MEET <https://redis.io/commands/cluster-meet>`_

        Force a node cluster to handshake with another node
      - :meth:`~coredis.StrictRedisCluster.cluster_meet`

        
        
        
        


      
            

    * - `CLUSTER NODES <https://redis.io/commands/cluster-nodes>`_

        Get Cluster config for the node
      - :meth:`~coredis.StrictRedisCluster.cluster_nodes`

        
        
        
        


      
            

    * - `CLUSTER REPLICATE <https://redis.io/commands/cluster-replicate>`_

        Reconfigure a node as a replica of the specified master node
      - :meth:`~coredis.StrictRedisCluster.cluster_replicate`

        
        
        
        


      
            

    * - `CLUSTER RESET <https://redis.io/commands/cluster-reset>`_

        Reset a Redis Cluster node
      - :meth:`~coredis.StrictRedisCluster.cluster_reset`

        
        
        
        


      
            

    * - `CLUSTER SET-CONFIG-EPOCH <https://redis.io/commands/cluster-set-config-epoch>`_

        Set the configuration epoch in a new node
      - :meth:`~coredis.StrictRedisCluster.cluster_set_config_epoch`

        
        
        
        


      
            

    * - `CLUSTER SETSLOT <https://redis.io/commands/cluster-setslot>`_

        Bind a hash slot to a specific node
      - :meth:`~coredis.StrictRedisCluster.cluster_setslot`

        
        
        
        


      
            

    * - `CLUSTER SLAVES <https://redis.io/commands/cluster-slaves>`_

        List replica nodes of the specified master node
      - :meth:`~coredis.StrictRedisCluster.cluster_slaves`

        
        - ☠️ Deprecated in redis: 5.0.0.
        - Use :meth:`~coredis.StrictRedisCluster.cluster replicas` 
        


      
            

    * - `CLUSTER SLOTS <https://redis.io/commands/cluster-slots>`_

        Get array of Cluster slot to node mappings
      - :meth:`~coredis.StrictRedisCluster.cluster_slots`

        
        
        
        


      
            

    * - `CLUSTER REPLICAS <https://redis.io/commands/cluster-replicas>`_

        List replica nodes of the specified master node
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.cluster.RedisClusterCommands.cluster_replicas`
        
        
      
                    

    * - `READONLY <https://redis.io/commands/readonly>`_

        Enables read queries for a connection to a cluster replica node
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.cluster.RedisClusterCommands.readonly`
        
        
      
                    

    * - `READWRITE <https://redis.io/commands/readwrite>`_

        Disables read queries for a connection to a cluster replica node
      - Not Implemented

        redis-py reference: :meth:`~redis.commands.cluster.RedisClusterCommands.readwrite`
        
        
      
                    

    * - `ASKING <https://redis.io/commands/asking>`_

        Sent by cluster clients after an -ASK redirect
      - Not Implemented.

        
        
      
       

    * - `CLUSTER BUMPEPOCH <https://redis.io/commands/cluster-bumpepoch>`_

        Advance the cluster config epoch
      - Not Implemented.

        
        
      
       

    * - `CLUSTER COUNT-FAILURE-REPORTS <https://redis.io/commands/cluster-count-failure-reports>`_

        Return the number of failure reports active for a given node
      - Not Implemented.

        
        
      
       

    * - `CLUSTER FLUSHSLOTS <https://redis.io/commands/cluster-flushslots>`_

        Delete a node's own slots information
      - Not Implemented.

        
        
      
       

    * - `CLUSTER GETKEYSINSLOT <https://redis.io/commands/cluster-getkeysinslot>`_

        Return local key names in the specified hash slot
      - Not Implemented.

        
        
      
       

    * - `CLUSTER MYID <https://redis.io/commands/cluster-myid>`_

        Return the node id
      - Not Implemented.

        
        
      
       

    * - `CLUSTER SAVECONFIG <https://redis.io/commands/cluster-saveconfig>`_

        Forces the node to save cluster state on disk
      - Not Implemented.

        
        
      
       


