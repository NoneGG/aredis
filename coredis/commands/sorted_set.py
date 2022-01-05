import re
from coredis.exceptions import RedisError
from coredis.utils import (
    b,
    iteritems,
    first_key,
    iterkeys,
    itervalues,
    dict_merge,
    string_keys_to_dict,
    int_or_none,
)

VALID_ZADD_OPTIONS = {"NX", "XX", "CH", "INCR"}


def float_or_none(response):
    if response is None:
        return None
    return float(response)


def zset_score_pairs(response, **options):
    """
    If ``withscores`` is specified in the options, return the response as
    a list of (value, score) pairs
    """
    if not response or not options["withscores"]:
        return response
    score_cast_func = options.get("score_cast_func", float)
    it = iter(response)
    return list(zip(it, map(score_cast_func, it)))


def parse_zscan(response, **options):
    score_cast_func = options.get("score_cast_func", float)
    cursor, r = response
    it = iter(r)
    return int(cursor), list(zip(it, map(score_cast_func, it)))


class SortedSetCommandMixin:

    RESPONSE_CALLBACKS = dict_merge(
        string_keys_to_dict(
            "ZADD ZCARD ZLEXCOUNT "
            "ZREM ZREMRANGEBYLEX "
            "ZREMRANGEBYRANK "
            "ZREMRANGEBYSCORE",
            int,
        ),
        string_keys_to_dict("ZSCORE ZINCRBY", float_or_none),
        string_keys_to_dict(
            "ZRANGE ZRANGEBYSCORE ZREVRANGE ZREVRANGEBYSCORE", zset_score_pairs
        ),
        string_keys_to_dict("ZRANK ZREVRANK", int_or_none),
        {"ZSCAN": parse_zscan,},
    )

    async def zadd(self, name, *args, **kwargs):
        """
        Set any number of score, element-name pairs to the key ``name``. Pairs
        can be specified in two ways:

        As *args, in the form of: score1, name1, score2, name2, ...
        or as **kwargs, in the form of: name1=score1, name2=score2, ...

        The following example would add four values to the 'my-key' key:
        redis.zadd('my-key', 1.1, 'name1', 2.2, 'name2', name3=3.3, name4=4.4)
        """
        pieces = []
        if args:
            if len(args) % 2 != 0:
                raise RedisError(
                    "ZADD requires an equal number of " "values and scores"
                )
            pieces.extend(args)
        for pair in iteritems(kwargs):
            pieces.append(pair[1])
            pieces.append(pair[0])
        return await self.execute_command("ZADD", name, *pieces)

    async def zaddoption(self, name, option=None, *args, **kwargs):
        """
        Differs from zadd in that you can set either 'XX' or 'NX' option as
        described here: https://redis.io/commands/zadd. Only for Redis 3.0.2 or
        later.

        The following example would add four values to the 'my-key' key:
        redis.zaddoption('my-key', 'XX', 1.1, 'name1', 2.2, 'name2', name3=3.3, name4=4.4)
        redis.zaddoption('my-key', 'NX CH', name1=2.2)
        """
        if not option:
            raise RedisError("ZADDOPTION must take options")
        options = set(opt.upper() for opt in option.split())
        if options - VALID_ZADD_OPTIONS:
            raise RedisError("ZADD only takes XX, NX, CH, or INCR")
        if "NX" in options and "XX" in options:
            raise RedisError("ZADD only takes one of XX or NX")
        pieces = list(options)
        members = []
        if args:
            if len(args) % 2 != 0:
                raise RedisError(
                    "ZADD requires an equal number of " "values and scores"
                )
            members.extend(args)
        for pair in iteritems(kwargs):
            members.append(pair[1])
            members.append(pair[0])
        if "INCR" in options and len(members) != 2:
            raise RedisError("ZADD with INCR only takes one score-name pair")
        return await self.execute_command("ZADD", name, *pieces, *members)

    async def zcard(self, name):
        """Returns the number of elements in the sorted set ``name``"""
        return await self.execute_command("ZCARD", name)

    async def zcount(self, name, min, max):
        """
        Returns the number of elements in the sorted set at key ``name`` with
        a score between ``min`` and ``max``.
        """
        return await self.execute_command("ZCOUNT", name, min, max)

    async def zincrby(self, name, value, amount=1):
        """
        Increments the score of ``value`` in sorted set ``name`` by ``amount``
        """
        return await self.execute_command("ZINCRBY", name, amount, value)

    async def zinterstore(self, dest, keys, aggregate=None):
        """
        Intersects multiple sorted sets specified by ``keys`` into
        a new sorted set, ``dest``. Scores in the destination will be
        aggregated based on the ``aggregate``, or SUM if none is provided.
        """
        return await self._zaggregate("ZINTERSTORE", dest, keys, aggregate)

    async def zlexcount(self, name, min, max):
        """
        Returns the number of items in the sorted set ``name`` between the
        lexicographical range ``min`` and ``max``.
        """
        return await self.execute_command("ZLEXCOUNT", name, min, max)

    async def zrange(
        self, name, start, end, desc=False, withscores=False, score_cast_func=float
    ):
        """
        Returns a range of values from sorted set ``name`` between
        ``start`` and ``end`` sorted in ascending order.

        ``start`` and ``end`` can be negative, indicating the end of the range.

        ``desc`` a boolean indicating whether to sort the results descendingly

        ``withscores`` indicates to return the scores along with the values.
        The return type is a list of (value, score) pairs

        ``score_cast_func`` a callable used to cast the score return value
        """
        if desc:
            return await self.zrevrange(name, start, end, withscores, score_cast_func)
        pieces = ["ZRANGE", name, start, end]
        if withscores:
            pieces.append(b("WITHSCORES"))
        options = {"withscores": withscores, "score_cast_func": score_cast_func}
        return await self.execute_command(*pieces, **options)

    async def zrangebylex(self, name, min, max, start=None, num=None):
        """
        Returns the lexicographical range of values from sorted set ``name``
        between ``min`` and ``max``.

        If ``start`` and ``num`` are specified, then return a slice of the
        range.
        """
        if (start is not None and num is None) or (num is not None and start is None):
            raise RedisError("``start`` and ``num`` must both be specified")
        pieces = ["ZRANGEBYLEX", name, min, max]
        if start is not None and num is not None:
            pieces.extend([b("LIMIT"), start, num])
        return await self.execute_command(*pieces)

    async def zrevrangebylex(self, name, max, min, start=None, num=None):
        """
        Returns the reversed lexicographical range of values from sorted set
        ``name`` between ``max`` and ``min``.

        If ``start`` and ``num`` are specified, then return a slice of the
        range.
        """
        if (start is not None and num is None) or (num is not None and start is None):
            raise RedisError("``start`` and ``num`` must both be specified")
        pieces = ["ZREVRANGEBYLEX", name, max, min]
        if start is not None and num is not None:
            pieces.extend([b("LIMIT"), start, num])
        return await self.execute_command(*pieces)

    async def zrangebyscore(
        self,
        name,
        min,
        max,
        start=None,
        num=None,
        withscores=False,
        score_cast_func=float,
    ):
        """
        Returns a range of values from the sorted set ``name`` with scores
        between ``min`` and ``max``.

        If ``start`` and ``num`` are specified, then return a slice
        of the range.

        ``withscores`` indicates to return the scores along with the values.
        The return type is a list of (value, score) pairs

        `score_cast_func`` a callable used to cast the score return value
        """
        if (start is not None and num is None) or (num is not None and start is None):
            raise RedisError("``start`` and ``num`` must both be specified")
        pieces = ["ZRANGEBYSCORE", name, min, max]
        if start is not None and num is not None:
            pieces.extend([b("LIMIT"), start, num])
        if withscores:
            pieces.append(b("WITHSCORES"))
        options = {"withscores": withscores, "score_cast_func": score_cast_func}
        return await self.execute_command(*pieces, **options)

    async def zrank(self, name, value):
        """
        Returns a 0-based value indicating the rank of ``value`` in sorted set
        ``name``
        """
        return await self.execute_command("ZRANK", name, value)

    async def zrem(self, name, *values):
        """Removes member ``values`` from sorted set ``name``"""
        return await self.execute_command("ZREM", name, *values)

    async def zremrangebylex(self, name, min, max):
        """
        Removes all elements in the sorted set ``name`` between the
        lexicographical range specified by ``min`` and ``max``.

        Returns the number of elements removed.
        """
        return await self.execute_command("ZREMRANGEBYLEX", name, min, max)

    async def zremrangebyrank(self, name, min, max):
        """
        Removes all elements in the sorted set ``name`` with ranks between
        ``min`` and ``max``. Values are 0-based, ordered from smallest score
        to largest. Values can be negative indicating the highest scores.
        Returns the number of elements removed
        """
        return await self.execute_command("ZREMRANGEBYRANK", name, min, max)

    async def zremrangebyscore(self, name, min, max):
        """
        Removes all elements in the sorted set ``name`` with scores
        between ``min`` and ``max``. Returns the number of elements removed.
        """
        return await self.execute_command("ZREMRANGEBYSCORE", name, min, max)

    async def zrevrange(
        self, name, start, end, withscores=False, score_cast_func=float
    ):
        """
        Returns a range of values from sorted set ``name`` between
        ``start`` and ``end`` sorted in descending order.

        ``start`` and ``end`` can be negative, indicating the end of the range.

        ``withscores`` indicates to return the scores along with the values
        The return type is a list of (value, score) pairs

        ``score_cast_func`` a callable used to cast the score return value
        """
        pieces = ["ZREVRANGE", name, start, end]
        if withscores:
            pieces.append(b("WITHSCORES"))
        options = {"withscores": withscores, "score_cast_func": score_cast_func}
        return await self.execute_command(*pieces, **options)

    async def zrevrangebyscore(
        self,
        name,
        max,
        min,
        start=None,
        num=None,
        withscores=False,
        score_cast_func=float,
    ):
        """
        Returns a range of values from the sorted set ``name`` with scores
        between ``min`` and ``max`` in descending order.

        If ``start`` and ``num`` are specified, then return a slice
        of the range.

        ``withscores`` indicates to return the scores along with the values.
        The return type is a list of (value, score) pairs

        ``score_cast_func`` a callable used to cast the score return value
        """
        if (start is not None and num is None) or (num is not None and start is None):
            raise RedisError("``start`` and ``num`` must both be specified")
        pieces = ["ZREVRANGEBYSCORE", name, max, min]
        if start is not None and num is not None:
            pieces.extend([b("LIMIT"), start, num])
        if withscores:
            pieces.append(b("WITHSCORES"))
        options = {"withscores": withscores, "score_cast_func": score_cast_func}
        return await self.execute_command(*pieces, **options)

    async def zrevrank(self, name, value):
        """
        Returns a 0-based value indicating the descending rank of
        ``value`` in sorted set ``name``
        """
        return await self.execute_command("ZREVRANK", name, value)

    async def zscore(self, name, value):
        "Return the score of element ``value`` in sorted set ``name``"
        return await self.execute_command("ZSCORE", name, value)

    async def zunionstore(self, dest, keys, aggregate=None):
        """
        Performs Union on multiple sorted sets specified by ``keys`` into
        a new sorted set, ``dest``. Scores in the destination will be
        aggregated based on the ``aggregate``, or SUM if none is provided.
        """
        return await self._zaggregate("ZUNIONSTORE", dest, keys, aggregate)

    async def _zaggregate(self, command, dest, keys, aggregate=None):
        pieces = [command, dest, len(keys)]
        if isinstance(keys, dict):
            keys, weights = iterkeys(keys), itervalues(keys)
        else:
            weights = None
        pieces.extend(keys)
        if weights:
            pieces.append(b("WEIGHTS"))
            pieces.extend(weights)
        if aggregate:
            pieces.append(b("AGGREGATE"))
            pieces.append(aggregate)
        return await self.execute_command(*pieces)

    async def zscan(
        self, name, cursor=0, match=None, count=None, score_cast_func=float
    ):
        """
        Incrementally returns lists of elements in a sorted set. Also returns
        a cursor pointing to the scan position.

        ``match`` allows for filtering the keys by pattern

        ``count`` allows for hint the minimum number of returns

        ``score_cast_func`` a callable used to cast the score return value
        """
        pieces = [name, cursor]
        if match is not None:
            pieces.extend([b("MATCH"), match])
        if count is not None:
            pieces.extend([b("COUNT"), count])
        options = {"score_cast_func": score_cast_func}
        return await self.execute_command("ZSCAN", *pieces, **options)


class ClusterSortedSetCommandMixin(SortedSetCommandMixin):

    RESULT_CALLBACKS = {"ZSCAN": first_key}
