from coredis.utils import b, dict_merge, bool_ok, nativestr, string_keys_to_dict
from coredis.exceptions import DataError, RedisClusterException, RedisError


class ListsCommandMixin:

    RESPONSE_CALLBACKS = dict_merge(
        string_keys_to_dict("BLPOP BRPOP", lambda r: r and tuple(r) or None),
        string_keys_to_dict(
            # these return OK, or int if redis-server is >=1.3.4
            "LPUSH RPUSH",
            lambda r: isinstance(r, int) and r or nativestr(r) == "OK",
        ),
        string_keys_to_dict("LSET LTRIM", bool_ok),
        string_keys_to_dict("LINSERT LLEN LPUSHX RPUSHX", int),
    )

    async def blpop(self, keys, timeout=0):
        """
        LPOP a value off of the first non-empty list
        named in the ``keys`` list.

        If none of the lists in ``keys`` has a value to LPOP, then block
        for ``timeout`` seconds, or until a value gets pushed on to one
        of the lists.

        If timeout is 0, then block indefinitely.
        """
        if timeout is None:
            timeout = 0
        if isinstance(keys, str):
            keys = [keys]
        else:
            keys = list(keys)
        keys.append(timeout)
        return await self.execute_command("BLPOP", *keys)

    async def brpop(self, keys, timeout=0):
        """
        RPOP a value off of the first non-empty list
        named in the ``keys`` list.

        If none of the lists in ``keys`` has a value to LPOP, then block
        for ``timeout`` seconds, or until a value gets pushed on to one
        of the lists.

        If timeout is 0, then block indefinitely.
        """
        if timeout is None:
            timeout = 0
        if isinstance(keys, str):
            keys = [keys]
        else:
            keys = list(keys)
        keys.append(timeout)
        return await self.execute_command("BRPOP", *keys)

    async def brpoplpush(self, src, dst, timeout=0):
        """
        Pop a value off the tail of ``src``, push it on the head of ``dst``
        and then return it.

        This command blocks until a value is in ``src`` or until ``timeout``
        seconds elapse, whichever is first. A ``timeout`` value of 0 blocks
        forever.
        """
        if timeout is None:
            timeout = 0
        return await self.execute_command("BRPOPLPUSH", src, dst, timeout)

    async def lindex(self, name, index):
        """
        Return the item from list ``name`` at position ``index``

        Negative indexes are supported and will return an item at the
        end of the list
        """
        return await self.execute_command("LINDEX", name, index)

    async def linsert(self, name, where, refvalue, value):
        """
        Insert ``value`` in list ``name`` either immediately before or after
        [``where``] ``refvalue``

        Returns the new length of the list on success or -1 if ``refvalue``
        is not in the list.
        """
        return await self.execute_command("LINSERT", name, where, refvalue, value)

    async def llen(self, name):
        """Returns the length of the list ``name``"""
        return await self.execute_command("LLEN", name)

    async def lpop(self, name):
        """RemoveS and returns the first item of the list ``name``"""
        return await self.execute_command("LPOP", name)

    async def lpush(self, name, *values):
        """Pushes ``values`` onto the head of the list ``name``"""
        return await self.execute_command("LPUSH", name, *values)

    async def lpushx(self, name, value):
        """
        Pushes ``value`` onto the head of the list ``name`` if ``name`` exists
        """
        return await self.execute_command("LPUSHX", name, value)

    async def lrange(self, name, start, end):
        """
        Returns a slice of the list ``name`` between
        position ``start`` and ``end``

        ``start`` and ``end`` can be negative numbers just like
        Python slicing notation
        """
        return await self.execute_command("LRANGE", name, start, end)

    async def lrem(self, name, count, value):
        """
        Removes the first ``count`` occurrences of elements equal to ``value``
        from the list stored at ``name``.

        The count argument influences the operation in the following ways:
            count > 0: Remove elements equal to value moving from head to tail.
            count < 0: Remove elements equal to value moving from tail to head.
            count = 0: Remove all elements equal to value.
        """
        return await self.execute_command("LREM", name, count, value)

    async def lset(self, name, index, value):
        """Sets ``position`` of list ``name`` to ``value``"""
        return await self.execute_command("LSET", name, index, value)

    async def ltrim(self, name, start, end):
        """
        Trims the list ``name``, removing all values not within the slice
        between ``start`` and ``end``

        ``start`` and ``end`` can be negative numbers just like
        Python slicing notation
        """
        return await self.execute_command("LTRIM", name, start, end)

    async def rpop(self, name):
        """Removes and return the last item of the list ``name``"""
        return await self.execute_command("RPOP", name)

    async def rpoplpush(self, src, dst):
        """
        RPOP a value off of the ``src`` list and atomically LPUSH it
        on to the ``dst`` list.  Returns the value.
        """
        return await self.execute_command("RPOPLPUSH", src, dst)

    async def rpush(self, name, *values):
        """Pushes ``values`` onto the tail of the list ``name``"""
        return await self.execute_command("RPUSH", name, *values)

    async def rpushx(self, name, value):
        """
        Pushes ``value`` onto the tail of the list ``name`` if ``name`` exists
        """
        return await self.execute_command("RPUSHX", name, value)


