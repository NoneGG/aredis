import datetime
import time as mod_time

from coredis.exceptions import DataError, RedisError, ResponseError
from coredis.utils import (
    NodeFlag,
    b,
    bool_ok,
    dict_merge,
    first_key,
    int_or_none,
    list_keys_to_dict,
    merge_result,
    string_keys_to_dict,
)


def sort_return_tuples(response, **options):
    """
    If ``groups`` is specified, return the response as a list of
    n-element tuples with n being the value found in options['groups']
    """

    if not response or not options["groups"]:
        return response
    n = options["groups"]

    return list(zip(*[response[i::n] for i in range(n)]))


def parse_object(response, infotype):
    """Parse the results of an OBJECT command"""

    if infotype in ("idletime", "refcount"):
        return int_or_none(response)

    return response


def parse_scan(response, **options):
    cursor, r = response

    return int(cursor), r


class KeysCommandMixin:

    RESPONSE_CALLBACKS = dict_merge(
        string_keys_to_dict("EXISTS EXPIRE EXPIREAT " "MOVE PERSIST RENAMENX", bool),
        {
            "DEL": int,
            "SORT": sort_return_tuples,
            "OBJECT": parse_object,
            "RANDOMKEY": lambda r: r and r or None,
            "SCAN": parse_scan,
            "RENAME": bool_ok,
        },
    )

    async def delete(self, *keys):
        """Delete one or more keys specified by ``keys``"""

        return await self.execute_command("DEL", *keys)

    async def dump(self, key):
        """
        Return a serialized version of the value stored at the specified key.
        If key does not exist a nil bulk reply is returned.
        """

        return await self.execute_command("DUMP", key)

    async def object_encoding(self, key):
        """
        Return the internal encoding for the object stored at ``key``

        .. versionadded:: 2.1.0
        """

        return await self.execute_command("OBJECT ENCODING", key)

    async def object_freq(self, key):
        """
        Return the logarithmic access frequency counter for the object
        stored at ``key``

        .. versionadded:: 2.1.0
        """

        return await self.execute_command("OBJECT FREQ", key)

    async def object_idletime(self, key):
        """
        Return the time in seconds since the last access to the object
        stored at ``key``

        .. versionadded:: 2.1.0
        """

        return await self.execute_command("OBJECT IDLETIME", key)

    async def object_refcount(self, key):
        """
        Return the reference count of the object stored at ``key``

        .. versionadded:: 2.1.0
        """

        return await self.execute_command("OBJECT REFCOUNT", key)

    async def exists(self, *keys):
        """Returns a count indicating the number of keys in ``keys`` that exist"""

        return await self.execute_command("EXISTS", *keys)

    async def expire(self, key, seconds):
        """
        Set an expire flag on key ``key`` for ``seconds`` seconds. ``seconds``
        can be represented by an integer or a Python timedelta object.
        """

        if isinstance(seconds, datetime.timedelta):
            seconds = seconds.seconds + seconds.days * 24 * 3600

        return await self.execute_command("EXPIRE", key, seconds)

    async def expireat(self, key, timestamp):
        """
        Set an expire flag on key ``key``. ``timestamp`` can be represented
        as an integer indicating unix time or a Python datetime object.
        """

        if isinstance(timestamp, datetime.datetime):
            timestamp = int(mod_time.mktime(timestamp.timetuple()))

        return await self.execute_command("EXPIREAT", key, timestamp)

    async def keys(self, pattern="*"):
        """Returns a list of keys matching ``pattern``"""

        return await self.execute_command("KEYS", pattern)

    async def move(self, key, db):
        """Moves the key ``key`` to a different Redis database ``db``"""

        return await self.execute_command("MOVE", key, db)

    async def object(self, infotype, key):
        """Returns the encoding, idletime, or refcount about the key"""

        return await self.execute_command("OBJECT", infotype, key, infotype=infotype)

    async def persist(self, key):
        """Removes an expiration on ``key``"""

        return await self.execute_command("PERSIST", key)

    async def pexpire(self, key, milliseconds):
        """
        Set an expire flag on key ``key`` for ``milliseconds`` milliseconds.
        ``milliseconds`` can be represented by an integer or a Python timedelta
        object.
        """

        if isinstance(milliseconds, datetime.timedelta):
            ms = int(milliseconds.microseconds / 1000)
            milliseconds = (
                milliseconds.seconds + milliseconds.days * 24 * 3600
            ) * 1000 + ms

        return await self.execute_command("PEXPIRE", key, milliseconds)

    async def pexpireat(self, key, timestamp):
        """
        Set an expire flag on key ``key``. ``timestamp`` can be represented
        as an integer representing unix time in milliseconds (unix time * 1000)
        or a Python datetime object.
        """

        if isinstance(timestamp, datetime.datetime):
            ms = int(timestamp.microsecond / 1000)
            timestamp = int(mod_time.mktime(timestamp.timetuple())) * 1000 + ms

        return await self.execute_command("PEXPIREAT", key, timestamp)

    async def pttl(self, key):
        """
        Returns the number of milliseconds until the key ``key`` will expire
        """

        return await self.execute_command("PTTL", key)

    async def randomkey(self):
        """Returns the name of a random key"""

        return await self.execute_command("RANDOMKEY")

    async def rename(self, key, newkey):
        """
        Rekeys key ``key`` to ``newkey``
        """

        return await self.execute_command("RENAME", key, newkey)

    async def renamenx(self, key, newkey):
        """Rekeys key ``key`` to ``newkey`` if ``newkey`` doesn't already exist"""

        return await self.execute_command("RENAMENX", key, newkey)

    async def restore(self, key, ttl, serialized_value, replace=False):
        """
        Creates a key using the provided serialized value, previously obtained
        using DUMP.
        """
        params = [key, ttl, serialized_value]

        if replace:
            params.append("REPLACE")

        return await self.execute_command("RESTORE", *params)

    async def sort(
        self,
        key,
        start=None,
        num=None,
        by=None,
        get=None,
        desc=False,
        alpha=False,
        store=None,
        groups=False,
    ):
        """
        Sorts and returns a list, set or sorted set at ``key``.

        ``start`` and ``num`` are for paginating sorted data

        ``by`` allows using an external key to weight and sort the items.
            Use an "*" to indicate where in the key the item value is located

        ``get`` is for returning items from external keys rather than the
            sorted data itself.  Use an "*" to indicate where int he key
            the item value is located

        ``desc`` is for reversing the sort

        ``alpha`` is for sorting lexicographically rather than numerically

        ``store`` is for storing the result of the sort into
            the key ``store``

        ``groups`` if set to True and if ``get`` contains at least two
            elements, sort will return a list of tuples, each containing the
            values fetched from the arguments to ``get``.

        """

        if (start is not None and num is None) or (num is not None and start is None):
            raise RedisError("``start`` and ``num`` must both be specified")

        pieces = [key]

        if by is not None:
            pieces.append(b("BY"))
            pieces.append(by)

        if start is not None and num is not None:
            pieces.append(b("LIMIT"))
            pieces.append(start)
            pieces.append(num)

        if get is not None:
            # If get is a string assume we want to get a single value.
            # Otherwise assume it's an interable and we want to get multiple
            # values. We can't just iterate blindly because strings are
            # iterable.

            if isinstance(get, str):
                pieces.append(b("GET"))
                pieces.append(get)
            else:
                for g in get:
                    pieces.append(b("GET"))
                    pieces.append(g)

        if desc:
            pieces.append(b("DESC"))

        if alpha:
            pieces.append(b("ALPHA"))

        if store is not None:
            pieces.append(b("STORE"))
            pieces.append(store)

        if groups:
            if not get or isinstance(get, str) or len(get) < 2:
                raise DataError(
                    'when using "groups" the "get" argument '
                    "must be specified and contain at least "
                    "two keys"
                )

        options = {"groups": len(get) if groups else None}

        return await self.execute_command("SORT", *pieces, **options)

    async def touch(self, keys):
        """
        Alters the last access time of a key(s).
        A key is ignored if it does not exist.
        """

        return await self.execute_command("TOUCH", *keys)

    async def ttl(self, key):
        """Returns the number of seconds until the key ``key`` will expire"""

        return await self.execute_command("TTL", key)

    async def type(self, key):
        """Returns the type of key ``key``"""

        return await self.execute_command("TYPE", key)

    async def unlink(self, *keys):
        """Removes the specified keys in a different thread, not blocking"""

        return await self.execute_command("UNLINK", *keys)

    async def wait(self, numreplicas, timeout):
        """
        Redis synchronous replication
        That returns the number of replicas that processed the query when
        we finally have at least ``numreplicas``, or when the ``timeout`` was
        reached.
        """

        return await self.execute_command("WAIT", numreplicas, timeout)

    async def scan(self, cursor=0, match=None, count=None):
        """
        Incrementally return lists of key keys. Also return a cursor
        indicating the scan position.

        ``match`` allows for filtering the keys by pattern

        ``count`` allows for hint the minimum number of returns
        """
        pieces = [cursor]

        if match is not None:
            pieces.extend([b("MATCH"), match])

        if count is not None:
            pieces.extend([b("COUNT"), count])

        return await self.execute_command("SCAN", *pieces)


