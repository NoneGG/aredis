from coredis.utils import b, dict_merge, list_or_args, first_key, string_keys_to_dict


def parse_sscan(response, **options):
    cursor, r = response
    return int(cursor), r


class SetsCommandMixin:

    RESPONSE_CALLBACKS = dict_merge(
        string_keys_to_dict(
            "SADD SCARD SDIFFSTORE " "SETRANGE SINTERSTORE " "SREM SUNIONSTORE", int
        ),
        string_keys_to_dict("SISMEMBER SMOVE", bool),
        string_keys_to_dict(
            "SDIFF SINTER SMEMBERS SUNION", lambda r: r and set(r) or set()
        ),
        {"SSCAN": parse_sscan,},
    )

    async def sadd(self, name, *values):
        """Adds ``value(s)`` to set ``name``"""
        return await self.execute_command("SADD", name, *values)

    async def scard(self, name):
        """Returns the number of elements in set ``name``"""
        return await self.execute_command("SCARD", name)

    async def sdiff(self, keys, *args):
        """Returns the difference of sets specified by ``keys``"""
        args = list_or_args(keys, args)
        return await self.execute_command("SDIFF", *args)

    async def sdiffstore(self, dest, keys, *args):
        """
        Stores the difference of sets specified by ``keys`` into a new
        set named ``dest``.  Returns the number of keys in the new set.
        """
        args = list_or_args(keys, args)
        return await self.execute_command("SDIFFSTORE", dest, *args)

    async def sinter(self, keys, *args):
        """Returns the intersection of sets specified by ``keys``"""
        args = list_or_args(keys, args)
        return await self.execute_command("SINTER", *args)

    async def sinterstore(self, dest, keys, *args):
        """
        Stores the intersection of sets specified by ``keys`` into a new
        set named ``dest``.  Returns the number of keys in the new set.
        """
        args = list_or_args(keys, args)
        return await self.execute_command("SINTERSTORE", dest, *args)

    async def sismember(self, name, value):
        """
        Returns a boolean indicating if ``value`` is a member of set ``name``
        """
        return await self.execute_command("SISMEMBER", name, value)

    async def smembers(self, name):
        """Returns all members of the set ``name``"""
        return await self.execute_command("SMEMBERS", name)

    async def smove(self, src, dst, value):
        """Moves ``value`` from set ``src`` to set ``dst`` atomically"""
        return await self.execute_command("SMOVE", src, dst, value)

    async def spop(self, name, count=None):
        """
        Removes and returns a random member of set ``name``
        ``count`` should be type of int and default set to 1.
        If ``count`` is supplied, pops a list of ``count`` random
        members of set ``name``
        """
        if count and isinstance(count, int):
            return await self.execute_command("SPOP", name, count)
        else:
            return await self.execute_command("SPOP", name)

    async def srandmember(self, name, number=None):
        """
        If ``number`` is None, returns a random member of set ``name``.

        If ``number`` is supplied, returns a list of ``number`` random
        memebers of set ``name``. Note this is only available when running
        Redis 2.6+.
        """
        args = number and [number] or []
        return await self.execute_command("SRANDMEMBER", name, *args)

    async def srem(self, name, *values):
        """Removes ``values`` from set ``name``"""
        return await self.execute_command("SREM", name, *values)

    async def sunion(self, keys, *args):
        """Returns the union of sets specified by ``keys``"""
        args = list_or_args(keys, args)
        return await self.execute_command("SUNION", *args)

    async def sunionstore(self, dest, keys, *args):
        """
        Stores the union of sets specified by ``keys`` into a new
        set named ``dest``.  Returns the number of keys in the new set.
        """
        args = list_or_args(keys, args)
        return await self.execute_command("SUNIONSTORE", dest, *args)

    async def sscan(self, name, cursor=0, match=None, count=None):
        """
        Incrementally returns lists of elements in a set. Also returns a
        cursor pointing to the scan position.

        ``match`` is for filtering the keys by pattern

        ``count`` is for hint the minimum number of returns
        """
        pieces = [name, cursor]
        if match is not None:
            pieces.extend([b("MATCH"), match])
        if count is not None:
            pieces.extend([b("COUNT"), count])
        return await self.execute_command("SSCAN", *pieces)


class ClusterSetsCommandMixin(SetsCommandMixin):

    RESULT_CALLBACKS = {"SSCAN": first_key}

    ###
    # Set commands

    async def sdiff(self, keys, *args):
        """
        Returns the difference of sets specified by ``keys``

        Cluster impl:
            Querry all keys and diff all sets and return result
        """
        k = list_or_args(keys, args)
        res = await self.smembers(k[0])

        for arg in k[1:]:
            res -= await self.smembers(arg)

        return res

    async def sdiffstore(self, dest, keys, *args):
        """
        Stores the difference of sets specified by ``keys`` into a new
        set named ``dest``.  Returns the number of keys in the new set.
        Overwrites dest key if it exists.

        Cluster impl:
            Use sdiff() --> Delete dest key --> store result in dest key
        """
        res = await self.sdiff(keys, *args)
        await self.delete(dest)

        if not res:
            return 0
        return await self.sadd(dest, *res)

    async def sinter(self, keys, *args):
        """
        Returns the intersection of sets specified by ``keys``

        Cluster impl:
            Querry all keys, intersection and return result
        """
        k = list_or_args(keys, args)
        res = await self.smembers(k[0])

        for arg in k[1:]:
            res &= await self.smembers(arg)

        return res

    async def sinterstore(self, dest, keys, *args):
        """
        Stores the intersection of sets specified by ``keys`` into a new
        set named ``dest``.  Returns the number of keys in the new set.

        Cluster impl:
            Use sinter() --> Delete dest key --> store result in dest key
        """
        res = await self.sinter(keys, *args)
        await self.delete(dest)

        if res:
            await self.sadd(dest, *res)
            return len(res)
        else:
            return 0

    async def smove(self, src, dst, value):
        """
        Moves ``value`` from set ``src`` to set ``dst`` atomically

        Cluster impl:
            SMEMBERS --> SREM --> SADD. Function is no longer atomic.
        """
        res = await self.srem(src, value)

        # Only add the element if existed in src set
        if res == 1:
            await self.sadd(dst, value)

        return res

    async def sunion(self, keys, *args):
        """
        Returns the union of sets specified by ``keys``

        Cluster impl:
            Querry all keys, union and return result

            Operation is no longer atomic.
        """
        k = list_or_args(keys, args)
        res = await self.smembers(k[0])

        for arg in k[1:]:
            res |= await self.smembers(arg)

        return res

    async def sunionstore(self, dest, keys, *args):
        """
        Stores the union of sets specified by ``keys`` into a new
        set named ``dest``.  Returns the number of keys in the new set.

        Cluster impl:
            Use sunion() --> Dlete dest key --> store result in dest key

            Operation is no longer atomic.
        """
        res = await self.sunion(keys, *args)
        await self.delete(dest)

        return await self.sadd(dest, *res)
