import datetime
import time

from coredis.exceptions import DataError, ReadOnlyError, RedisError
from coredis.utils import (
    NodeFlag,
    bool_ok,
    dict_merge,
    iteritems,
    list_or_args,
    nativestr,
    string_keys_to_dict,
)


class BitFieldOperation:
    """
    The command treats a Redis string as a array of bits,
    and is capable of addressing specific integer fields
    of varying bit widths and arbitrary non (necessary) aligned offset.

    The supported types are up to 64 bits for signed integers,
    and up to 63 bits for unsigned integers.

    Offset can be num prefixed with `#` character or num directly,
    for command detail you should see: https://redis.io/commands/bitfield
    """

    def __init__(self, redis_client, key, readonly=False):
        self._command_stack = ["BITFIELD" if not readonly else "BITFIELD_RO", key]
        self.redis = redis_client
        self.readonly = readonly

    def __del__(self):
        self._command_stack.clear()

    def set(self, type, offset, value):
        """
        Set the specified bit field and returns its old value.
        """

        if self.readonly:
            raise ReadOnlyError()

        self._command_stack.extend(["SET", type, offset, value])

        return self

    def get(self, type, offset):
        """
        Returns the specified bit field.
        """

        self._command_stack.extend(["GET", type, offset])

        return self

    def incrby(self, type, offset, increment):
        """
        Increments or decrements (if a negative increment is given)
        the specified bit field and returns the new value.
        """

        if self.readonly:
            raise ReadOnlyError()

        self._command_stack.extend(["INCRBY", type, offset, increment])

        return self

    def overflow(self, type="SAT"):
        """
        fine-tune the behavior of the increment or decrement overflow,
        have no effect unless used before `incrby`
        three types are available: WRAP|SAT|FAIL
        """

        if self.readonly:
            raise ReadOnlyError()
        self._command_stack.extend(["OVERFLOW", type])

        return self

    async def exc(self):
        """execute commands in command stack"""

        return await self.redis.execute_command(*self._command_stack)


