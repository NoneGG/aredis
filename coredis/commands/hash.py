from coredis.exceptions import DataError
from coredis.utils import (
    b,
    dict_merge,
    iteritems,
    first_key,
    string_keys_to_dict,
    list_or_args,
    pairs_to_dict,
)


def parse_hscan(response, **options):
    cursor, r = response
    return int(cursor), r and pairs_to_dict(r) or {}


class HashCommandMixin:

    RESPONSE_CALLBACKS = dict_merge(
        string_keys_to_dict("HDEL HLEN", int),
        string_keys_to_dict("HEXISTS HMSET", bool),
        {
            "HGETALL": lambda r: r and pairs_to_dict(r) or {},
            "HINCRBYFLOAT": float,
            "HSCAN": parse_hscan,
        },
    )

    async def hdel(self, name, *keys):
        """Deletes ``keys`` from hash ``name``"""
        return await self.execute_command("HDEL", name, *keys)

    async def hexists(self, name, key):
        """
        Returns a boolean indicating if ``key`` exists within hash ``name``
        """
        return await self.execute_command("HEXISTS", name, key)

    async def hget(self, name, key):
        """Returns the value of ``key`` within the hash ``name``"""
        return await self.execute_command("HGET", name, key)

    async def hgetall(self, name):
        """Returns a Python dict of the hash's name/value pairs"""
        return await self.execute_command("HGETALL", name)

    async def hincrby(self, name, key, amount=1):
        """Increments the value of ``key`` in hash ``name`` by ``amount``"""
        return await self.execute_command("HINCRBY", name, key, amount)

    async def hincrbyfloat(self, name, key, amount=1.0):
        """
        Increments the value of ``key`` in hash ``name`` by floating
        ``amount``
        """
        return await self.execute_command("HINCRBYFLOAT", name, key, amount)

    async def hkeys(self, name):
        """Returns the list of keys within hash ``name``"""
        return await self.execute_command("HKEYS", name)

    async def hlen(self, name):
        """Returns the number of elements in hash ``name``"""
        return await self.execute_command("HLEN", name)

    async def hset(self, name, key, value):
        """
        Sets ``key`` to ``value`` within hash ``name``
        Returns 1 if HSET created a new field, otherwise 0
        """
        return await self.execute_command("HSET", name, key, value)

    async def hsetnx(self, name, key, value):
        """
        Sets ``key`` to ``value`` within hash ``name`` if ``key`` does not
        exist.  Returns 1 if HSETNX created a field, otherwise 0.
        """
        return await self.execute_command("HSETNX", name, key, value)

    async def hmset(self, name, mapping):
        """
        Sets key to value within hash ``name`` for each corresponding
        key and value from the ``mapping`` dict.
        """
        if not mapping:
            raise DataError("'hmset' with 'mapping' of length 0")
        items = []
        for pair in iteritems(mapping):
            items.extend(pair)
        return await self.execute_command("HMSET", name, *items)

    async def hmget(self, name, keys, *args):
        """Returns a list of values ordered identically to ``keys``"""
        args = list_or_args(keys, args)
        return await self.execute_command("HMGET", name, *args)

    async def hvals(self, name):
        """Returns the list of values within hash ``name``"""
        return await self.execute_command("HVALS", name)

    async def hscan(self, name, cursor=0, match=None, count=None):
        """
        Incrementallys return key/value slices in a hash. Also returns a
        cursor pointing to the scan position.

        ``match`` allows for filtering the keys by pattern

        ``count`` allows for hint the minimum number of returns
        """
        pieces = [name, cursor]
        if match is not None:
            pieces.extend([b("MATCH"), match])
        if count is not None:
            pieces.extend([b("COUNT"), count])
        return await self.execute_command("HSCAN", *pieces)

    async def hstrlen(self, name, key):
        """
        Returns the string length of the value associated
        with field in the hash stored at key.
        If the key or the field do not exist, 0 is returned.
        """
        return await self.execute_command("HSTRLEN", name, key)


class ClusterHashCommandMixin(HashCommandMixin):

    RESULT_CALLBACKS = {"HSCAN": first_key}
