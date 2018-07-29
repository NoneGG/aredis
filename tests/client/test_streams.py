#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest
import aredis
from aredis.exceptions import RedisError

from tests.client.conftest import skip_if_server_version_lt


class TestStreams(object):

    @skip_if_server_version_lt('4.9.103')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xadd_with_wrong_id(self, r):
        with pytest.raises(RedisError):
            await r.xadd('test_stream', {'k1': 'v1', 'k2': 1}, stream_id=0,
                         max_len=10, approximate=False)

    @skip_if_server_version_lt('4.9.103')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xadd_without_given_id(self, r):
        await r.flushdb()
        stream_id = await r.xadd('test_stream', {'k1': 'v1', 'k2': 1})
        assert len(stream_id.decode().split('-')) == 2

    @skip_if_server_version_lt('4.9.103')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xadd_with_given_id(self, r):
        await r.flushdb()
        stream_id = await r.xadd('test_stream', {'k1': 'v1', 'k2': 1}, stream_id='12321')
        assert stream_id == b'12321-0'
        await r.flushdb()
        stream_id = await r.xadd('test_stream', {'k1': 'v1', 'k2': 1}, stream_id='12321-0')
        assert stream_id == b'12321-0'

    @skip_if_server_version_lt('4.9.103')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xadd_with_maxlen_accurately(self, r):
        await r.flushdb()
        for idx in range(10):
            await r.xadd('test_stream', {'k1': 'v1', 'k2': 1}, max_len=2, approximate=False)
        # also test xlen here
        length = await r.xlen('test_stream')
        assert length == 2

    @skip_if_server_version_lt('4.9.103')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xadd_with_maxlen_approximately(self, r):
        await r.flushdb()
        for idx in range(10):
            await r.xadd('test_stream', {'k1': 'v1', 'k2': 1}, max_len=2, approximate=True)
        length = await r.xlen('test_stream')
        assert length == 10

    @skip_if_server_version_lt('4.9.103')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xrange(self, r):
        await r.flushdb()
        for idx in range(1, 10):
            await r.xadd('test_stream', {'k1': 'v1', 'k2': 1}, stream_id=idx,
                         max_len=10, approximate=False)
        entries = await r.xrange('test_stream', count=5)
        assert len(entries) == 5 and isinstance(entries, list) and isinstance(entries[0], tuple)
        entries = await r.xrange('test_stream', start='2', end='3', count=3)
        assert len(entries) == 2 and entries[0][0] == b'2-0'

    @skip_if_server_version_lt('4.9.103')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xrevrange(self, r):
        await r.flushdb()
        for idx in range(1, 10):
            await r.xadd('test_stream', {'k1': 'v1', 'k2': 1}, stream_id=idx,
                         max_len=10, approximate=False)
        entries = await r.xrevrange('test_stream', count=5)
        assert len(entries) == 5 and isinstance(entries, list) and isinstance(entries[0], tuple)
        entries = await r.xrevrange('test_stream', start='2', end='3', count=3)
        assert len(entries) == 0
        entries = await r.xrevrange('test_stream', start='3', end='2', count=3)
        assert len(entries) == 2 and entries[0][0] == b'3-0'

    @skip_if_server_version_lt('4.9.103')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_xread(self, r):
        await r.flushdb()
        for idx in range(1, 10):
            await r.xadd('test_stream', {'k1': 'v1', 'k2': 1}, stream_id=idx)
        entries = await r.xread(count=5, block=10, test_stream='0')
        assert len(entries[b'test_stream']) == 5
        entries = await r.xread(count=10, block=10, test_stream='$')
        assert not entries
        entries = await r.xread(count=10, block=10, test_stream='2')
        assert entries and len(entries[b'test_stream']) == 7
        assert entries[b'test_stream'][0] == (b'3-0', {b'k1': b'v1', b'k2': b'1'})
