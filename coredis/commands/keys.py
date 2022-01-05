import datetime
import time as mod_time
from coredis.exceptions import ResponseError, RedisError, DataError
from coredis.utils import (
    merge_result,
    NodeFlag,
    first_key,
    b,
    dict_merge,
    int_or_none,
    bool_ok,
    string_keys_to_dict,
    list_keys_to_dict,
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

    async def delete(self, *names):
        """Delete one or more keys specified by ``names``"""
        return await self.execute_command("DEL", *names)

    async def dump(self, name):
        """
        Return a serialized version of the value stored at the specified key.
        If key does not exist a nil bulk reply is returned.
        """
        return await self.execute_command("DUMP", name)

    async def exists(self, name):
        """Returns a boolean indicating whether key ``name`` exists"""
        return await self.execute_command("EXISTS", name)

    async def expire(self, name, time):
        """
        Set an expire flag on key ``name`` for ``time`` seconds. ``time``
        can be represented by an integer or a Python timedelta object.
        """
        if isinstance(time, datetime.timedelta):
            time = time.seconds + time.days * 24 * 3600
        return await self.execute_command("EXPIRE", name, time)

    async def expireat(self, name, when):
        """
        Set an expire flag on key ``name``. ``when`` can be represented
        as an integer indicating unix time or a Python datetime object.
        """
        if isinstance(when, datetime.datetime):
            when = int(mod_time.mktime(when.timetuple()))
        return await self.execute_command("EXPIREAT", name, when)

    async def keys(self, pattern="*"):
        """Returns a list of keys matching ``pattern``"""
        return await self.execute_command("KEYS", pattern)

    async def move(self, name, db):
        """Moves the key ``name`` to a different Redis database ``db``"""
        return await self.execute_command("MOVE", name, db)

    async def object(self, infotype, key):
        """Returns the encoding, idletime, or refcount about the key"""
        return await self.execute_command("OBJECT", infotype, key, infotype=infotype)

    async def persist(self, name):
        """Removes an expiration on ``name``"""
        return await self.execute_command("PERSIST", name)

    async def pexpire(self, name, time):
        """
        Set an expire flag on key ``name`` for ``time`` milliseconds.
        ``time`` can be represented by an integer or a Python timedelta
        object.
        """
        if isinstance(time, datetime.timedelta):
            ms = int(time.microseconds / 1000)
            time = (time.seconds + time.days * 24 * 3600) * 1000 + ms
        return await self.execute_command("PEXPIRE", name, time)

    async def pexpireat(self, name, when):
        """
        Set an expire flag on key ``name``. ``when`` can be represented
        as an integer representing unix time in milliseconds (unix time * 1000)
        or a Python datetime object.
        """
        if isinstance(when, datetime.datetime):
            ms = int(when.microsecond / 1000)
            when = int(mod_time.mktime(when.timetuple())) * 1000 + ms
        return await self.execute_command("PEXPIREAT", name, when)

    async def pttl(self, name):
        """
        Returns the number of milliseconds until the key ``name`` will expire
        """
        return await self.execute_command("PTTL", name)

    async def randomkey(self):
        """Returns the name of a random key"""
        return await self.execute_command("RANDOMKEY")

    async def rename(self, src, dst):
        """
        Renames key ``src`` to ``dst``
        """
        return await self.execute_command("RENAME", src, dst)

    async def renamenx(self, src, dst):
        """Renames key ``src`` to ``dst`` if ``dst`` doesn't already exist"""
        return await self.execute_command("RENAMENX", src, dst)

    async def restore(self, name, ttl, value, replace=False):
        """
        Creates a key using the provided serialized value, previously obtained
        using DUMP.
        """
        params = [name, ttl, value]
        if replace:
            params.append("REPLACE")
        return await self.execute_command("RESTORE", *params)

    async def sort(
        self,
        name,
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
        Sorts and returns a list, set or sorted set at ``name``.

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

        pieces = [name]
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

    async def ttl(self, name):
        """Returns the number of seconds until the key ``name`` will expire"""
        return await self.execute_command("TTL", name)

    async def type(self, name):
        """Returns the type of key ``name``"""
        return await self.execute_command("TYPE", name)

    async def unlink(self, *keys):
        """Removes the specified keys in a different thread, not blocking"""
        return await self.execute_command("UNLINK", *keys)

    async def wait(self, num_replicas, timeout):
        """
        Redis synchronous replication
        That returns the number of replicas that processed the query when
        we finally have at least ``num_replicas``, or when the ``timeout`` was
        reached.
        """
        return await self.execute_command("WAIT", num_replicas, timeout)

    async def scan(self, cursor=0, match=None, count=None):
        """
        Incrementally return lists of key names. Also return a cursor
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

    async def delete(self, *names):
        """
        "Delete one or more keys specified by ``names``"

        Cluster impl:
            Iterate all keys and send DELETE for each key.
            This will go a lot slower than a normal delete call in StrictRedis.

            Operation is no longer atomic.
        """
        count = 0

        for arg in names:
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