class StringsCommandMixin:
    RESPONSE_CALLBACKS = dict_merge(
        string_keys_to_dict("MSETNX PSETEX SETEX SETNX", bool),
        string_keys_to_dict(
            "BITCOUNT BITPOS DECRBY GETBIT INCRBY " "STRLEN SETBIT", int
        ),
        {
            "INCRBYFLOAT": float,
            "MSET": bool_ok,
            "SET": lambda r: r and nativestr(r) == "OK",
        },
    )

    async def append(self, key, value):
        """
        Appends the string ``value`` to the value at ``key``. If ``key``
        doesn't already exist, create it with a value of ``value``.
        Returns the new length of the value at ``key``.
        """

        return await self.execute_command("APPEND", key, value)

    async def bitcount(self, key, start=None, end=None):
        """
        Returns the count of set bits in the value of ``key``.  Optional
        ``start`` and ``end`` paramaters indicate which bytes to consider
        """
        params = [key]

        if start is not None and end is not None:
            params.append(start)
            params.append(end)
        elif (start is not None and end is None) or (end is not None and start is None):
            raise RedisError("Both start and end must be specified")

        return await self.execute_command("BITCOUNT", *params)

    async def bitop(self, operation, dest, *keys):
        """
        Perform a bitwise operation using ``operation`` between ``keys`` and
        store the result in ``dest``.
        """

        return await self.execute_command("BITOP", operation, dest, *keys)

    async def bitpos(self, key, bit, start=None, end=None):
        """
        Return the position of the first bit set to 1 or 0 in a string.
        ``start`` and ``end`` difines search range. The range is interpreted
        as a range of bytes and not a range of bits, so start=0 and end=2
        means to look at the first three bytes.
        """

        if bit not in (0, 1):
            raise RedisError("bit must be 0 or 1")
        params = [key, bit]

        start is not None and params.append(start)

        if start is not None and end is not None:
            params.append(end)
        elif start is None and end is not None:
            raise RedisError("start argument is not set, " "when end is specified")

        return await self.execute_command("BITPOS", *params)

    def bitfield(self, key):
        """
        Return a :class:`BitFieldOperation` instance to conveniently construct one or
        more bitfield operations on ``key``.
        """

        return BitFieldOperation(self, key)

    def bitfield_ro(self, key):
        """
        Return a :class:`BitFieldOperation` instance to conveniently construct bitfield
        operations on a read only replica against ``key``.

        Raises :class:`ReadOnlyError` if a write operation is attempted

        .. versionadded:: 2.1.0
        """

        return BitFieldOperation(self, key, readonly=True)

    async def decr(self, name, amount=1):
        """
        Decrements the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as 0 - ``amount``
        """

        return await self.execute_command("DECRBY", name, amount)

    async def decrby(self, name, amount=1):
        """
        Decrements the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as 0 - ``amount``

        .. versionadded:: 2.1.0
        """

        return await self.execute_command("DECRBY", name, amount)

    async def get(self, name):
        """
        Return the value at key ``name``, or None if the key doesn't exist
        """

        return await self.execute_command("GET", name)

    async def getdel(self, name):
        """
        Get the value at key ``name`` and delete the key. This command
        is similar to GET, except for the fact that it also deletes
        the key on success (if and only if the key's value type
        is a string).

        .. versionadded:: 2.1.0
        """

        return await self.execute_command("GETDEL", name)

    async def getex(self, name, ex=None, px=None, exat=None, pxat=None, persist=False):
        """
        Get the value of key and optionally set its expiration.

        GETEX is similar to GET, but is a write command with
        additional options. All time parameters can be given as
        :class:`datetime.timedelta` or integers.

        :param name: name of the key
        :param ex: sets an expire flag on key ``name`` for ``ex`` seconds.
        :param px: sets an expire flag on key ``name`` for ``px`` milliseconds.
        :param exat: sets an expire flag on key ``name`` for ``ex`` seconds,
         specified in unix time.
        :param pxat: sets an expire flag on key ``name`` for ``ex`` milliseconds,
         specified in unix time.
        :param persist: remove the time to live associated with ``name``.

        .. versionadded:: 2.1.0
        """

        opset = {ex, px, exat, pxat}

        if len(opset) > 2 or len(opset) > 1 and persist:
            raise DataError(
                "``ex``, ``px``, ``exat``, ``pxat``, "
                "and ``persist`` are mutually exclusive."
            )

        pieces = []
        # similar to set command

        if ex is not None:
            pieces.append("EX")

            if isinstance(ex, datetime.timedelta):
                ex = int(ex.total_seconds())
            pieces.append(ex)

        if px is not None:
            pieces.append("PX")

            if isinstance(px, datetime.timedelta):
                px = int(px.total_seconds() * 1000)
            pieces.append(px)
        # similar to pexpireat command

        if exat is not None:
            pieces.append("EXAT")

            if isinstance(exat, datetime.datetime):
                s = int(exat.microsecond / 1000000)
                exat = int(time.mktime(exat.timetuple())) + s
            pieces.append(exat)

        if pxat is not None:
            pieces.append("PXAT")

            if isinstance(pxat, datetime.datetime):
                ms = int(pxat.microsecond / 1000)
                pxat = int(time.mktime(pxat.timetuple())) * 1000 + ms
            pieces.append(pxat)

        if persist:
            pieces.append("PERSIST")

        return await self.execute_command("GETEX", name, *pieces)

    async def getbit(self, name, offset):
        "Returns a boolean indicating the value of ``offset`` in ``name``"

        return await self.execute_command("GETBIT", name, offset)

    async def getrange(self, key, start, end):
        """
        Returns the substring of the string value stored at ``key``,
        determined by the offsets ``start`` and ``end`` (both are inclusive)
        """

        return await self.execute_command("GETRANGE", key, start, end)

    async def getset(self, name, value):
        """
        Sets the value at key ``name`` to ``value``
        and returns the old value at key ``name`` atomically.
        """

        return await self.execute_command("GETSET", name, value)

    async def incr(self, name, amount=1):
        """
        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        """

        return await self.execute_command("INCRBY", name, amount)

    async def incrby(self, name, amount=1):
        """
        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        """

        # An alias for ``incr()``, because it is already implemented
        # as INCRBY redis command.

        return await self.incr(name, amount)

    async def incrbyfloat(self, name, amount=1.0):
        """
        Increments the value at key ``name`` by floating ``amount``.
        If no key exists, the value will be initialized as ``amount``
        """

        return await self.execute_command("INCRBYFLOAT", name, amount)

    async def mget(self, keys, *args):
        """
        Returns a list of values ordered identically to ``keys``
        """
        args = list_or_args(keys, args)

        return await self.execute_command("MGET", *args)

    async def mset(self, *args, **kwargs):
        """
        Sets key/values based on a mapping. Mapping can be supplied as a single
        dictionary argument or as kwargs.
        """

        if args:
            if len(args) != 1 or not isinstance(args[0], dict):
                raise RedisError("MSET requires **kwargs or a single dict arg")
            kwargs.update(args[0])
        items = []

        for pair in iteritems(kwargs):
            items.extend(pair)

        return await self.execute_command("MSET", *items)

    async def msetnx(self, *args, **kwargs):
        """
        Sets key/values based on a mapping if none of the keys are already set.
        Mapping can be supplied as a single dictionary argument or as kwargs.
        Returns a boolean indicating if the operation was successful.
        """

        if args:
            if len(args) != 1 or not isinstance(args[0], dict):
                raise RedisError("MSETNX requires **kwargs or a single " "dict arg")
            kwargs.update(args[0])
        items = []

        for pair in iteritems(kwargs):
            items.extend(pair)

        return await self.execute_command("MSETNX", *items)

    async def psetex(self, name, time_ms, value):
        """
        Set the value of key ``name`` to ``value`` that expires in ``time_ms``
        milliseconds. ``time_ms`` can be represented by an integer or a Python
        timedelta object
        """

        if isinstance(time_ms, datetime.timedelta):
            ms = int(time_ms.microseconds / 1000)
            time_ms = (time_ms.seconds + time_ms.days * 24 * 3600) * 1000 + ms

        return await self.execute_command("PSETEX", name, time_ms, value)

    async def set(self, name, value, ex=None, px=None, nx=False, xx=False):
        """
        Set the value at key ``name`` to ``value``

        ``ex`` sets an expire flag on key ``name`` for ``ex`` seconds.

        ``px`` sets an expire flag on key ``name`` for ``px`` milliseconds.

        ``nx`` if set to True, set the value at key ``name`` to ``value`` if it
            does not already exist.

        ``xx`` if set to True, set the value at key ``name`` to ``value`` if it
            already exists.
        """
        pieces = [name, value]

        if ex is not None:
            pieces.append("EX")

            if isinstance(ex, datetime.timedelta):
                ex = ex.seconds + ex.days * 24 * 3600
            pieces.append(ex)

        if px is not None:
            pieces.append("PX")

            if isinstance(px, datetime.timedelta):
                ms = int(px.microseconds / 1000)
                px = (px.seconds + px.days * 24 * 3600) * 1000 + ms
            pieces.append(px)

        if nx:
            pieces.append("NX")

        if xx:
            pieces.append("XX")

        return await self.execute_command("SET", *pieces)

    async def setbit(self, name, offset, value):
        """
        Flag the ``offset`` in ``name`` as ``value``. Returns a boolean
        indicating the previous value of ``offset``.
        """
        value = value and 1 or 0

        return await self.execute_command("SETBIT", name, offset, value)

    async def setex(self, name, time, value):
        """
        Set the value of key ``name`` to ``value`` that expires in ``time``
        seconds. ``time`` can be represented by an integer or a Python
        timedelta object.
        """

        if isinstance(time, datetime.timedelta):
            time = time.seconds + time.days * 24 * 3600

        return await self.execute_command("SETEX", name, time, value)

    async def setnx(self, name, value):
        """
        Sets the value of key ``name`` to ``value`` if key doesn't exist
        """

        return await self.execute_command("SETNX", name, value)

    async def setrange(self, name, offset, value):
        """
        Overwrite bytes in the value of ``name`` starting at ``offset`` with
        ``value``. If ``offset`` plus the length of ``value`` exceeds the
        length of the original value, the new value will be larger than before.
        If ``offset`` exceeds the length of the original value, null bytes
        will be used to pad between the end of the previous value and the start
        of what's being injected.

        Returns the length of the new string.
        """

        return await self.execute_command("SETRANGE", name, offset, value)

    async def strlen(self, name):
        """Returns the number of bytes stored in the value of ``name``"""

        return await self.execute_command("STRLEN", name)

    async def substr(self, name, start, end=-1):
        """
        Returns a substring of the string at key ``name``. ``start`` and ``end``
        are 0-based integers specifying the portion of the string to return.
        """

        return await self.execute_command("SUBSTR", name, start, end)


