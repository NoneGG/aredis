from coredis.exceptions import DataError
from coredis.utils import (
    b,
    dict_merge,
    first_key,
    iteritems,
    list_or_args,
    pairs_to_dict,
    string_keys_to_dict,
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

    async def hdel(self, key, *fields):
        """Deletes ``fields`` from hash ``key``"""

        return await self.execute_command("HDEL", key, *fields)

    async def hexists(self, key, field):
        """
        Returns a boolean indicating if ``field`` exists within hash ``key``
        """

        return await self.execute_command("HEXISTS", key, field)

    async def hget(self, key, field):
        """Returns the value of ``field`` within the hash ``key``"""

        return await self.execute_command("HGET", key, field)

    async def hgetall(self, key):
        """Returns a Python dict of the hash's name/value pairs"""

        return await self.execute_command("HGETALL", key)

    async def hincrby(self, key, field, amount=1):
        """Increments the value of ``field`` in hash ``key`` by ``amount``"""

        return await self.execute_command("HINCRBY", key, key, amount)

    async def hincrbyfloat(self, key, field, amount=1.0):
        """
        Increments the value of ``field`` in hash ``key`` by floating
        ``amount``
        """

        return await self.execute_command("HINCRBYFLOAT", key, field, amount)

    async def hkeys(self, key):
        """Returns the list of keys within hash ``key``"""

        return await self.execute_command("HKEYS", key)

    async def hlen(self, key):
        """Returns the number of elements in hash ``key``"""

        return await self.execute_command("HLEN", key)

    async def hset(self, key, field, value):
        """
        Sets ``field`` to ``value`` within hash ``key``
        Returns 1 if HSET created a new field, otherwise 0
        """

        return await self.execute_command("HSET", key, field, value)

    async def hsetnx(self, key, field, value):
        """
        Sets ``field`` to ``value`` within hash ``key`` if ``field`` does not
        exist.  Returns 1 if HSETNX created a field, otherwise 0.
        """

        return await self.execute_command("HSETNX", key, field, value)

    async def hmset(self, key, field_values):
        """
        Sets key to value within hash ``key`` for each corresponding
        key and value from the ``field_items`` dict.
        """

        if not field_values:
            raise DataError("'hmset' with 'field_values' of length 0")
        items = []

        for pair in iteritems(field_values):
            items.extend(pair)

        return await self.execute_command("HMSET", key, *items)

    async def hmget(self, key, fields, *args):
        """Returns a list of values ordered identically to ``fields``"""
        args = list_or_args(fields, args)

        return await self.execute_command("HMGET", key, *args)

    async def hvals(self, key):
        """Returns the list of values within hash ``key``"""

        return await self.execute_command("HVALS", key)

    async def hscan(self, key, cursor=0, match=None, count=None):
        """
        Incrementallys return key/value slices in a hash. Also returns a
        cursor pointing to the scan position.

        :param match: allows for filtering the keys by pattern
        :param count: allows for hint the minimum number of returns
        """
        pieces = [key, cursor]

        if match is not None:
            pieces.extend([b("MATCH"), match])

        if count is not None:
            pieces.extend([b("COUNT"), count])

        return await self.execute_command("HSCAN", *pieces)

    async def hstrlen(self, key, field):
        """
        Returns the string length of the value associated
        with field in the hash stored at key.
        If the key or the field do not exist, 0 is returned.
        """

        return await self.execute_command("HSTRLEN", key, field)

    async def hrandfield(self, key, count=None, withvalues=False):
        """
        Return a random field from the hash value stored at key.

        :param count: if the argument is positive, return an array of distinct fields.
         If called with a negative count, the behavior changes and the command
         is allowed to return the same field multiple times. In this case,
         the number of returned fields is the absolute value of the
         specified count.
        :param withvalues: The optional WITHVALUES modifier changes the reply so it
         includes the respective values of the randomly selected hash fields.

        .. versionadded:: 2.1.0
        """
        params = []

        if count is not None:
            params.append(count)

        if withvalues:
            params.append("WITHVALUES")

        return await self.execute_command("HRANDFIELD", key, *params)


class ClusterHashCommandMixin(HashCommandMixin):

    RESULT_CALLBACKS = {"HSCAN": first_key}
