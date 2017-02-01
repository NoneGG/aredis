from aredis.utils import (dict_merge,
                          bool_ok,
                          string_keys_to_dict)


class ListsCommandMixin:

    RESPONSE_CALLBACKS = dict_merge(
        string_keys_to_dict(
            'BLPOP BRPOP',
            lambda r: r and tuple(r) or None
        ),
        string_keys_to_dict(
            # these return OK, or int if redis-server is >=1.3.4
            'LPUSH RPUSH',
            lambda r: isinstance(r, int) and r or r == b'OK'
        ),
        string_keys_to_dict('LSET LTRIM', bool_ok),
        string_keys_to_dict('LINSERT LLEN LPUSHX RPUSHX', int),
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
        return await self.execute_command('BLPOP', *keys)

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
        return await self.execute_command('BRPOP', *keys)

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
        return await self.execute_command('BRPOPLPUSH', src, dst, timeout)

    async def lindex(self, name, index):
        """
        Return the item from list ``name`` at position ``index``

        Negative indexes are supported and will return an item at the
        end of the list
        """
        return await self.execute_command('LINDEX', name, index)

    async def linsert(self, name, where, refvalue, value):
        """
        Insert ``value`` in list ``name`` either immediately before or after
        [``where``] ``refvalue``

        Returns the new length of the list on success or -1 if ``refvalue``
        is not in the list.
        """
        return await self.execute_command('LINSERT', name, where, refvalue, value)

    async def llen(self, name):
        "Return the length of the list ``name``"
        return await self.execute_command('LLEN', name)

    async def lpop(self, name):
        "Remove and return the first item of the list ``name``"
        return await self.execute_command('LPOP', name)

    async def lpush(self, name, *values):
        "Push ``values`` onto the head of the list ``name``"
        return await self.execute_command('LPUSH', name, *values)

    async def lpushx(self, name, value):
        "Push ``value`` onto the head of the list ``name`` if ``name`` exists"
        return await self.execute_command('LPUSHX', name, value)

    async def lrange(self, name, start, end):
        """
        Return a slice of the list ``name`` between
        position ``start`` and ``end``

        ``start`` and ``end`` can be negative numbers just like
        Python slicing notation
        """
        return await self.execute_command('LRANGE', name, start, end)

    async def lrem(self, name, count, value):
        """
        Remove the first ``count`` occurrences of elements equal to ``value``
        from the list stored at ``name``.

        The count argument influences the operation in the following ways:
            count > 0: Remove elements equal to value moving from head to tail.
            count < 0: Remove elements equal to value moving from tail to head.
            count = 0: Remove all elements equal to value.
        """
        return await self.execute_command('LREM', name, count, value)

    async def lset(self, name, index, value):
        "Set ``position`` of list ``name`` to ``value``"
        return await self.execute_command('LSET', name, index, value)

    async def ltrim(self, name, start, end):
        """
        Trim the list ``name``, removing all values not within the slice
        between ``start`` and ``end``

        ``start`` and ``end`` can be negative numbers just like
        Python slicing notation
        """
        return await self.execute_command('LTRIM', name, start, end)

    async def rpop(self, name):
        "Remove and return the last item of the list ``name``"
        return await self.execute_command('RPOP', name)

    async def rpoplpush(self, src, dst):
        """
        RPOP a value off of the ``src`` list and atomically LPUSH it
        on to the ``dst`` list.  Returns the value.
        """
        return await self.execute_command('RPOPLPUSH', src, dst)

    async def rpush(self, name, *values):
        "Push ``values`` onto the tail of the list ``name``"
        return await self.execute_command('RPUSH', name, *values)

    async def rpushx(self, name, value):
        "Push ``value`` onto the tail of the list ``name`` if ``name`` exists"
        return await self.execute_command('RPUSHX', name, value)