class ClusterListsCommandMixin(ListsCommandMixin):
    async def brpoplpush(self, src, dst, timeout=0):
        """
        Pops a value off the tail of ``src``, push it on the head of ``dst``
        and then return it.

        This command blocks until a value is in ``src`` or until ``timeout``
        seconds elapse, whichever is first. A ``timeout`` value of 0 blocks
        forever.

        Cluster impl:
            Call brpop() then send the result into lpush()

            Operation is no longer atomic.
        """
        try:
            value = await self.brpop(src, timeout=timeout)
            if value is None:
                return None
        except TimeoutError:
            # Timeout was reached
            return None

        await self.lpush(dst, value[1])
        return value[1]

    async def rpoplpush(self, src, dst):
        """
        RPOP a value off of the ``src`` list and atomically LPUSH it
        on to the ``dst`` list.  Returns the value.

        Cluster impl:
            Call rpop() then send the result into lpush()

            Operation is no longer atomic.
        """
        value = await self.rpop(src)

        if value:
            await self.lpush(dst, value)
            return value

        return None

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
        groups=None,
    ):
        """Sorts and returns a list, set or sorted set at ``name``.

        :start: and :num:
            are for paging through the sorted data

        :by:
            allows using an external key to weight and sort the items.
            Use an "*" to indicate where in the key the item value is located

        :get:
            is for returning items from external keys rather than the
            sorted data itself.  Use an "*" to indicate where int he key
            the item value is located

        :desc:
            is for reversing the sort

        :alpha:
            is for sorting lexicographically rather than numerically

        :store:
            is for storing the result of the sort into the key `store`

        ClusterImpl:
            A full implementation of the server side sort mechanics because many of the
            options work on multiple keys that can exist on multiple servers.
        """
        if (start is None and num is not None) or (start is not None and num is None):
            raise RedisError("RedisError: ``start`` and ``num`` must both be specified")
        try:
            data_type = b(await self.type(name))

            if data_type == b("none"):
                return []
            elif data_type == b("set"):
                data = list(await self.smembers(name))[:]
            elif data_type == b("list"):
                data = await self.lrange(name, 0, -1)
            else:
                raise RedisClusterException(
                    "Unable to sort data type : {0}".format(data_type)
                )
            if by is not None:
                # _sort_using_by_arg mutates data so we don't
                # need need a return value.
                data = await self._sort_using_by_arg(data, by, alpha)
            elif not alpha:
                data.sort(key=self._strtod_key_func)
            else:
                data.sort()
            if desc:
                data = data[::-1]
            if not (start is None and num is None):
                data = data[start : start + num]

            if get:
                data = await self._retrive_data_from_sort(data, get)

            if store is not None:
                if data_type == b("set"):
                    await self.delete(store)
                    await self.rpush(store, *data)
                elif data_type == b("list"):
                    await self.delete(store)
                    await self.rpush(store, *data)
                else:
                    raise RedisClusterException(
                        "Unable to store sorted data for data type : {0}".format(
                            data_type
                        )
                    )

                return len(data)

            if groups:
                if not get or isinstance(get, str) or len(get) < 2:
                    raise DataError(
                        'when using "groups" the "get" argument '
                        "must be specified and contain at least "
                        "two keys"
                    )
                n = len(get)
                return list(zip(*[data[i::n] for i in range(n)]))
            else:
                return data
        except KeyError:
            return []

    async def _retrive_data_from_sort(self, data, get):
        """
        Used by sort()
        """
        if get is not None:
            if isinstance(get, str):
                get = [get]
            new_data = []
            for k in data:
                for g in get:
                    single_item = await self._get_single_item(k, g)
                    new_data.append(single_item)
            data = new_data
        return data

    async def _get_single_item(self, k, g):
        """
        Used by sort()
        """
        if getattr(k, "decode", None):
            k = k.decode("utf-8")

        if "*" in g:
            g = g.replace("*", k)
            if "->" in g:
                key, hash_key = g.split("->")
                single_item = await self.get(key, {}).get(hash_key)
            else:
                single_item = await self.get(g)
        elif "#" in g:
            single_item = k
        else:
            single_item = None
        return b(single_item)

    def _strtod_key_func(self, arg):
        """
        Used by sort()
        """
        return float(arg)

    async def _sort_using_by_arg(self, data, by, alpha):
        """
        Used by sort()
        """
        if getattr(by, "decode", None):
            by = by.decode("utf-8")

        async def _by_key(arg):
            if getattr(arg, "decode", None):
                arg = arg.decode("utf-8")

            key = by.replace("*", arg)
            if "->" in by:
                key, hash_key = key.split("->")
                v = await self.hget(key, hash_key)
                if alpha:
                    return v
                else:
                    return float(v)
            else:
                return await self.get(key)

        sorted_data = []
        for d in data:
            sorted_data.append((d, await _by_key(d)))
        return [x[0] for x in sorted(sorted_data, key=lambda x: x[1])]