class ClusterKeysCommandMixin(KeysCommandMixin):

    NODES_FLAGS = dict_merge(
        {
            "MOVE": NodeFlag.BLOCKED,
            "RANDOMKEY": NodeFlag.RANDOM,
            "SCAN": NodeFlag.ALL_MASTERS,
        },
        list_keys_to_dict(["KEYS"], NodeFlag.ALL_NODES),
    )

    RESULT_CALLBACKS = {
        "KEYS": merge_result,
        "RANDOMKEY": first_key,
        "SCAN": lambda res: res,
    }

    async def rename(self, src, dst):
        """
        Rename key ``src`` to ``dst``

        Cluster impl:
            This operation is no longer atomic because each key must be querried
            then set in separate calls because they maybe will change cluster node
        """

        if src == dst:
            raise ResponseError("source and destination objects are the same")

        data = await self.dump(src)

        if data is None:
            raise ResponseError("no such key")

        ttl = await self.pttl(src)

        if ttl is None or ttl < 1:
            ttl = 0

        await self.delete(dst)
        await self.restore(dst, ttl, data)
        await self.delete(src)

        return True

    async def delete(self, *keys):
        """
        "Delete one or more keys specified by ``keys``"

        Cluster impl:
            Iterate all keys and send DELETE for each key.
            This will go a lot slower than a normal delete call in StrictRedis.

            Operation is no longer atomic.
        """
        count = 0

        for arg in keys:
            count += await self.execute_command("DEL", arg)

        return count

    async def renamenx(self, src, dst):
        """
        Rename key ``src`` to ``dst`` if ``dst`` doesn't already exist

        Cluster impl:
            Check if dst key do not exists, then calls rename().

            Operation is no longer atomic.
        """

        if not await self.exists(dst):
            return await self.rename(src, dst)

        return False
