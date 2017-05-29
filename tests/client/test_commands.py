from __future__ import with_statement
import binascii
import datetime
import pytest
import aredis
import time
from string import ascii_letters

from aredis.utils import (b, iteritems,
                          iterkeys, itervalues)
from aredis.commands.server import parse_info
from aredis.exceptions import (RedisError,
                               ResponseError,
                               DataError)

from .conftest import (skip_if_server_version_lt,
                       skip_python_vsersion_lt)


async def redis_server_time(client):
    seconds, milliseconds = await client.time()
    timestamp = float('%s.%s' % (seconds, milliseconds))
    return datetime.datetime.fromtimestamp(timestamp)


# RESPONSE CALLBACKS
class TestResponseCallbacks(object):
    "Tests for the response callback system"

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_response_callbacks(self, r):
        assert r.response_callbacks == aredis.StrictRedis.RESPONSE_CALLBACKS
        assert id(r.response_callbacks) != id(aredis.StrictRedis.RESPONSE_CALLBACKS)
        r.set_response_callback('GET', lambda x: 'static')
        await r.set('a', 'foo')
        assert await r.get('a') == 'static'


class TestRedisCommands(object):

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_command_on_invalid_key_type(self, r):
        await r.flushdb()
        await r.lpush('a', '1')
        with pytest.raises(ResponseError):
            await r.get('a')

    # SERVER INFORMATION
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_client_list(self, r):
        clients = await r.client_list()
        assert isinstance(clients[0], dict)
        assert 'addr' in clients[0]

    @skip_if_server_version_lt('2.6.9')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_client_getname(self, r):
        assert await r.client_getname() is None

    @skip_if_server_version_lt('2.6.9')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_client_setname(self, r):
        assert await r.client_setname('redis_py_test')
        assert await r.client_getname() == 'redis_py_test'

    @skip_if_server_version_lt('2.9.5')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_client_pause(self, r, event_loop):
        await r.flushdb()
        key = 'key_should_expire'
        another_client = aredis.StrictRedis(loop=event_loop)
        await r.set(key, 1, px=100)
        assert await r.client_pause(100)
        res = await another_client.get(key)
        assert not res

    @skip_if_server_version_lt('2.8.12')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_role_master(self, event_loop, mock_resp_role):
        role = await mock_resp_role.role()
        assert role['role'] == 'master'
        slave_offset = role['slaves'][0]['offset']
        assert slave_offset == role['offset']

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_config_get(self, r):
        data = await r.config_get()
        assert 'maxmemory' in data
        assert data['maxmemory'].isdigit()

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_config_resetstat(self, r):
        await r.ping()
        prior_commands_processed = int((await r.info())['total_commands_processed'])
        assert prior_commands_processed >= 1
        await r.config_resetstat()
        reset_commands_processed = int((await r.info())['total_commands_processed'])
        assert reset_commands_processed < prior_commands_processed

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_config_set(self, r):
        data = await r.config_get()
        rdbname = data['dbfilename']
        try:
            assert await r.config_set('dbfilename', 'redis_py_test.rdb')
            assert (await r.config_get())['dbfilename'] == 'redis_py_test.rdb'
        finally:
            assert await r.config_set('dbfilename', rdbname)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_dbsize(self, r):
        await r.flushdb()
        await r.set('a', 'foo')
        await r.set('b', 'bar')
        assert await r.dbsize() == 2

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_echo(self, r):
        assert await r.echo('foo bar') == b'foo bar'

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_info(self, r):
        await r.set('a', 'foo')
        await r.set('b', 'bar')
        info = await r.info()
        assert isinstance(info, dict)
        assert info['db0']['keys'] == 2

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_lastsave(self, r):
        assert isinstance(await r.lastsave(), datetime.datetime)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_object(self, r):
        await r.set('a', 'foo')
        assert isinstance(await r.object('refcount', 'a'), int)
        assert isinstance(await r.object('idletime', 'a'), int)
        assert await r.object('encoding', 'a') in (b('raw'), b('embstr'))
        assert await r.object('idletime', 'invalid-key') is None

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_ping(self, r):
        assert await r.ping()

    async def slowlog(self, *, loop):
        client = aredis.StrictRedis(loop=loop)
        current_config = await client.config_get()
        old_slower_than_value = current_config['slowlog-log-slower-than']
        old_max_length_value = current_config['slowlog-max-len']
        await client.config_set('slowlog-log-slower-than', 0)
        await client.config_set('slowlog-max-len', 128)
        return old_slower_than_value, old_max_length_value

    async def cleanup(self, old_slower_than_value, old_max_legnth_value, *, loop):
        client = aredis.StrictRedis(loop=loop)
        await client.config_set('slowlog-log-slower-than', old_slower_than_value)
        await client.config_set('slowlog-max-len', old_max_legnth_value)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_slowlog_get(self, r, event_loop):
        sl_v, length_v = await self.slowlog(loop=event_loop)
        await r.slowlog_reset()
        unicode_string = '3456abcd3421'
        await r.get(unicode_string)
        slowlog = await r.slowlog_get()
        assert isinstance(slowlog, list)
        commands = [log['command'] for log in slowlog]

        get_command = b(' ').join((b('GET'), unicode_string.encode('utf-8')))
        assert get_command in commands
        assert b('SLOWLOG RESET') in commands
        # the order should be ['GET <uni string>', 'SLOWLOG RESET'],
        # but if other clients are executing commands at the same time, there
        # could be commands, before, between, or after, so just check that
        # the two we care about are in the appropriate order.
        assert commands.index(get_command) < commands.index(b('SLOWLOG RESET'))

        # make sure other attributes are typed correctly
        assert isinstance(slowlog[0]['start_time'], int)
        assert isinstance(slowlog[0]['duration'], int)
        await self.cleanup(sl_v, length_v, loop=event_loop)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_slowlog_get_limit(self, r, event_loop):
        sl_v, length_v = await self.slowlog(loop=event_loop)
        assert await r.slowlog_reset()
        await r.get('foo')
        await r.get('bar')
        slowlog = await r.slowlog_get(1)
        assert isinstance(slowlog, list)
        commands = [log['command'] for log in slowlog]
        assert b('GET foo') not in commands
        assert b('GET bar') in commands
        await self.cleanup(sl_v, length_v, loop=event_loop)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_slowlog_length(self, r, event_loop):
        sl_v, length_v = await self.slowlog(loop=event_loop)
        await r.get('foo')
        assert isinstance(await r.slowlog_len(), int)
        await self.cleanup(sl_v, length_v, loop=event_loop)

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_time(self, r):
        t = await r.time()
        assert len(t) == 2
        assert isinstance(t[0], int)
        assert isinstance(t[1], int)

    # BASIC KEY COMMANDS
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_append(self, r):
        await r.flushdb()
        assert await r.append('a', 'a1') == 2
        assert await r.get('a') == b('a1')
        assert await r.append('a', 'a2') == 4
        assert await r.get('a') == b('a1a2')

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitcount(self, r):
        await r.flushdb()
        await r.setbit('a', 5, True)
        assert await r.bitcount('a') == 1
        await r.setbit('a', 6, True)
        assert await r.bitcount('a') == 2
        await r.setbit('a', 5, False)
        assert await r.bitcount('a') == 1
        await r.setbit('a', 9, True)
        await r.setbit('a', 17, True)
        await r.setbit('a', 25, True)
        await r.setbit('a', 33, True)
        assert await r.bitcount('a') == 5
        assert await r.bitcount('a', 0, -1) == 5
        assert await r.bitcount('a', 2, 3) == 2
        assert await r.bitcount('a', 2, -1) == 3
        assert await r.bitcount('a', -2, -1) == 2
        assert await r.bitcount('a', 1, 1) == 1

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitop_not_empty_string(self, r):
        await r.flushdb()
        await r.set('a', '')
        await r.bitop('not', 'r', 'a')
        assert await r.get('r') is None

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitop_not(self, r):
        test_str = b('\xAA\x00\xFF\x55')
        correct = ~0xAA00FF55 & 0xFFFFFFFF
        await r.set('a', test_str)
        await r.bitop('not', 'r', 'a')
        assert int(binascii.hexlify(await r.get('r')), 16) == correct

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitop_not_in_place(self, r):
        test_str = b('\xAA\x00\xFF\x55')
        correct = ~0xAA00FF55 & 0xFFFFFFFF
        await r.set('a', test_str)
        await r.bitop('not', 'a', 'a')
        assert int(binascii.hexlify(await r.get('a')), 16) == correct

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitop_single_string(self, r):
        test_str = b('\x01\x02\xFF')
        await r.set('a', test_str)
        await r.bitop('and', 'res1', 'a')
        await r.bitop('or', 'res2', 'a')
        await r.bitop('xor', 'res3', 'a')
        assert await r.get('res1') == test_str
        assert await r.get('res2') == test_str
        assert await r.get('res3') == test_str

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitop_string_operands(self, r):
        await r.set('a', b('\x01\x02\xFF\xFF'))
        await r.set('b', b('\x01\x02\xFF'))
        await r.bitop('and', 'res1', 'a', 'b')
        await r.bitop('or', 'res2', 'a', 'b')
        await r.bitop('xor', 'res3', 'a', 'b')
        assert int(binascii.hexlify(await r.get('res1')), 16) == 0x0102FF00
        assert int(binascii.hexlify(await r.get('res2')), 16) == 0x0102FFFF
        assert int(binascii.hexlify(await r.get('res3')), 16) == 0x000000FF

    @skip_if_server_version_lt('2.8.7')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitpos(self, r):
        key = 'key:bitpos'
        await r.set(key, b('\xff\xf0\x00'))
        assert await r.bitpos(key, 0) == 12
        assert await r.bitpos(key, 0, 2, -1) == 16
        assert await r.bitpos(key, 0, -2, -1) == 12
        await r.set(key, b('\x00\xff\xf0'))
        assert await r.bitpos(key, 1, 0) == 8
        assert await r.bitpos(key, 1, 1) == 8
        await r.set(key, b('\x00\x00\x00'))
        assert await r.bitpos(key, 1) == -1

    @skip_if_server_version_lt('2.8.7')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitpos_wrong_arguments(self, r):
        key = 'key:bitpos:wrong:args'
        await r.set(key, b('\xff\xf0\x00'))
        with pytest.raises(RedisError):
            await r.bitpos(key, 0, end=1) == 12
        with pytest.raises(RedisError):
            await r.bitpos(key, 7) == 12

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitfield_set(self, r):
        key = 'key:bitfield:set'
        assert [0] == await r.bitfield(key).set('i4', '#1', 100).exc()
        assert [4] == await r.bitfield(key).set('i4', '4', 101).exc()

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitfield_set(self, r):
        key = 'key:bitfield:get'
        await r.set(key, '\x00d')
        assert [100] == await r.bitfield(key).get('i8', '#1').exc()

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitfield_incrby(self, r):
        key = 'key:bitfield:incrby'
        await r.bitfield(key).incrby('u2', 10, 1).exc()
        assert await r.get(key) == b'\x00\x10'
        # overflow
        await r.delete(key)
        assert [-128] == await r.bitfield(key).incrby('i8', 0, 128).exc()

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_bitfield_overflow(self, r):
        key = 'key:bitfield:overflow'
        # nothing too happen
        assert not await r.bitfield(key).overflow().exc()
        assert [-128] == await r.bitfield(key).overflow('WRAP').incrby('i8', 0, 128).exc()
        await r.delete(key)
        assert [127] == await r.bitfield(key).overflow('SAT').incrby('i8', 0, 128).exc()
        await r.delete(key)
        assert [None] == await r.bitfield(key).overflow('fail').incrby('i8', 0, 128).exc()

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_decr(self, r):
        await r.flushdb()
        assert await r.decr('a') == -1
        assert await r.get('a') == b('-1')
        assert await r.decr('a') == -2
        assert await r.get('a') == b('-2')
        assert await r.decr('a', amount=5) == -7
        assert await r.get('a') == b('-7')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_delete(self, r):
        await r.flushdb()
        assert await r.delete('a') == 0
        await r.set('a', 'foo')
        assert await r.delete('a') == 1

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_delete_with_multiple_keys(self, r):
        await r.set('a', 'foo')
        await r.set('b', 'bar')
        assert await r.delete('a', 'b') == 2
        assert await r.get('a') is None
        assert await r.get('b') is None

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_dump_and_restore(self, r):
        await r.flushdb()
        await r.set('a', 'foo')
        dumped = await r.dump('a')
        await r.delete('a')
        await r.restore('a', 0, dumped)
        assert await r.get('a') == b('foo')

    @skip_if_server_version_lt('3.0.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_dump_and_restore_and_replace(self, r):
        await r.flushdb()
        await r.set('a', 'bar')
        dumped = await r.dump('a')
        with pytest.raises(ResponseError):
            await r.restore('a', 0, dumped)

        await r.restore('a', 0, dumped, replace=True)
        assert await r.get('a') == b('bar')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_exists(self, r):
        await r.flushdb()
        assert not await r.exists('a')
        await r.set('a', 'foo')
        assert await r.exists('a')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_expire(self, r):
        await r.flushdb()
        assert not await r.expire('a', 10)
        await r.set('a', 'foo')
        assert await r.expire('a', 10)
        assert 0 < await r.ttl('a') <= 10
        assert await r.persist('a')
        assert await r.ttl('a') == -1

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_expireat_datetime(self, r):
        await r.flushdb()
        expire_at = await redis_server_time(r) + datetime.timedelta(minutes=1)
        await r.set('a', 'foo')
        assert await r.expireat('a', expire_at)
        assert 0 < await r.ttl('a') <= 61

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_expireat_no_key(self, r):
        await r.flushdb()
        expire_at = await redis_server_time(r) + datetime.timedelta(minutes=1)
        assert not await r.expireat('a', expire_at)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_expireat_unixtime(self, r):
        await r.flushdb()
        expire_at = await redis_server_time(r) + datetime.timedelta(minutes=1)
        await r.set('a', 'foo')
        expire_at_seconds = int(time.mktime(expire_at.timetuple()))
        assert await r.expireat('a', expire_at_seconds)
        assert 0 < await r.ttl('a') <= 61

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_get_and_set(self, r):
        await r.flushdb()
        # get and set can't be tested independently of each other
        assert await r.get('a') is None
        byte_string = b('value')
        integer = 5
        unicode_string = chr(33) + 'abcd' + chr(22)
        assert await r.set('byte_string', byte_string)
        assert await r.set('integer', 5)
        assert await r.set('unicode_string', unicode_string)
        assert await r.get('byte_string') == byte_string
        assert await r.get('integer') == b(str(integer))
        assert (await r.get('unicode_string')).decode('utf-8') == unicode_string

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_get_set_bit(self, r):
        await r.flushdb()
        # no value
        assert not await r.getbit('a', 5)
        # set bit 5
        assert not await r.setbit('a', 5, True)
        assert await r.getbit('a', 5)
        # unset bit 4
        assert not await r.setbit('a', 4, False)
        assert not await r.getbit('a', 4)
        # set bit 4
        assert not await r.setbit('a', 4, True)
        assert await r.getbit('a', 4)
        # set bit 5 again
        assert await r.setbit('a', 5, True)
        assert await r.getbit('a', 5)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_getrange(self, r):
        await r.flushdb()
        await r.set('a', 'foo')
        assert await r.getrange('a', 0, 0) == b('f')
        assert await r.getrange('a', 0, 2) == b('foo')
        assert await r.getrange('a', 3, 4) == b('')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_getset(self, r):
        await r.flushdb()
        assert await r.getset('a', 'foo') is None
        assert await r.getset('a', 'bar') == b('foo')
        assert await r.get('a') == b('bar')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_incr(self, r):
        await r.flushdb()
        assert await r.incr('a') == 1
        assert await r.get('a') == b('1')
        assert await r.incr('a') == 2
        assert await r.get('a') == b('2')
        assert await r.incr('a', amount=5) == 7
        assert await r.get('a') == b('7')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_incrby(self, r):
        await r.flushdb()
        assert await r.incrby('a') == 1
        assert await r.incrby('a', 4) == 5
        assert await r.get('a') == b('5')

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_incrbyfloat(self, r):
        await r.flushdb()
        assert await r.incrbyfloat('a') == 1.0
        assert await r.get('a') == b('1')
        assert await r.incrbyfloat('a', 1.1) == 2.1
        assert float(await r.get('a')) == float(2.1)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_keys(self, r):
        await r.flushdb()
        assert await r.keys() == []
        keys_with_underscores = {b('test_a'), b('test_b')}
        keys = keys_with_underscores.union({b('testc')})
        for key in keys:
            await r.set(key, 1)
        assert set(await r.keys(pattern='test_*')) == keys_with_underscores
        assert set(await r.keys(pattern='test*')) == keys

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_mget(self, r):
        await r.flushdb()
        assert await r.mget(['a', 'b']) == [None, None]
        await r.set('a', '1')
        await r.set('b', '2')
        await r.set('c', '3')
        assert await r.mget('a', 'other', 'b', 'c') == [b('1'), None, b('2'), b('3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_mset(self, r):
        d = {'a': b('1'), 'b': b('2'), 'c': b('3')}
        assert await r.mset(d)
        for k, v in iteritems(d):
            assert await r.get(k) == v

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_mset_kwargs(self, r):
        d = {'a': b('1'), 'b': b('2'), 'c': b('3')}
        assert await r.mset(**d)
        for k, v in iteritems(d):
            assert await r.get(k) == v

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_msetnx(self, r):
        await r.flushdb()
        d = {'a': b('1'), 'b': b('2'), 'c': b('3')}
        assert await r.msetnx(d)
        d2 = {'a': b('x'), 'd': b('4')}
        assert not await r.msetnx(d2)
        for k, v in iteritems(d):
            assert await r.get(k) == v
        assert await r.get('d') is None

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_msetnx_kwargs(self, r):
        await r.flushdb()
        d = {'a': b('1'), 'b': b('2'), 'c': b('3')}
        assert await r.msetnx(**d)
        d2 = {'a': b('x'), 'd': b('4')}
        assert not await r.msetnx(**d2)
        for k, v in iteritems(d):
            assert await r.get(k) == v
        assert await r.get('d') is None

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pexpire(self, r):
        await r.flushdb()
        assert not await r.pexpire('a', 60000)
        await r.set('a', 'foo')
        assert await r.pexpire('a', 60000)
        assert 0 < await r.pttl('a') <= 60000
        assert await r.persist('a')
        assert await r.pttl('a') < 0

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pexpireat_datetime(self, r):
        expire_at = await redis_server_time(r) + datetime.timedelta(minutes=1)
        await r.set('a', 'foo')
        assert await r.pexpireat('a', expire_at)
        assert 0 < await r.pttl('a') <= 61000

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pexpireat_no_key(self, r):
        await r.flushdb()
        expire_at = await redis_server_time(r) + datetime.timedelta(minutes=1)
        assert not await r.pexpireat('a', expire_at)

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pexpireat_unixtime(self, r):
        await r.flushdb()
        expire_at = await redis_server_time(r) + datetime.timedelta(minutes=1)
        await r.set('a', 'foo')
        expire_at_seconds = int(time.mktime(expire_at.timetuple())) * 1000
        assert await r.pexpireat('a', expire_at_seconds)
        assert 0 < await r.pttl('a') <= 61000

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_psetex(self, r):
        await r.flushdb()
        assert await r.psetex('a', 1000, 'value')
        assert await r.get('a') == b('value')
        assert 0 < await r.pttl('a') <= 1000

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_psetex_timedelta(self, r):
        await r.flushdb()
        expire_at = datetime.timedelta(milliseconds=1000)
        assert await r.psetex('a', expire_at, 'value')
        assert await r.get('a') == b('value')
        assert 0 < await r.pttl('a') <= 1000

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_randomkey(self, r):
        await r.flushdb()
        assert await r.randomkey() is None
        for key in ('a', 'b', 'c'):
            await r.set(key, 1)
        assert await r.randomkey() in (b('a'), b('b'), b('c'))

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_rename(self, r):
        await r.flushdb()
        await r.set('a', 1)
        assert await r.rename('a', 'b')
        assert await r.get('a') is None
        assert await r.get('b') == b('1')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_renamenx(self, r):
        await r.flushdb()
        await r.set('a', 1)
        await r.set('b', 2)
        assert not await r.renamenx('a', 'b')
        assert await r.get('a') == b('1')
        assert await r.get('b') == b('2')

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set_nx(self, r):
        await r.flushdb()
        assert await r.set('a', '1', nx=True)
        assert not await r.set('a', '2', nx=True)
        assert await r.get('a') == b('1')

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set_xx(self, r):
        await r.flushdb()
        assert not await r.set('a', '1', xx=True)
        assert await r.get('a') is None
        await r.set('a', 'bar')
        assert await r.set('a', '2', xx=True)
        assert await r.get('a') == b('2')

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set_px(self, r):
        await r.flushdb()
        assert await r.set('a', '1', px=10000)
        assert await r.get('a') == b('1')
        assert 0 < await r.pttl('a') <= 10000
        assert 0 < await r.ttl('a') <= 10

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set_px_timedelta(self, r):
        await r.flushdb()
        expire_at = datetime.timedelta(milliseconds=1000)
        assert await r.set('a', '1', px=expire_at)
        assert 0 < await r.pttl('a') <= 1000
        assert 0 < await r.ttl('a') <= 1

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set_ex(self, r):
        await r.flushdb()
        assert await r.set('a', '1', ex=10)
        assert 0 < await r.ttl('a') <= 10

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set_ex_timedelta(self, r):
        await r.flushdb()
        expire_at = datetime.timedelta(seconds=60)
        assert await r.set('a', '1', ex=expire_at)
        assert 0 < await r.ttl('a') <= 60

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_set_multipleoptions(self, r):
        await r.flushdb()
        await r.set('a', 'val')
        assert await r.set('a', '1', xx=True, px=10000)
        assert 0 < await r.ttl('a') <= 10

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_setex(self, r):
        await r.flushdb()
        assert await r.setex('a', 60, '1')
        assert await r.get('a') == b('1')
        assert 0 < await r.ttl('a') <= 60

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_setnx(self, r):
        await r.flushdb()
        assert await r.setnx('a', '1')
        assert await r.get('a') == b('1')
        assert not await r.setnx('a', '2')
        assert await r.get('a') == b('1')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_setrange(self, r):
        await r.flushdb()
        assert await r.setrange('a', 5, 'foo') == 8
        assert await r.get('a') == b('\0\0\0\0\0foo')
        await r.set('a', 'abcdefghijh')
        assert await r.setrange('a', 6, '12345') == 11
        assert await r.get('a') == b('abcdef12345')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_strlen(self, r):
        await r.flushdb()
        await r.set('a', 'foo')
        assert await r.strlen('a') == 3

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_substr(self, r):
        await r.flushdb()
        await r.set('a', '0123456789')
        assert await r.substr('a', 0) == b('0123456789')
        assert await r.substr('a', 2) == b('23456789')
        assert await r.substr('a', 3, 5) == b('345')
        assert await r.substr('a', 3, -2) == b('345678')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_type(self, r):
        await r.flushdb()
        assert await r.type('a') == b('none')
        await r.set('a', '1')
        assert await r.type('a') == b('string')
        await r.delete('a')
        await r.lpush('a', '1')
        assert await r.type('a') == b('list')
        await r.delete('a')
        await r.sadd('a', '1')
        assert await r.type('a') == b('set')
        await r.delete('a')
        await r.zadd('a', **{'1': 1})
        assert await r.type('a') == b('zset')

    @skip_if_server_version_lt('3.2.1')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_touch(self, r):
        await r.flushdb()
        keys = ['a', 'b', 'c', 'd']
        for index, key in enumerate(keys):
            await r.set(key, index)
        assert await r.touch(keys) == len(keys)

    @skip_if_server_version_lt('4.0.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_unlink(self, r):
        await r.flushdb()
        keys = ['a', 'b', 'c', 'd']
        for index, key in enumerate(keys):
            await r.set(key, index)
        await r.unlink(keys)
        for key in keys:
            assert r.get(key) is None

    # LIST COMMANDS
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_blpop(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '2')
        await r.rpush('b', '3', '4')
        assert await r.blpop(['b', 'a'], timeout=1) == (b('b'), b('3'))
        assert await r.blpop(['b', 'a'], timeout=1) == (b('b'), b('4'))
        assert await r.blpop(['b', 'a'], timeout=1) == (b('a'), b('1'))
        assert await r.blpop(['b', 'a'], timeout=1) == (b('a'), b('2'))
        assert await r.blpop(['b', 'a'], timeout=1) is None
        await r.rpush('c', '1')
        assert await r.blpop('c', timeout=1) == (b('c'), b('1'))

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_brpop(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '2')
        await r.rpush('b', '3', '4')
        assert await r.brpop(['b', 'a'], timeout=1) == (b('b'), b('4'))
        assert await r.brpop(['b', 'a'], timeout=1) == (b('b'), b('3'))
        assert await r.brpop(['b', 'a'], timeout=1) == (b('a'), b('2'))
        assert await r.brpop(['b', 'a'], timeout=1) == (b('a'), b('1'))
        assert await r.brpop(['b', 'a'], timeout=1) is None
        await r.rpush('c', '1')
        assert await r.brpop('c', timeout=1) == (b('c'), b('1'))

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_brpoplpush(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '2')
        await r.rpush('b', '3', '4')
        assert await r.brpoplpush('a', 'b') == b('2')
        assert await r.brpoplpush('a', 'b') == b('1')
        assert await r.brpoplpush('a', 'b', timeout=1) is None
        assert await r.lrange('a', 0, -1) == []
        assert await r.lrange('b', 0, -1) == [b('1'), b('2'), b('3'), b('4')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_brpoplpush_empty_string(self, r):
        await r.flushdb()
        await r.rpush('a', '')
        assert await r.brpoplpush('a', 'b') == b('')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_lindex(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '2', '3')
        assert await r.lindex('a', '0') == b('1')
        assert await r.lindex('a', '1') == b('2')
        assert await r.lindex('a', '2') == b('3')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_linsert(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '2', '3')
        assert await r.linsert('a', 'after', '2', '2.5') == 4
        assert await r.lrange('a', 0, -1) == [b('1'), b('2'), b('2.5'), b('3')]
        assert await r.linsert('a', 'before', '2', '1.5') == 5
        assert await r.lrange('a', 0, -1) == \
            [b('1'), b('1.5'), b('2'), b('2.5'), b('3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_llen(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '2', '3')
        assert await r.llen('a') == 3

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_lpop(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '2', '3')
        assert await r.lpop('a') == b('1')
        assert await r.lpop('a') == b('2')
        assert await r.lpop('a') == b('3')
        assert await r.lpop('a') is None

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_lpush(self, r):
        await r.flushdb()
        assert await r.lpush('a', '1') == 1
        assert await r.lpush('a', '2') == 2
        assert await r.lpush('a', '3', '4') == 4
        assert await r.lrange('a', 0, -1) == [b('4'), b('3'), b('2'), b('1')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_lpushx(self, r):
        await r.flushdb()
        assert await r.lpushx('a', '1') == 0
        assert await r.lrange('a', 0, -1) == []
        await r.rpush('a', '1', '2', '3')
        assert await r.lpushx('a', '4') == 4
        assert await r.lrange('a', 0, -1) == [b('4'), b('1'), b('2'), b('3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_lrange(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '2', '3', '4', '5')
        assert await r.lrange('a', 0, 2) == [b('1'), b('2'), b('3')]
        assert await r.lrange('a', 2, 10) == [b('3'), b('4'), b('5')]
        assert await r.lrange('a', 0, -1) == [b('1'), b('2'), b('3'), b('4'), b('5')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_lrem(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '1', '1', '1')
        assert await r.lrem('a', 1, '1') == 1
        assert await r.lrange('a', 0, -1) == [b('1'), b('1'), b('1')]
        assert await r.lrem('a', 3, '1') == 3
        assert await r.lrange('a', 0, -1) == []

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_lset(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '2', '3')
        assert await r.lrange('a', 0, -1) == [b('1'), b('2'), b('3')]
        assert await r.lset('a', 1, '4')
        assert await r.lrange('a', 0, 2) == [b('1'), b('4'), b('3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_ltrim(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '2', '3')
        assert await r.ltrim('a', 0, 1)
        assert await r.lrange('a', 0, -1) == [b('1'), b('2')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_rpop(self, r):
        await r.flushdb()
        await r.rpush('a', '1', '2', '3')
        assert await r.rpop('a') == b('3')
        assert await r.rpop('a') == b('2')
        assert await r.rpop('a') == b('1')
        assert await r.rpop('a') is None

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_rpoplpush(self, r):
        await r.flushdb()
        await r.rpush('a', 'a1', 'a2', 'a3')
        await r.rpush('b', 'b1', 'b2', 'b3')
        assert await r.rpoplpush('a', 'b') == b('a3')
        assert await r.lrange('a', 0, -1) == [b('a1'), b('a2')]
        assert await r.lrange('b', 0, -1) == [b('a3'), b('b1'), b('b2'), b('b3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_rpush(self, r):
        await r.flushdb()
        assert await r.rpush('a', '1') == 1
        assert await r.rpush('a', '2') == 2
        assert await r.rpush('a', '3', '4') == 4
        assert await r.lrange('a', 0, -1) == [b('1'), b('2'), b('3'), b('4')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_rpushx(self, r):
        await r.flushdb()
        assert await r.rpushx('a', 'b') == 0
        assert await r.lrange('a', 0, -1) == []
        await r.rpush('a', '1', '2', '3')
        assert await r.rpushx('a', '4') == 4
        assert await r.lrange('a', 0, -1) == [b('1'), b('2'), b('3'), b('4')]

    # SCAN COMMANDS
    @skip_if_server_version_lt('2.8.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_scan(self, r):
        await r.flushdb()
        await r.set('a', 1)
        await r.set('b', 2)
        await r.set('c', 3)
        cursor, keys = await r.scan()
        assert cursor == 0
        assert set(keys) == set([b('a'), b('b'), b('c')])
        _, keys = await r.scan(match='a')
        assert set(keys) == set([b('a')])

    @skip_if_server_version_lt('2.8.0')
    @skip_python_vsersion_lt('3.6')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_scan_iter(self, r):
        await r.flushdb()
        await r.set('a', 1)
        await r.set('b', 2)
        await r.set('c', 3)
        keys = set()
        async for key in r.scan_iter():
            keys.add(key)
        assert keys == set([b('a'), b('b'), b('c')])
        async for key in r.scan_iter(match='a'):
            assert key == b('a')

    @skip_if_server_version_lt('2.8.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sscan(self, r):
        await r.flushdb()
        await r.sadd('a', 1, 2, 3)
        cursor, members = await r.sscan('a')
        assert cursor == 0
        assert set(members) == set([b('1'), b('2'), b('3')])
        _, members = await r.sscan('a', match=b('1'))
        assert set(members) == set([b('1')])

    @skip_if_server_version_lt('2.8.0')
    @skip_python_vsersion_lt('3.6')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sscan_iter(self, r):
        await r.flushdb()
        await r.sadd('a', 1, 2, 3)
        members = set()
        async for member in r.sscan_iter('a'):
            members.add(member)
        assert members == set([b('1'), b('2'), b('3')])
        async for member in r.sscan_iter('a', match=b('1')):
            assert member == b('1')

    @skip_if_server_version_lt('2.8.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hscan(self, r):
        await r.flushdb()
        await r.hmset('a', {'a': 1, 'b': 2, 'c': 3})
        cursor, dic = await r.hscan('a')
        assert cursor == 0
        assert dic == {b('a'): b('1'), b('b'): b('2'), b('c'): b('3')}
        _, dic = await r.hscan('a', match='a')
        assert dic == {b('a'): b('1')}

    @skip_if_server_version_lt('2.8.0')
    @skip_python_vsersion_lt('3.6')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hscan_iter(self, r):
        await r.flushdb()
        await r.hmset('a', {'a': 1, 'b': 2, 'c': 3})
        dic = dict()
        async for data in r.hscan_iter('a'):
            dic.update(dict([data]))
        assert dic == {b('a'): b('1'), b('b'): b('2'), b('c'): b('3')}
        async for data in r.hscan_iter('a', match='a'):
            assert dict([data]) == {b('a'): b('1')}

    @skip_if_server_version_lt('2.8.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zscan(self, r):
        await r.flushdb()
        await r.zadd('a', 1, 'a', 2, 'b', 3, 'c')
        cursor, pairs = await r.zscan('a')
        assert cursor == 0
        assert set(pairs) == set([(b('a'), 1), (b('b'), 2), (b('c'), 3)])
        _, pairs = await r.zscan('a', match='a')
        assert set(pairs) == set([(b('a'), 1)])

    @skip_if_server_version_lt('2.8.0')
    @skip_python_vsersion_lt('3.6')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zscan_iter(self, r):
        await r.zadd('a', 1, 'a', 2, 'b', 3, 'c')
        pairs = set()
        async for pair in r.zscan_iter('a'):
            pairs.add(pair)
        assert pairs == set([(b('a'), 1), (b('b'), 2), (b('c'), 3)])
        async for pair in r.zscan_iter('a', match='a'):
            assert pair == (b('a'), 1)

    # SET COMMANDS
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sadd(self, r):
        await r.flushdb()
        members = set([b('1'), b('2'), b('3')])
        await r.sadd('a', *members)
        assert await r.smembers('a') == members

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_scard(self, r):
        await r.flushdb()
        await r.sadd('a', '1', '2', '3')
        assert await r.scard('a') == 3

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sdiff(self, r):
        await r.flushdb()
        await r.sadd('a', '1', '2', '3')
        assert await r.sdiff('a', 'b') == set([b('1'), b('2'), b('3')])
        await r.sadd('b', '2', '3')
        assert await r.sdiff('a', 'b') == set([b('1')])

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sdiffstore(self, r):
        await r.flushdb()
        await r.sadd('a', '1', '2', '3')
        assert await r.sdiffstore('c', 'a', 'b') == 3
        assert await r.smembers('c') == set([b('1'), b('2'), b('3')])
        await r.sadd('b', '2', '3')
        assert await r.sdiffstore('c', 'a', 'b') == 1
        assert await r.smembers('c') == set([b('1')])

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sinter(self, r):
        await r.flushdb()
        await r.sadd('a', '1', '2', '3')
        assert await r.sinter('a', 'b') == set()
        await r.sadd('b', '2', '3')
        assert await r.sinter('a', 'b') == set([b('2'), b('3')])

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sinterstore(self, r):
        await r.flushdb()
        await r.sadd('a', '1', '2', '3')
        assert await r.sinterstore('c', 'a', 'b') == 0
        assert await r.smembers('c') == set()
        await r.sadd('b', '2', '3')
        assert await r.sinterstore('c', 'a', 'b') == 2
        assert await r.smembers('c') == set([b('2'), b('3')])

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sismember(self, r):
        await r.flushdb()
        await r.sadd('a', '1', '2', '3')
        assert await r.sismember('a', '1')
        assert await r.sismember('a', '2')
        assert await r.sismember('a', '3')
        assert not await r.sismember('a', '4')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_smembers(self, r):
        await r.flushdb()
        await r.sadd('a', '1', '2', '3')
        assert await r.smembers('a') == set([b('1'), b('2'), b('3')])

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_smove(self, r):
        await r.flushdb()
        await r.sadd('a', 'a1', 'a2')
        await r.sadd('b', 'b1', 'b2')
        assert await r.smove('a', 'b', 'a1')
        assert await r.smembers('a') == set([b('a2')])
        assert await r.smembers('b') == set([b('b1'), b('b2'), b('a1')])

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_spop(self, r):
        await r.flushdb()
        s = [b('1'), b('2'), b('3')]
        await r.sadd('a', *s)
        value = await r.spop('a')
        assert value in s
        assert await r.smembers('a') == set(s) - set([value])

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_srandmember(self, r):
        await r.flushdb()
        s = [b('1'), b('2'), b('3')]
        await r.sadd('a', *s)
        assert await r.srandmember('a') in s

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_srandmember_multi_value(self, r):
        await r.flushdb()
        s = [b('1'), b('2'), b('3')]
        await r.sadd('a', *s)
        randoms = await r.srandmember('a', number=2)
        assert len(randoms) == 2
        assert set(randoms).intersection(s) == set(randoms)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_srem(self, r):
        await r.flushdb()
        await r.sadd('a', '1', '2', '3', '4')
        assert await r.srem('a', '5') == 0
        assert await r.srem('a', '2', '4') == 2
        assert await r.smembers('a') == set([b('1'), b('3')])

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sunion(self, r):
        await r.flushdb()
        await r.sadd('a', '1', '2')
        await r.sadd('b', '2', '3')
        assert await r.sunion('a', 'b') == set([b('1'), b('2'), b('3')])

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sunionstore(self, r):
        await r.flushdb()
        await r.sadd('a', '1', '2')
        await r.sadd('b', '2', '3')
        assert await r.sunionstore('c', 'a', 'b') == 3
        assert await r.smembers('c') == set([b('1'), b('2'), b('3')])

    # SORTED SET COMMANDS
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zadd(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3)
        assert await r.zrange('a', 0, -1) == [b('a1'), b('a2'), b('a3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zcard(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3)
        assert await r.zcard('a') == 3

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zcount(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3)
        assert await r.zcount('a', '-inf', '+inf') == 3
        assert await r.zcount('a', 1, 2) == 2
        assert await r.zcount('a', 10, 20) == 0

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zincrby(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3)
        assert await r.zincrby('a', 'a2') == 3.0
        assert await r.zincrby('a', 'a3', amount=5) == 8.0
        assert await r.zscore('a', 'a2') == 3.0
        assert await r.zscore('a', 'a3') == 8.0

    @skip_if_server_version_lt('2.8.9')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zlexcount(self, r):
        await r.flushdb()
        await r.zadd('a', a=0, b=0, c=0, d=0, e=0, f=0, g=0)
        assert await r.zlexcount('a', '-', '+') == 7
        assert await r.zlexcount('a', '[b', '[f') == 5

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zinterstore_sum(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=1, a3=1)
        await r.zadd('b', a1=2, a2=2, a3=2)
        await r.zadd('c', a1=6, a3=5, a4=4)
        assert await r.zinterstore('d', ['a', 'b', 'c']) == 2
        assert await r.zrange('d', 0, -1, withscores=True) == \
            [(b('a3'), 8), (b('a1'), 9)]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zinterstore_max(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=1, a3=1)
        await r.zadd('b', a1=2, a2=2, a3=2)
        await r.zadd('c', a1=6, a3=5, a4=4)
        assert await r.zinterstore('d', ['a', 'b', 'c'], aggregate='MAX') == 2
        assert await r.zrange('d', 0, -1, withscores=True) == \
            [(b('a3'), 5), (b('a1'), 6)]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zinterstore_min(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3)
        await r.zadd('b', a1=2, a2=3, a3=5)
        await r.zadd('c', a1=6, a3=5, a4=4)
        assert await r.zinterstore('d', ['a', 'b', 'c'], aggregate='MIN') == 2
        assert await r.zrange('d', 0, -1, withscores=True) == \
            [(b('a1'), 1), (b('a3'), 3)]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zinterstore_with_weight(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=1, a3=1)
        await r.zadd('b', a1=2, a2=2, a3=2)
        await r.zadd('c', a1=6, a3=5, a4=4)
        assert await r.zinterstore('d', {'a': 1, 'b': 2, 'c': 3}) == 2
        assert await r.zrange('d', 0, -1, withscores=True) == \
            [(b('a3'), 20), (b('a1'), 23)]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zrange(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3)
        assert await r.zrange('a', 0, 1) == [b('a1'), b('a2')]
        assert await r.zrange('a', 1, 2) == [b('a2'), b('a3')]

        # withscores
        assert await r.zrange('a', 0, 1, withscores=True) == \
            [(b('a1'), 1.0), (b('a2'), 2.0)]
        assert await r.zrange('a', 1, 2, withscores=True) == \
            [(b('a2'), 2.0), (b('a3'), 3.0)]

        # custom score function
        assert await r.zrange('a', 0, 1, withscores=True, score_cast_func=int) == \
            [(b('a1'), 1), (b('a2'), 2)]

    @skip_if_server_version_lt('2.8.9')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zrangebylex(self, r):
        await r.flushdb()
        await r.zadd('a', a=0, b=0, c=0, d=0, e=0, f=0, g=0)
        assert await r.zrangebylex('a', '-', '[c') == [b('a'), b('b'), b('c')]
        assert await r.zrangebylex('a', '-', '(c') == [b('a'), b('b')]
        assert await r.zrangebylex('a', '[aaa', '(g') == \
            [b('b'), b('c'), b('d'), b('e'), b('f')]
        assert await r.zrangebylex('a', '[f', '+') == [b('f'), b('g')]
        assert await r.zrangebylex('a', '-', '+', start=3, num=2) == [b('d'), b('e')]

    @skip_if_server_version_lt('2.9.9')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zrevrangebylex(self, r):
        await r.flushdb()
        await r.zadd('a', a=0, b=0, c=0, d=0, e=0, f=0, g=0)
        assert await r.zrevrangebylex('a', '[c', '-') == [b('c'), b('b'), b('a')]
        assert await r.zrevrangebylex('a', '(c', '-') == [b('b'), b('a')]
        assert await r.zrevrangebylex('a', '(g', '[aaa') == \
            [b('f'), b('e'), b('d'), b('c'), b('b')]
        assert await r.zrevrangebylex('a', '+', '[f') == [b('g'), b('f')]
        assert await r.zrevrangebylex('a', '+', '-', start=3, num=2) == \
            [b('d'), b('c')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zrangebyscore(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3, a4=4, a5=5)
        assert await r.zrangebyscore('a', 2, 4) == [b('a2'), b('a3'), b('a4')]

        # slicing with start/num
        assert await r.zrangebyscore('a', 2, 4, start=1, num=2) == \
            [b('a3'), b('a4')]

        # withscores
        assert await r.zrangebyscore('a', 2, 4, withscores=True) == \
            [(b('a2'), 2.0), (b('a3'), 3.0), (b('a4'), 4.0)]

        # custom score function
        assert await r.zrangebyscore('a', 2, 4, withscores=True,
                               score_cast_func=int) == \
            [(b('a2'), 2), (b('a3'), 3), (b('a4'), 4)]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zrank(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3, a4=4, a5=5)
        assert await r.zrank('a', 'a1') == 0
        assert await r.zrank('a', 'a2') == 1
        assert await r.zrank('a', 'a6') is None

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zrem(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3)
        assert await r.zrem('a', 'a2') == 1
        assert await r.zrange('a', 0, -1) == [b('a1'), b('a3')]
        assert await r.zrem('a', 'b') == 0
        assert await r.zrange('a', 0, -1) == [b('a1'), b('a3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zrem_multiple_keys(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3)
        assert await r.zrem('a', 'a1', 'a2') == 2
        assert await r.zrange('a', 0, 5) == [b('a3')]

    @skip_if_server_version_lt('2.8.9')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zremrangebylex(self, r):
        await r.flushdb()
        await r.zadd('a', a=0, b=0, c=0, d=0, e=0, f=0, g=0)
        assert await r.zremrangebylex('a', '-', '[c') == 3
        assert await r.zrange('a', 0, -1) == [b('d'), b('e'), b('f'), b('g')]
        assert await r.zremrangebylex('a', '[f', '+') == 2
        assert await r.zrange('a', 0, -1) == [b('d'), b('e')]
        assert await r.zremrangebylex('a', '[h', '+') == 0
        assert await r.zrange('a', 0, -1) == [b('d'), b('e')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zremrangebyrank(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3, a4=4, a5=5)
        assert await r.zremrangebyrank('a', 1, 3) == 3
        assert await r.zrange('a', 0, 5) == [b('a1'), b('a5')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zremrangebyscore(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3, a4=4, a5=5)
        assert await r.zremrangebyscore('a', 2, 4) == 3
        assert await r.zrange('a', 0, -1) == [b('a1'), b('a5')]
        assert await r.zremrangebyscore('a', 2, 4) == 0
        assert await r.zrange('a', 0, -1) == [b('a1'), b('a5')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zrevrange(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3)
        assert await r.zrevrange('a', 0, 1) == [b('a3'), b('a2')]
        assert await r.zrevrange('a', 1, 2) == [b('a2'), b('a1')]

        # withscores
        assert await r.zrevrange('a', 0, 1, withscores=True) == \
            [(b('a3'), 3.0), (b('a2'), 2.0)]
        assert await r.zrevrange('a', 1, 2, withscores=True) == \
            [(b('a2'), 2.0), (b('a1'), 1.0)]

        # custom score function
        assert await r.zrevrange('a', 0, 1, withscores=True,
                           score_cast_func=int) == \
            [(b('a3'), 3.0), (b('a2'), 2.0)]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zrevrangebyscore(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3, a4=4, a5=5)
        assert await r.zrevrangebyscore('a', 4, 2) == [b('a4'), b('a3'), b('a2')]

        # slicing with start/num
        assert await r.zrevrangebyscore('a', 4, 2, start=1, num=2) == \
            [b('a3'), b('a2')]

        # withscores
        assert await r.zrevrangebyscore('a', 4, 2, withscores=True) == \
            [(b('a4'), 4.0), (b('a3'), 3.0), (b('a2'), 2.0)]

        # custom score function
        assert await r.zrevrangebyscore('a', 4, 2, withscores=True,
                                  score_cast_func=int) == \
            [(b('a4'), 4), (b('a3'), 3), (b('a2'), 2)]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zrevrank(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3, a4=4, a5=5)
        assert await r.zrevrank('a', 'a1') == 4
        assert await r.zrevrank('a', 'a2') == 3
        assert await r.zrevrank('a', 'a6') is None

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zscore(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3)
        assert await r.zscore('a', 'a1') == 1.0
        assert await r.zscore('a', 'a2') == 2.0
        assert await r.zscore('a', 'a4') is None

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zunionstore_sum(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=1, a3=1)
        await r.zadd('b', a1=2, a2=2, a3=2)
        await r.zadd('c', a1=6, a3=5, a4=4)
        assert await r.zunionstore('d', ['a', 'b', 'c']) == 4
        assert await r.zrange('d', 0, -1, withscores=True) == \
            [(b('a2'), 3), (b('a4'), 4), (b('a3'), 8), (b('a1'), 9)]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zunionstore_max(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=1, a3=1)
        await r.zadd('b', a1=2, a2=2, a3=2)
        await r.zadd('c', a1=6, a3=5, a4=4)
        assert await r.zunionstore('d', ['a', 'b', 'c'], aggregate='MAX') == 4
        assert await r.zrange('d', 0, -1, withscores=True) == \
            [(b('a2'), 2), (b('a4'), 4), (b('a3'), 5), (b('a1'), 6)]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zunionstore_min(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=2, a3=3)
        await r.zadd('b', a1=2, a2=2, a3=4)
        await r.zadd('c', a1=6, a3=5, a4=4)
        assert await r.zunionstore('d', ['a', 'b', 'c'], aggregate='MIN') == 4
        assert await r.zrange('d', 0, -1, withscores=True) == \
            [(b('a1'), 1), (b('a2'), 2), (b('a3'), 3), (b('a4'), 4)]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_zunionstore_with_weight(self, r):
        await r.flushdb()
        await r.zadd('a', a1=1, a2=1, a3=1)
        await r.zadd('b', a1=2, a2=2, a3=2)
        await r.zadd('c', a1=6, a3=5, a4=4)
        assert await r.zunionstore('d', {'a': 1, 'b': 2, 'c': 3}) == 4
        assert await r.zrange('d', 0, -1, withscores=True) == \
            [(b('a2'), 5), (b('a4'), 12), (b('a3'), 20), (b('a1'), 23)]

    # HYPERLOGLOG TESTS
    @skip_if_server_version_lt('2.8.9')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pfadd(self, r):
        await r.flushdb()
        members = set([b('1'), b('2'), b('3')])
        assert await r.pfadd('a', *members) == 1
        assert await r.pfadd('a', *members) == 0
        assert await r.pfcount('a') == len(members)

    @skip_if_server_version_lt('2.8.9')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pfcount(self, r):
        await r.flushdb()
        members = set([b('1'), b('2'), b('3')])
        await r.pfadd('a', *members)
        assert await r.pfcount('a') == len(members)
        members_b = set([b('2'), b('3'), b('4')])
        await r.pfadd('b', *members_b)
        assert await r.pfcount('b') == len(members_b)
        assert await r.pfcount('a', 'b') == len(members_b.union(members))

    @skip_if_server_version_lt('2.8.9')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pfmerge(self, r):
        await r.flushdb()
        mema = set([b('1'), b('2'), b('3')])
        memb = set([b('2'), b('3'), b('4')])
        memc = set([b('5'), b('6'), b('7')])
        await r.pfadd('a', *mema)
        await r.pfadd('b', *memb)
        await r.pfadd('c', *memc)
        await r.pfmerge('d', 'c', 'a')
        assert await r.pfcount('d') == 6
        await r.pfmerge('d', 'b')
        assert await r.pfcount('d') == 7

    # HASH COMMANDS
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hget_and_hset(self, r):
        await r.flushdb()
        await r.hmset('a', {'1': 1, '2': 2, '3': 3})
        assert await r.hget('a', '1') == b('1')
        assert await r.hget('a', '2') == b('2')
        assert await r.hget('a', '3') == b('3')

        # field was updated, redis returns 0
        assert await r.hset('a', '2', 5) == 0
        assert await r.hget('a', '2') == b('5')

        # field is new, redis returns 1
        assert await r.hset('a', '4', 4) == 1
        assert await r.hget('a', '4') == b('4')

        # key inside of hash that doesn't exist returns null value
        assert await r.hget('a', 'b') is None

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hdel(self, r):
        await r.flushdb()
        await r.hmset('a', {'1': 1, '2': 2, '3': 3})
        assert await r.hdel('a', '2') == 1
        assert await r.hget('a', '2') is None
        assert await r.hdel('a', '1', '3') == 2
        assert await r.hlen('a') == 0

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hexists(self, r):
        await r.flushdb()
        await r.hmset('a', {'1': 1, '2': 2, '3': 3})
        assert await r.hexists('a', '1')
        assert not await r.hexists('a', '4')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hgetall(self, r):
        await r.flushdb()
        h = {b('a1'): b('1'), b('a2'): b('2'), b('a3'): b('3')}
        await r.hmset('a', h)
        assert await r.hgetall('a') == h

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hincrby(self, r):
        await r.flushdb()
        assert await r.hincrby('a', '1') == 1
        assert await r.hincrby('a', '1', amount=2) == 3
        assert await r.hincrby('a', '1', amount=-2) == 1

    @skip_if_server_version_lt('2.6.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hincrbyfloat(self, r):
        await r.flushdb()
        assert await r.hincrbyfloat('a', '1') == 1.0
        assert await r.hincrbyfloat('a', '1') == 2.0
        assert await r.hincrbyfloat('a', '1', 1.2) == 3.2

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hkeys(self, r):
        await r.flushdb()
        h = {b('a1'): b('1'), b('a2'): b('2'), b('a3'): b('3')}
        await r.hmset('a', h)
        local_keys = list(iterkeys(h))
        remote_keys = await r.hkeys('a')
        assert (sorted(local_keys) == sorted(remote_keys))

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hlen(self, r):
        await r.flushdb()
        await r.hmset('a', {'1': 1, '2': 2, '3': 3})
        assert await r.hlen('a') == 3

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hmget(self, r):
        await r.flushdb()
        assert await r.hmset('a', {'a': 1, 'b': 2, 'c': 3})
        assert await r.hmget('a', 'a', 'b', 'c') == [b('1'), b('2'), b('3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hmset(self, r):
        await r.flushdb()
        h = {b('a'): b('1'), b('b'): b('2'), b('c'): b('3')}
        assert await r.hmset('a', h)
        assert await r.hgetall('a') == h

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hsetnx(self, r):
        await r.flushdb()
        # Initially set the hash field
        assert await r.hsetnx('a', '1', 1)
        assert await r.hget('a', '1') == b('1')
        assert not await r.hsetnx('a', '1', 2)
        assert await r.hget('a', '1') == b('1')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hvals(self, r):
        await r.flushdb()
        h = {b('a1'): b('1'), b('a2'): b('2'), b('a3'): b('3')}
        await r.hmset('a', h)
        local_vals = list(itervalues(h))
        remote_vals = await r.hvals('a')
        assert sorted(local_vals) == sorted(remote_vals)

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_hstrlen(self, r):
        await r.flushdb()
        key = 'myhash'
        myhash = {'f1': 'HelloWorld', 'f2': 99, 'f3': -256}
        await r.hmset(key, myhash)
        assert await r.hstrlen('key_not_exist', 'f1') == 0
        assert await r.hstrlen(key, 'f4') == 0
        assert await r.hstrlen(key, 'f1') == 10
        assert await r.hstrlen(key, 'f2') == 2
        assert await r.hstrlen(key, 'f3') == 4

    # SORT
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_basic(self, r):
        await r.flushdb()
        await r.rpush('a', '3', '2', '1', '4')
        assert await r.sort('a') == [b('1'), b('2'), b('3'), b('4')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_limited(self, r):
        await r.flushdb()
        await r.rpush('a', '3', '2', '1', '4')
        assert await r.sort('a', start=1, num=2) == [b('2'), b('3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_by(self, r):
        await r.flushdb()
        await r.set('score:1', 8)
        await r.set('score:2', 3)
        await r.set('score:3', 5)
        await r.rpush('a', '3', '2', '1')
        assert await r.sort('a', by='score:*') == [b('2'), b('3'), b('1')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_get(self, r):
        await r.flushdb()
        await r.set('user:1', 'u1')
        await r.set('user:2', 'u2')
        await r.set('user:3', 'u3')
        await r.rpush('a', '2', '3', '1')
        assert await r.sort('a', get='user:*') == [b('u1'), b('u2'), b('u3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_get_multi(self, r):
        await r.flushdb()
        await r.set('user:1', 'u1')
        await r.set('user:2', 'u2')
        await r.set('user:3', 'u3')
        await r.rpush('a', '2', '3', '1')
        assert await r.sort('a', get=('user:*', '#')) == \
            [b('u1'), b('1'), b('u2'), b('2'), b('u3'), b('3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_get_groups_two(self, r):
        await r.flushdb()
        await r.set('user:1', 'u1')
        await r.set('user:2', 'u2')
        await r.set('user:3', 'u3')
        await r.rpush('a', '2', '3', '1')
        assert await r.sort('a', get=('user:*', '#'), groups=True) == \
            [(b('u1'), b('1')), (b('u2'), b('2')), (b('u3'), b('3'))]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_groups_string_get(self, r):
        await r.flushdb()
        await r.set('user:1', 'u1')
        await r.set('user:2', 'u2')
        await r.set('user:3', 'u3')
        await r.rpush('a', '2', '3', '1')
        with pytest.raises(DataError):
            await r.sort('a', get='user:*', groups=True)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_groups_just_one_get(self, r):
        await r.flushdb()
        await r.set('user:1', 'u1')
        await r.set('user:2', 'u2')
        await r.set('user:3', 'u3')
        await r.rpush('a', '2', '3', '1')
        with pytest.raises(DataError):
            await r.sort('a', get=['user:*'], groups=True)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_groups_no_get(self, r):
        await r.flushdb()
        await r.set('user:1', 'u1')
        await r.set('user:2', 'u2')
        await r.set('user:3', 'u3')
        await r.rpush('a', '2', '3', '1')
        with pytest.raises(DataError):
            await r.sort('a', groups=True)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_groups_three_gets(self, r):
        await r.flushdb()
        await r.set('user:1', 'u1')
        await r.set('user:2', 'u2')
        await r.set('user:3', 'u3')
        await r.set('door:1', 'd1')
        await r.set('door:2', 'd2')
        await r.set('door:3', 'd3')
        await r.rpush('a', '2', '3', '1')
        assert await r.sort('a', get=('user:*', 'door:*', '#'), groups=True) == \
            [
                (b('u1'), b('d1'), b('1')),
                (b('u2'), b('d2'), b('2')),
                (b('u3'), b('d3'), b('3'))
        ]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_desc(self, r):
        await r.flushdb()
        await r.rpush('a', '2', '3', '1')
        assert await r.sort('a', desc=True) == [b('3'), b('2'), b('1')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_alpha(self, r):
        await r.flushdb()
        await r.rpush('a', 'e', 'c', 'b', 'd', 'a')
        assert await r.sort('a', alpha=True) == \
            [b('a'), b('b'), b('c'), b('d'), b('e')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_store(self, r):
        await r.flushdb()
        await r.rpush('a', '2', '3', '1')
        assert await r.sort('a', store='sorted_values') == 3
        assert await r.lrange('sorted_values', 0, -1) == [b('1'), b('2'), b('3')]

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_sort_all_options(self, r):
        await r.flushdb()
        await r.set('user:1:username', 'zeus')
        await r.set('user:2:username', 'titan')
        await r.set('user:3:username', 'hermes')
        await r.set('user:4:username', 'hercules')
        await r.set('user:5:username', 'apollo')
        await r.set('user:6:username', 'athena')
        await r.set('user:7:username', 'hades')
        await r.set('user:8:username', 'dionysus')

        await r.set('user:1:favorite_drink', 'yuengling')
        await r.set('user:2:favorite_drink', 'rum')
        await r.set('user:3:favorite_drink', 'vodka')
        await r.set('user:4:favorite_drink', 'milk')
        await r.set('user:5:favorite_drink', 'pinot noir')
        await r.set('user:6:favorite_drink', 'water')
        await r.set('user:7:favorite_drink', 'gin')
        await r.set('user:8:favorite_drink', 'apple juice')

        await r.rpush('gods', '5', '8', '3', '1', '2', '7', '6', '4')
        num = await r.sort('gods', start=2, num=4, by='user:*:username',
                     get='user:*:favorite_drink', desc=True, alpha=True,
                     store='sorted')
        assert num == 4
        assert await r.lrange('sorted', 0, 10) == \
            [b('vodka'), b('milk'), b('gin'), b('apple juice')]

    # GEO COMMANDS
    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_geoadd(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        assert await r.geoadd('barcelona', *values) == 2
        assert await r.zcard('barcelona') == 2

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_geoadd_invalid_params(self, r):
        await r.flushdb()
        with pytest.raises(RedisError):
            await r.geoadd('barcelona', *(1, 2))

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_geodist(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        assert await r.geoadd('barcelona', *values) == 2
        assert await r.geodist('barcelona', 'place1', 'place2') == 3067.4157

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_geodist_units(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)
        assert await r.geodist('barcelona', 'place1', 'place2', 'km') == 3.0674

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_geodist_invalid_units(self, r):
        await r.flushdb()
        with pytest.raises(RedisError):
            assert await r.geodist('x', 'y', 'z', 'inches')

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_geohash(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)
        assert await r.geohash('barcelona', 'place1', 'place2') ==\
            [b'sp3e9yg3kd0', b'sp3e9cbc3t0']

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_geopos(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)
        # redis uses 52 bits precision, hereby small errors may be introduced.
        assert await r.geopos('barcelona', 'place1', 'place2') ==\
            [(2.19093829393386841, 41.43379028184083523),
             (2.18737632036209106, 41.40634178640635099)]

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_georadius(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)
        assert await r.georadius('barcelona', 2.191, 41.433, 1000) == ['place1']

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_georadius_no_values(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)
        assert await r.georadius('barcelona', 1, 2, 1000) == []

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_georadius_units(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)
        assert await r.georadius('barcelona', 2.191, 41.433, 1, unit='km') ==\
            ['place1']

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_georadius_with(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)

        # test a bunch of combinations to test the parse response
        # function.
        assert await r.georadius('barcelona', 2.191, 41.433, 1, unit='km',
                           withdist=True, withcoord=True, withhash=True) ==\
            [['place1', 0.0881, 3471609698139488,
              (2.19093829393386841, 41.43379028184083523)]]

        assert await r.georadius('barcelona', 2.191, 41.433, 1, unit='km',
                           withdist=True, withcoord=True) ==\
            [['place1', 0.0881,
              (2.19093829393386841, 41.43379028184083523)]]

        assert await r.georadius('barcelona', 2.191, 41.433, 1, unit='km',
                           withhash=True, withcoord=True) ==\
            [['place1', 3471609698139488,
              (2.19093829393386841, 41.43379028184083523)]]

        # test no values.
        assert await r.georadius('barcelona', 2, 1, 1, unit='km',
                           withdist=True, withcoord=True, withhash=True) == []

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_georadius_count(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)
        assert await r.georadius('barcelona', 2.191, 41.433, 3000, count=1) ==\
            ['place1']

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_georadius_sort(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)
        assert await r.georadius('barcelona', 2.191, 41.433, 3000, sort='ASC') ==\
            ['place1', 'place2']
        assert await r.georadius('barcelona', 2.191, 41.433, 3000, sort='DESC') ==\
            ['place2', 'place1']

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_georadius_store(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)
        await r.georadius('barcelona', 2.191, 41.433, 1000, store='places_barcelona')
        assert await r.zrange('places_barcelona', 0, -1) == [b'place1']

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_georadius_store_dist(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)
        await r.georadius('barcelona', 2.191, 41.433, 1000,
                    store_dist='places_barcelona')
        # instead of save the geo score, the distance is saved.
        assert await r.zscore('places_barcelona', 'place1') == 88.05060698409301

    @skip_if_server_version_lt('3.2.0')
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_georadiusmember(self, r):
        await r.flushdb()
        values = (2.1909389952632, 41.433791470673, 'place1') +\
                 (2.1873744593677, 41.406342043777, 'place2')

        await r.geoadd('barcelona', *values)
        assert await r.georadiusbymember('barcelona', 'place1', 4000) ==\
            ['place2', 'place1']
        assert await r.georadiusbymember('barcelona', 'place1', 10) == ['place1']

        assert await r.georadiusbymember('barcelona', 'place1', 4000,
                                   withdist=True, withcoord=True,
                                   withhash=True) ==\
            [['place2', 3067.4157, 3471609625421029,
                (2.187376320362091, 41.40634178640635)],
             ['place1', 0.0, 3471609698139488,
                 (2.1909382939338684, 41.433790281840835)]]


class TestBinarySave(object):

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_binary_get_set(self, r):
        await r.flushdb()
        assert await r.set(' foo bar ', '123')
        assert await r.get(' foo bar ') == b('123')

        assert await r.set(' foo\r\nbar\r\n ', '456')
        assert await r.get(' foo\r\nbar\r\n ') == b('456')

        assert await r.set(' \r\n\t\x07\x13 ', '789')
        assert await r.get(' \r\n\t\x07\x13 ') == b('789')

        assert sorted(await r.keys('*')) == \
            [b(' \r\n\t\x07\x13 '), b(' foo\r\nbar\r\n '), b(' foo bar ')]

        assert await r.delete(' foo bar ')
        assert await r.delete(' foo\r\nbar\r\n ')
        assert await r.delete(' \r\n\t\x07\x13 ')

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_binary_lists(self, r):
        await r.flushdb()
        mapping = {
            b('foo bar'): [b('1'), b('2'), b('3')],
            b('foo\r\nbar\r\n'): [b('4'), b('5'), b('6')],
            b('foo\tbar\x07'): [b('7'), b('8'), b('9')],
        }
        # fill in lists
        for key, value in iteritems(mapping):
            await r.rpush(key, *value)

        # check that KEYS returns all the keys as they are
        assert sorted(await r.keys('*')) == sorted(list(iterkeys(mapping)))

        # check that it is possible to get list content by key name
        for key, value in iteritems(mapping):
            assert await r.lrange(key, 0, -1) == value

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_22_info(self, r):
        """
        Older Redis versions contained 'allocation_stats' in INFO that
        was the cause of a number of bugs when parsing.
        """
        await r.flushdb()
        info = b"allocation_stats:6=1,7=1,8=7141,9=180,10=92,11=116,12=5330," \
               b"13=123,14=3091,15=11048,16=225842,17=1784,18=814,19=12020," \
               b"20=2530,21=645,22=15113,23=8695,24=142860,25=318,26=3303," \
               b"27=20561,28=54042,29=37390,30=1884,31=18071,32=31367,33=160," \
               b"34=169,35=201,36=10155,37=1045,38=15078,39=22985,40=12523," \
               b"41=15588,42=265,43=1287,44=142,45=382,46=945,47=426,48=171," \
               b"49=56,50=516,51=43,52=41,53=46,54=54,55=75,56=647,57=332," \
               b"58=32,59=39,60=48,61=35,62=62,63=32,64=221,65=26,66=30," \
               b"67=36,68=41,69=44,70=26,71=144,72=169,73=24,74=37,75=25," \
               b"76=42,77=21,78=126,79=374,80=27,81=40,82=43,83=47,84=46," \
               b"85=114,86=34,87=37,88=7240,89=34,90=38,91=18,92=99,93=20," \
               b"94=18,95=17,96=15,97=22,98=18,99=69,100=17,101=22,102=15," \
               b"103=29,104=39,105=30,106=70,107=22,108=21,109=26,110=52," \
               b"111=45,112=33,113=67,114=41,115=44,116=48,117=53,118=54," \
               b"119=51,120=75,121=44,122=57,123=44,124=66,125=56,126=52," \
               b"127=81,128=108,129=70,130=50,131=51,132=53,133=45,134=62," \
               b"135=12,136=13,137=7,138=15,139=21,140=11,141=20,142=6,143=7," \
               b"144=11,145=6,146=16,147=19,148=1112,149=1,151=83,154=1," \
               b"155=1,156=1,157=1,160=1,161=1,162=2,166=1,169=1,170=1,171=2," \
               b"172=1,174=1,176=2,177=9,178=34,179=73,180=30,181=1,185=3," \
               b"187=1,188=1,189=1,192=1,196=1,198=1,200=1,201=1,204=1,205=1," \
               b"207=1,208=1,209=1,214=2,215=31,216=78,217=28,218=5,219=2," \
               b"220=1,222=1,225=1,227=1,234=1,242=1,250=1,252=1,253=1," \
               b">=256=203"
        parsed = parse_info(info)
        assert 'allocation_stats' in parsed
        assert '6' in parsed['allocation_stats']
        assert '>=256' in parsed['allocation_stats']

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_large_responses(self, r):
        "The PythonParser has some special cases for return values > 1MB"
        # load up 5MB of data into a key
        await r.flushdb()
        data = ''.join([ascii_letters] * (5000000 // len(ascii_letters)))
        await r.set('a', data)
        assert await r.get('a') == b(data)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_floating_point_encoding(self, r):
        """
        High precision floating point values sent to the server should keep
        precision.
        """
        await r.flushdb()
        timestamp = 1349673917.939762
        await r.zadd('a', timestamp, 'a1')
        assert await r.zscore('a', 'a1') == timestamp
