from coredis.exceptions import DataError, RedisClusterException, RedisError
from coredis.utils import b, bool_ok, dict_merge, nativestr, string_keys_to_dict


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

    async def brpoplpush(self, source, destination, timeout=0):
        """
        Pop a value off the tail of ``source``, push it on the head of ``destination``
        and then return it.

        This command blocks until a value is in ``source`` or until ``timeout``
        seconds elapse, whichever is first. A ``timeout`` value of 0 blocks
        forever.
        """

        if timeout is None:
            timeout = 0

        return await self.execute_command("BRPOPLPUSH", source, destination, timeout)

    async def lindex(self, key, index):
        """
        Return the item from list ``key`` at position ``index``

        Negative indexes are supported and will return an item at the
        end of the list
        """

        return await self.execute_command("LINDEX", key, index)

    async def linsert(self, key, where, pivot, element):
        """
        Insert ``element`` in list ``key`` either immediately before or after
        [``where``] ``pivot``

        Returns the new length of the list on success or -1 if ``pivot``
        is not in the list.
        """

        return await self.execute_command("LINSERT", key, where, pivot, element)

    async def llen(self, key):
        """Returns the length of the list ``key``"""

        return await self.execute_command("LLEN", key)

    async def lpop(self, key):
        """RemoveS and returns the first item of the list ``key``"""

        return await self.execute_command("LPOP", key)

    async def lpush(self, key, *elements):
        """Pushes ``elements`` onto the head of the list ``key``"""

        return await self.execute_command("LPUSH", key, *elements)

    async def lpushx(self, key, *elements):
        """
        Pushes ``elements`` onto the head of the list ``key`` if it exists
        """

        return await self.execute_command("LPUSHX", key, *elements)

    async def lrange(self, key, start, stop):
        """
        Returns a slice of the list ``key`` between
        position ``start`` and ``stop``

        ``start`` and ``stop`` can be negative numbers just like
        Python slicing notation
        """

        return await self.execute_command("LRANGE", key, start, stop)

    async def lrem(self, key, count, element):
        """
        Removes the first ``count`` occurrences of elements equal to ``element``
        from the list stored at ``key``.

        The count argument influences the operation in the following ways:
            count > 0: Remove elements equal to value moving from head to tail.
            count < 0: Remove elements equal to value moving from tail to head.
            count = 0: Remove all elements equal to value.
        """

        return await self.execute_command("LREM", key, count, element)

    async def lset(self, key, index, element):
        """Sets ``index`` of list ``key`` to ``element``"""

        return await self.execute_command("LSET", key, index, element)

    async def ltrim(self, key, start, stop):
        """
        Trims the list ``key``, removing all values not within the slice
        between ``start`` and ``stop``

        ``start`` and ``stop`` can be negative numbers just like
        Python slicing notation
        """

        return await self.execute_command("LTRIM", key, start, stop)

    async def rpop(self, key):
        """Removes and return the last item of the list ``key``"""

        return await self.execute_command("RPOP", key)

    async def rpoplpush(self, source, destination):
        """
        RPOP a value off of the ``source`` list and atomically LPUSH it
        on to the ``destination`` list.  Returns the value.
        """

        return await self.execute_command("RPOPLPUSH", source, destination)

    async def rpush(self, key, *elements):
        """Pushes ``elements`` onto the tail of the list ``key``"""

        return await self.execute_command("RPUSH", key, *elements)

    async def rpushx(self, key, *elements):
        """
        Pushes ``elements`` onto the tail of the list ``key`` if it exists
        """

        return await self.execute_command("RPUSHX", key, *elements)

    async def lmove(self, source, destination, wherefrom="LEFT", whereto="RIGHT"):
        """
        Atomically returns and removes the first/last element of a list,
        pushing it as the first/last element on the destination list.
        Returns the element being popped and pushed.

        .. versionadded:: 2.1.0
        """
        params = [source, destination, wherefrom, whereto]

        return await self.execute_command("LMOVE", *params)

    async def blmove(
        self, source, destination, timeout, wherefrom="LEFT", whereto="RIGHT"
    ):
        """
        Blocking version of lmove.

        .. versionadded:: 2.1.0
        """
        params = [source, destination, wherefrom, whereto, timeout]

        return await self.execute_command("BLMOVE", *params)

    async def lpos(self, key, element, rank=None, count=None, maxlen=None):
        """
        Get position of ``element`` within the list ``key``
         If specified, ``rank`` indicates the "rank" of the first element to
         return in case there are multiple copies of ``element`` in the list.
         By default, LPOS returns the position of the first occurrence of
         ``element`` in the list. When ``rank`` 2, LPOS returns the position of
         the second ``element`` in the list. If ``rank`` is negative, LPOS
         searches the list in reverse. For example, -1 would return the
         position of the last occurrence of ``element`` and -2 would return the
         position of the next to last occurrence of ``element``.
         If specified, ``count`` indicates that LPOS should return a list of
         up to ``count`` positions. A ``count`` of 2 would return a list of
         up to 2 positions. A ``count`` of 0 returns a list of all positions
         matching ``element``. When ``count`` is specified and but ``value``
         does not exist in the list, an empty list is returned.
         If specified, ``maxlen`` indicates the maximum number of list
         elements to scan. A ``maxlen`` of 1000 will only return the
         position(s) of items within the first 1000 entries in the list.
         A ``maxlen`` of 0 (the default) will scan the entire list.

        .. versionadded:: 2.1.0
        """
        pieces = [key, element]

        if rank is not None:
            pieces.extend(["RANK", rank])

        if count is not None:
            pieces.extend(["COUNT", count])

        if maxlen is not None:
            pieces.extend(["MAXLEN", maxlen])

        return await self.execute_command("LPOS", *pieces)


class ClusterListsCommandMixin(ListsCommandMixin):
    async def brpoplpush(self, source, destination, timeout=0):
        """
        Pops a value off the tail of ``source``, push it on the head of ``destination``
        and then return it.

        This command blocks until a value is in ``source`` or until ``timeout``
        seconds elapse, whichever is first. A ``timeout`` value of 0 blocks
        forever.

        Cluster impl:
            Call brpop() then send the result into lpush()

            Operation is no longer atomic.
        """
        try:
            value = await self.brpop(source, timeout=timeout)

            if value is None:
                return None
        except TimeoutError:
            # Timeout was reached

            return None

        await self.lpush(destination, value[1])

        return value[1]

    async def rpoplpush(self, source, destination):
        """
        RPOP a value off of the ``source`` list and atomically LPUSH it
        on to the ``destination`` list.  Returns the value.

        Cluster impl:
            Call rpop() then send the result into lpush()

            Operation is no longer atomic.
        """
        value = await self.rpop(source)

        if value:
            await self.lpush(destination, value)

            return value

        return None

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
        groups=None,
    ):
        """Sorts and returns a list, set or sorted set at ``key``.

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
            data_type = b(await self.type(key))

            if data_type == b("none"):
                return []
            elif data_type == b("set"):
                data = list(await self.smembers(key))[:]
            elif data_type == b("list"):
                data = await self.lrange(key, 0, -1)
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