class ClusterStringsCommandMixin(StringsCommandMixin):

    NODES_FLAGS = {"BITOP": NodeFlag.BLOCKED}

    async def mget(self, keys, *args):
        """
        Returns a list of values ordered identically to ``keys``

        Cluster impl:
            Itterate all keys and send GET for each key.
            This will go alot slower than a normal mget call in StrictRedis.

            Operation is no longer atomic.
        """
        res = list()

        for arg in list_or_args(keys, args):
            res.append(await self.get(arg))

        return res

    async def mset(self, *args, **kwargs):
        """
        Sets key/values based on a mapping. Mapping can be supplied as a single
        dictionary argument or as kwargs.

        Cluster impl:
            Itterate over all items and do SET on each (k,v) pair

            Operation is no longer atomic.
        """

        if args:
            if len(args) != 1 or not isinstance(args[0], dict):
                raise RedisError("MSET requires **kwargs or a single dict arg")
            kwargs.update(args[0])

        for pair in iteritems(kwargs):
            await self.set(pair[0], pair[1])

        return True

    async def msetnx(self, *args, **kwargs):
        """
        Sets key/values based on a mapping if none of the keys are already set.
        Mapping can be supplied as a single dictionary argument or as kwargs.
        Returns a boolean indicating if the operation was successful.

        Clutser impl:
            Itterate over all items and do GET to determine if all keys do not exists.
            If true then call mset() on all keys.
        """

        if args:
            if len(args) != 1 or not isinstance(args[0], dict):
                raise RedisError("MSETNX requires **kwargs or a single dict arg")
            kwargs.update(args[0])

        # Itterate over all items and fail fast if one value is True.

        for k, _ in kwargs.items():
            if await self.get(k):
                return False

        return await self.mset(**kwargs)
