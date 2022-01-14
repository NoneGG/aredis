from coredis.exceptions import RedisError
from coredis.utils import bool_ok, dict_merge, pairs_to_dict, string_keys_to_dict


def stream_list(response):
    result = []
    if response:
        for r in response:
            kv_pairs = r[1]
            kv_dict = dict()
            while kv_pairs and len(kv_pairs) > 1:
                kv_dict[kv_pairs.pop()] = kv_pairs.pop()
            result.append((r[0], kv_dict))
    return result


def multi_stream_list(response):
    result = dict()
    if response:
        for r in response:
            result[r[0]] = stream_list(r[1])
    return result


def list_of_pairs_to_dict(response):
    return [pairs_to_dict(row) for row in response]


def parse_xinfo_stream(response):
    res = pairs_to_dict(response)
    if res["first-entry"] and len(res["first-entry"]) > 0:
        res["first-entry"][1] = pairs_to_dict(res["first-entry"][1])
    if res["last-entry"] and len(res["last-entry"]) > 0:
        res["last-entry"][1] = pairs_to_dict(res["last-entry"][1])
    return res


class StreamsCommandMixin:
    RESPONSE_CALLBACKS = dict_merge(
        string_keys_to_dict("XREVRANGE XRANGE", stream_list),
        string_keys_to_dict("XREAD XREADGROUP", multi_stream_list),
        {
            "XINFO GROUPS": list_of_pairs_to_dict,
            "XINFO STREAM": parse_xinfo_stream,
            "XINFO CONSUMERS": list_of_pairs_to_dict,
            "XGROUP SETID": bool_ok,
            "XGROUP CREATE": bool_ok,
        },
    )

    async def xadd(
        self, name: str, entry: dict, max_len=None, stream_id="*", approximate=True
    ) -> str:
        """
        Appends the specified stream entry to the stream at the specified key.
        If the key does not exist, as a side effect of running
        this command the key is created with a stream value.

        :param name: name of the stream
        :param entry: key-values to be appended to the stream
        :param max_len: max length of the stream
         length will not be limited max_len is set to None
         notice: max_len should be int greater than 0,
         if set to 0 or negative, the stream length will not be limited
        :param stream_id: id of the options appended to the stream.
         The XADD command will auto-generate a unique id for you
         if the id argument specified is the * character.
         ID are specified by two numbers separated by a "-" character
        :param approximate: whether redis will limit
         the stream with given max length exactly, if set to True,
         there will be a few tens of entries more,
         but never less than 1000 items
        :return: id auto generated or the specified id given.

        .. note:: specified id without "-" character will be completed like "id-0"
        """
        pieces = []
        if max_len is not None:
            if not isinstance(max_len, int) or max_len < 1:
                raise RedisError("XADD maxlen must be a positive integer")
            pieces.append("MAXLEN")
            if approximate:
                pieces.append("~")
            pieces.append(str(max_len))
        pieces.append(stream_id)
        for kv in entry.items():
            pieces.extend(list(kv))
        return await self.execute_command("XADD", name, *pieces)

    async def xlen(self, name: str) -> int:
        """
        Returns the number of elements in a given stream.
        """
        return await self.execute_command("XLEN", name)

    async def xrange(self, name: str, start="-", end="+", count=None) -> list:
        """
        Read stream values within an interval.

        :param name: name of the stream.
        :param start: first stream ID. defaults to '-',
         meaning the earliest available.
        :param end: last stream ID. defaults to '+',
         meaning the latest available.
        :param count: if set, only return this many items, beginning with the
         earliest available.
        :return: list of (stream_id, entry(k-v pair))
        """

        pieces = [start, end]
        if count is not None:
            if not isinstance(count, int) or count < 1:
                raise RedisError("XRANGE count must be a positive integer")
            pieces.append("COUNT")
            pieces.append(str(count))
        return await self.execute_command("XRANGE", name, *pieces)

    async def xrevrange(self, name: str, start="+", end="-", count=None) -> list:
        """
        Read stream values within an interval, in reverse order.

        :param name: name of the stream
        :param start: first stream ID. defaults to '+',
               meaning the latest available.
        :param end: last stream ID. defaults to '-',
                meaning the earliest available.
        :param count: if set, only return this many items, beginning with the
               latest available.

        """
        pieces = [start, end]
        if count is not None:
            if not isinstance(count, int) or count < 1:
                raise RedisError("XREVRANGE count must be a positive integer")
            pieces.append("COUNT")
            pieces.append(str(count))
        return await self.execute_command("XREVRANGE", name, *pieces)

    async def xread(self, count=None, block=None, **streams) -> dict:
        """
        Read data from one or multiple streams,
        only returning entries with an ID greater
        than the last received ID reported by the caller.

        :param count: int, if set, only return this many items, beginning with the
               earliest available.
        :param block: int, milliseconds we want to block before timing out,
                if the BLOCK option is not used, the command is synchronous
        :param streams: stream_name - stream_id mapping
        :return dict like {stream_name: [(stream_id: entry), ...]}
        """
        pieces = []
        if block is not None:
            if not isinstance(block, int) or block < 0:
                raise RedisError("XREAD block must be a positive integer")
            pieces.append("BLOCK")
            pieces.append(str(block))
        if count is not None:
            if not isinstance(count, int) or count < 1:
                raise RedisError("XREAD count must be a positive integer")
            pieces.append("COUNT")
            pieces.append(str(count))
        pieces.append("STREAMS")
        ids = []
        for partial_stream in streams.items():
            pieces.append(partial_stream[0])
            ids.append(partial_stream[1])
        pieces.extend(ids)
        return await self.execute_command("XREAD", *pieces)

    async def xreadgroup(
        self, group: str, consumer_id: str, count=None, block=None, **streams
    ):
        """
        Read data from one or multiple streams via the consumer group,
        only returning entries with an ID greater
        than the last received ID reported by the caller.

        :param group: the name of the consumer group
        :param consumer_id: the name of the consumer that is attempting to read
        :param count: int, if set, only return this many items, beginning with the
               earliest available.
        :param block: int, milliseconds we want to block before timing out,
                if the BLOCK option is not used, the command is synchronous
        :param streams: stream_name - stream_id mapping
        :return dict like {stream_name: [(stream_id: entry), ...]}
        """
        pieces = ["GROUP", group, consumer_id]
        if block is not None:
            if not isinstance(block, int) or block < 1:
                raise RedisError("XREAD block must be a positive integer")
            pieces.append("BLOCK")
            pieces.append(str(block))
        if count is not None:
            if not isinstance(count, int) or count < 1:
                raise RedisError("XREAD count must be a positive integer")
            pieces.append("COUNT")
            pieces.append(str(count))
        pieces.append("STREAMS")
        ids = []
        for partial_stream in streams.items():
            pieces.append(partial_stream[0])
            ids.append(partial_stream[1])
        pieces.extend(ids)
        return await self.execute_command("XREADGROUP", *pieces)

    async def xpending(
        self, name: str, group: str, start="-", end="+", count=None, consumer=None
    ) -> list:
        """
        Fetching data from a stream via a consumer group,
        and not acknowledging such data,
        has the effect of creating pending entries.
        The XPENDING command is the interface to inspect the list of pending messages.

        :param name: name of the stream
        :param group: name of the consumer group
        :param start: first stream ID. defaults to '-',
               meaning the earliest available.
        :param end: last stream ID. defaults to '+',
                meaning the latest available.
        :param count: int, number of entries
                [NOTICE] only when count is set to int,
                start & end options will have effect
                and detail of pending entries will be returned
        :param consumer: str, consumer of the stream in the group
                [NOTICE] only when count is set to int,
                this option can be appended to
                query pending entries of given consumer
        """
        pieces = [name, group]
        if count is not None:
            pieces.extend([start, end, count])
            if consumer is not None:
                pieces.append(str(consumer))
        # todo: may there be a parse function
        return await self.execute_command("XPENDING", *pieces)

    async def xtrim(self, name: str, max_len: int, approximate=True) -> int:
        """
        XTRIM is designed to accept different trimming strategies,
        even if currently only MAXLEN is implemented.

        :param name: name of the stream
        :param max_len: max length of the stream after being trimmed
        :param approximate: whether redis will limit
         the stream with given max length exactly, if set to True,
         there will be a few tens of entries more,
         but never less than 1000 items:

        :return: number of entries trimmed
        """
        pieces = ["MAXLEN"]
        if approximate:
            pieces.append("~")
        pieces.append(max_len)
        return await self.execute_command("XTRIM", name, *pieces)

    async def xdel(self, name: str, stream_id: str) -> int:
        """
        [NOTICE] In the current implementation, memory is not
        really reclaimed until a macro node is completely empty,
        so you should not abuse this feature.

        remove items from the middle of a stream, just by ID.

        :param name: name of the stream
        :param stream_id: id of the options appended to the stream.
        """
        return await self.execute_command("XDEL", name, stream_id)

    async def xinfo_consumers(self, name: str, group: str) -> list:
        """
        XINFO command is an observability interface that can be used
        with sub-commands in order to get information
        about streams or consumer groups.

        :param name: name of the stream
        :param group: name of the consumer group
        """
        return await self.execute_command("XINFO CONSUMERS", name, group)

    async def xinfo_groups(self, name: str) -> list:
        """
        XINFO command is an observability interface that can be used
        with sub-commands in order to get information
        about streams or consumer groups.

        :param name: name of the stream
        """
        return await self.execute_command("XINFO GROUPS", name)

    async def xinfo_stream(self, name: str) -> dict:
        """
        XINFO command is an observability interface that can be used
        with sub-commands in order to get information
        about streams or consumer groups.

        :param name: name of the stream
        """
        return await self.execute_command("XINFO STREAM", name)

    async def xack(self, name: str, group: str, stream_id: str) -> int:
        """
        XACK is the command that allows a consumer to mark a pending message as correctly processed.

        :param name: name of the stream
        :param group: name of the consumer group
        :param stream_id: id of the entry the consumer wants to mark
        :return: number of entry marked
        """
        return await self.execute_command("XACK", name, group, stream_id)

    async def xclaim(
        self, name: str, group: str, consumer: str, min_idle_time: int, *stream_ids
    ):
        """
        Gets ownership of one or multiple messages in the Pending Entries List of a given stream
        consumer group.

        :param name: name of the stream
        :param group: name of the consumer group
        :param consumer: name of the consumer
        :param min_idle_time: ms
            If the message ID (among the specified ones) exists, and its idle time greater
            or equal to min_idle_time, then the message new owner
            becomes the specified <consumer>. If the minimum idle time specified
            is zero, messages are claimed regardless of their idle time.
        :param stream_ids:
        """
        return await self.execute_command(
            "XCLAIM", name, group, consumer, min_idle_time, *stream_ids
        )

    async def xgroup_create(self, name: str, group: str, stream_id="$") -> bool:
        """
        XGROUP is used in order to create, destroy and manage consumer groups.

        :param name: name of the stream
        :param group: name of the consumer group
        :param stream_id:
            If we provide $ as we did, then only new messages arriving
            in the stream from now on will be provided to the consumers in the group.
            If we specify 0 instead the consumer group will consume all the messages
            in the stream history to start with.
            Of course, you can specify any other valid ID
        """
        return await self.execute_command("XGROUP CREATE", name, group, stream_id)

    async def xgroup_set_id(self, name: str, group: str, stream_id: str) -> bool:
        """
        :param name: name of the stream
        :param group: name of the consumer group
        :param stream_id:
            If we provide $ as we did, then only new messages arriving
            in the stream from now on will be provided to the consumers in the group.
            If we specify 0 instead the consumer group will consume all the messages
            in the stream history to start with.
            Of course, you can specify any other valid ID
        """
        return await self.execute_command("XGROUP SETID", name, group, stream_id)

    async def xgroup_destroy(self, name: str, group: str) -> int:
        """
        XGROUP is used in order to create, destroy and manage consumer groups.

        :param name: name of the stream
        :param group: name of the consumer group
        """
        return await self.execute_command("XGROUP DESTROY", name, group)

    async def xgroup_del_consumer(self, name: str, group: str, consumer: str) -> int:
        """
        XGROUP is used in order to create, destroy and manage consumer groups.

        :param name: name of the stream
        :param group: name of the consumer group
        :param consumer: name of the consumer
        """
        return await self.execute_command("XGROUP DELCONSUMER", name, group, consumer)
