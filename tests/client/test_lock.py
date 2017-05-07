from __future__ import with_statement
import pytest
import time

from aredis.exceptions import LockError, ResponseError
from aredis.lock import Lock, LuaLock


class TestLock(object):
    lock_class = Lock

    def get_lock(self, redis, *args, **kwargs):
        kwargs['lock_class'] = self.lock_class
        return redis.lock(*args, **kwargs)

    @pytest.mark.asyncio()
    async def test_lock(self, r):
        await r.flushdb()
        lock = self.get_lock(r, 'foo')
        assert await lock.acquire(blocking=False)
        assert await r.get('foo') == lock.local.token
        assert await r.ttl('foo') == -1
        await lock.release()
        assert await r.get('foo') is None

    @pytest.mark.asyncio()
    async def test_competing_locks(self, r):
        lock1 = self.get_lock(r, 'foo')
        lock2 = self.get_lock(r, 'foo')
        assert await lock1.acquire(blocking=False)
        assert not await lock2.acquire(blocking=False)
        await lock1.release()
        assert await lock2.acquire(blocking=False)
        assert not await lock1.acquire(blocking=False)
        await lock2.release()

    @pytest.mark.asyncio()
    async def test_timeout(self, r):
        lock = self.get_lock(r, 'foo', timeout=10)
        assert await lock.acquire(blocking=False)
        assert 8 < await r.ttl('foo') <= 10
        await lock.release()

    @pytest.mark.asyncio()
    async def test_float_timeout(self, r):
        lock = self.get_lock(r, 'foo', timeout=9.5)
        assert await lock.acquire(blocking=False)
        assert 8 < await r.pttl('foo') <= 9500
        await lock.release()

    @pytest.mark.asyncio()
    async def test_blocking_timeout(self, r):
        lock1 = self.get_lock(r, 'foo')
        assert await lock1.acquire(blocking=False)
        lock2 = self.get_lock(r, 'foo', blocking_timeout=0.2)
        start = time.time()
        assert not await lock2.acquire()
        assert (time.time() - start) > 0.2
        await lock1.release()

    @pytest.mark.asyncio()
    async def test_context_manager(self, r):
        # blocking_timeout prevents a deadlock if the lock can't be acquired
        # for some reason
        async with self.get_lock(r, 'foo', blocking_timeout=0.2) as lock:
            assert await r.get('foo') == lock.local.token
        assert await r.get('foo') is None

    @pytest.mark.asyncio()
    async def test_high_sleep_raises_error(self, r):
        "If sleep is higher than timeout, it should raise an error"
        with pytest.raises(LockError):
            self.get_lock(r, 'foo', timeout=1, sleep=2)

    @pytest.mark.asyncio()
    async def test_releasing_unlocked_lock_raises_error(self, r):
        lock = self.get_lock(r, 'foo')
        with pytest.raises(LockError):
            await lock.release()

    @pytest.mark.asyncio()
    async def test_releasing_lock_no_longer_owned_raises_error(self, r):
        lock = self.get_lock(r, 'foo')
        await lock.acquire(blocking=False)
        # manually change the token
        await r.set('foo', 'a')
        with pytest.raises(LockError):
            await lock.release()
        # even though we errored, the token is still cleared
        assert lock.local.token is None

    @pytest.mark.asyncio()
    async def test_extend_lock(self, r):
        await r.flushdb()
        lock = self.get_lock(r, 'foo', timeout=10)
        assert await lock.acquire(blocking=False)
        assert 8000 < await r.pttl('foo') <= 10000
        assert await lock.extend(10)
        assert 16000 < await r.pttl('foo') <= 20000
        await lock.release()

    @pytest.mark.asyncio()
    async def test_extend_lock_float(self, r):
        await r.flushdb()
        lock = self.get_lock(r, 'foo', timeout=10.0)
        assert await lock.acquire(blocking=False)
        assert 8000 < await r.pttl('foo') <= 10000
        assert await lock.extend(10.0)
        assert 16000 < await r.pttl('foo') <= 20000
        await lock.release()

    @pytest.mark.asyncio()
    async def test_extending_unlocked_lock_raises_error(self, r):
        lock = self.get_lock(r, 'foo', timeout=10)
        with pytest.raises(LockError):
            await lock.extend(10)

    @pytest.mark.asyncio()
    async def test_extending_lock_with_no_timeout_raises_error(self, r):
        lock = self.get_lock(r, 'foo')
        await r.flushdb()
        assert await lock.acquire(blocking=False)
        with pytest.raises(LockError):
            await lock.extend(10)
        await lock.release()

    @pytest.mark.asyncio()
    async def test_extending_lock_no_longer_owned_raises_error(self, r):
        lock = self.get_lock(r, 'foo')
        await r.flushdb()
        assert await lock.acquire(blocking=False)
        await r.set('foo', 'a')
        with pytest.raises(LockError):
            await lock.extend(10)


class TestLuaLock(TestLock):
    lock_class = LuaLock


class TestLockClassSelection(object):

    @pytest.mark.asyncio()
    async def test_lock_class_argument(self, r):
        lock = r.lock('foo', lock_class=Lock)
        assert type(lock) == Lock
        lock = r.lock('foo', lock_class=LuaLock)
        assert type(lock) == LuaLock

    @pytest.mark.asyncio()
    async def test_cached_lualock_flag(self, r):
        try:
            r._use_lua_lock = True
            lock = r.lock('foo')
            assert type(lock) == LuaLock
        finally:
            r._use_lua_lock = None

    @pytest.mark.asyncio()
    async def test_cached_lock_flag(self, r):
        try:
            r._use_lua_lock = False
            lock = r.lock('foo')
            assert type(lock) == Lock
        finally:
            r._use_lua_lock = None

    @pytest.mark.asyncio()
    async def test_lua_compatible_server(self, r, monkeypatch):
        @classmethod
        def mock_register(cls, redis):
            return
        monkeypatch.setattr(LuaLock, 'register_scripts', mock_register)
        try:
            lock = r.lock('foo')
            assert type(lock) == LuaLock
            assert r._use_lua_lock is True
        finally:
            r._use_lua_lock = None

    @pytest.mark.asyncio()
    async def test_lua_unavailable(self, r, monkeypatch):
        @classmethod
        def mock_register(cls, redis):
            raise ResponseError()
        monkeypatch.setattr(LuaLock, 'register_scripts', mock_register)
        try:
            lock = r.lock('foo')
            assert type(lock) == Lock
            assert r._use_lua_lock is False
        finally:
            r._use_lua_lock = None
