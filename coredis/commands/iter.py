#!/usr/bin/python
# -*- coding: utf-8 -*-


class IterCommandMixin:
    """
    convenient function of scan iter, make it a class separately
    because yield can not be used in async function in Python3.6
    """

    RESPONSE_CALLBACKS = {}

    async def scan_iter(self, match=None, count=None):
        """
        Make an iterator using the SCAN command so that the client doesn't
        need to remember the cursor position.

        ``match`` allows for filtering the keys by pattern

        ``count`` allows for hint the minimum number of returns
        """
        cursor = "0"
        while cursor != 0:
            cursor, data = await self.scan(cursor=cursor, match=match, count=count)
            for item in data:
                yield item

    async def sscan_iter(self, name, match=None, count=None):
        """
        Make an iterator using the SSCAN command so that the client doesn't
        need to remember the cursor position.

        ``match`` allows for filtering the keys by pattern

        ``count`` allows for hint the minimum number of returns
        """
        cursor = "0"
        while cursor != 0:
            cursor, data = await self.sscan(
                name, cursor=cursor, match=match, count=count
            )
            for item in data:
                yield item

    async def hscan_iter(self, name, match=None, count=None):
        """
        Make an iterator using the HSCAN command so that the client doesn't
        need to remember the cursor position.

        ``match`` allows for filtering the keys by pattern

        ``count`` allows for hint the minimum number of returns
        """
        cursor = "0"
        while cursor != 0:
            cursor, data = await self.hscan(
                name, cursor=cursor, match=match, count=count
            )
            for item in data.items():
                yield item

    async def zscan_iter(self, name, match=None, count=None, score_cast_func=float):
        """
        Make an iterator using the ZSCAN command so that the client doesn't
        need to remember the cursor position.

        ``match`` allows for filtering the keys by pattern

        ``count`` allows for hint the minimum number of returns

        ``score_cast_func`` a callable used to cast the score return value
        """
        cursor = "0"
        while cursor != 0:
            cursor, data = await self.zscan(
                name,
                cursor=cursor,
                match=match,
                count=count,
                score_cast_func=score_cast_func,
            )
            for item in data:
                yield item


class ClusterIterCommandMixin(IterCommandMixin):
    async def scan_iter(self, match=None, count=None):
        nodes = await self.cluster_nodes()
        for node in nodes:
            if "master" in node["flags"]:
                cursor = "0"
                while cursor != 0:
                    pieces = [cursor]
                    if match is not None:
                        pieces.extend(["MATCH", match])
                    if count is not None:
                        pieces.extend(["COUNT", count])
                    response = await self.execute_command_on_nodes(
                        [node], "SCAN", *pieces
                    )
                    cursor, data = list(response.values())[0]
                    for item in data:
                        yield item
