import time

import pytest

from coredis.exceptions import LockError
from coredis.lock import LuaLock


class TestLock:
    lock_class = LuaLock

    def get_lock(self, redis, *args, **kwargs):
        kwargs["lock_class"] = self.lock_class

        return redis.lock(*args, **kwargs)

    @pytest.mark.asyncio()
    async def test_lock(self, redis_cluster):
        lock = self.get_lock(redis_cluster, "foo", timeout=3)
        assert await lock.acquire(blocking=False)
        assert await redis_cluster.get("foo") == lock.local.get()
        assert await redis_cluster.ttl("foo") == 3
        await lock.release()
        assert await redis_cluster.get("foo") is None

    @pytest.mark.asyncio()
    async def test_competing_locks(self, redis_cluster):
        lock1 = self.get_lock(redis_cluster, "foo", timeout=3)
        lock2 = self.get_lock(redis_cluster, "foo", timeout=3)
        assert await lock1.acquire(blocking=False)
        assert not await lock2.acquire(blocking=False)
        await lock1.release()
        assert await lock2.acquire(blocking=False)
        assert not await lock1.acquire(blocking=False)
        await lock2.release()

    @pytest.mark.asyncio()
    async def test_timeout(self, redis_cluster):
        lock = self.get_lock(redis_cluster, "foo", timeout=10)
        assert await lock.acquire(blocking=False)
        assert 8 < await redis_cluster.ttl("foo") <= 10
        await lock.release()

    @pytest.mark.asyncio()
    async def test_float_timeout(self, redis_cluster):
        lock = self.get_lock(redis_cluster, "foo", timeout=9.5)
        assert await lock.acquire(blocking=False)
        assert 8 < await redis_cluster.pttl("foo") <= 9500
        await lock.release()

    @pytest.mark.asyncio()
    async def test_blocking_timeout(self, redis_cluster):
        lock1 = self.get_lock(redis_cluster, "foo", timeout=3)
        assert await lock1.acquire(blocking=False)
        lock2 = self.get_lock(redis_cluster, "foo", timeout=3, blocking_timeout=0.2)
        start = time.time()
        assert not await lock2.acquire()
        assert (time.time() - start) > 0.2
        await lock1.release()

    @pytest.mark.asyncio()
    async def test_context_manager(self, redis_cluster):
        # blocking_timeout prevents a deadlock if the lock can't be acquired
        # for some reason
        async with self.get_lock(
            redis_cluster, "foo", timeout=3, blocking_timeout=0.2
        ) as lock:
            assert await redis_cluster.get("foo") == lock.local.get()
        assert await redis_cluster.get("foo") is None

    @pytest.mark.asyncio()
    async def test_high_sleep_raises_error(self, redis_cluster):
        "If sleep is higher than timeout, it should raise an error"
        with pytest.raises(LockError):
            self.get_lock(redis_cluster, "foo", timeout=1, sleep=2)

    @pytest.mark.asyncio()
    async def test_releasing_unlocked_lock_raises_error(self, redis_cluster):
        lock = self.get_lock(redis_cluster, "foo", timeout=3)
        with pytest.raises(LockError):
            await lock.release()

    @pytest.mark.asyncio()
    async def test_releasing_lock_no_longer_owned_raises_error(self, redis_cluster):
        lock = self.get_lock(redis_cluster, "foo", timeout=3)
        await lock.acquire(blocking=False)
        # manually change the token
        await redis_cluster.set("foo", "a")
        with pytest.raises(LockError):
            await lock.release()
        # even though we errored, the token is still cleared
        assert lock.local.get() is None

    @pytest.mark.asyncio()
    async def test_extend_lock(self, redis_cluster):
        lock = self.get_lock(redis_cluster, "foo", timeout=10)
        assert await lock.acquire(blocking=False)
        assert 8000 < await redis_cluster.pttl("foo") <= 10000
        assert await lock.extend(10)
        assert 16000 < await redis_cluster.pttl("foo") <= 20000
        await lock.release()

    @pytest.mark.asyncio()
    async def test_extend_lock_float(self, redis_cluster):
        lock = self.get_lock(redis_cluster, "foo", timeout=10.0)
        assert await lock.acquire(blocking=False)
        assert 8000 < await redis_cluster.pttl("foo") <= 10000
        assert await lock.extend(10.0)
        assert 16000 < await redis_cluster.pttl("foo") <= 20000
        await lock.release()

    @pytest.mark.asyncio()
    async def test_extending_unlocked_lock_raises_error(self, redis_cluster):
        lock = self.get_lock(redis_cluster, "foo", timeout=10)
        with pytest.raises(LockError):
            await lock.extend(10)

    @pytest.mark.asyncio()
    async def test_extending_lock_no_longer_owned_raises_error(self, redis_cluster):
        lock = self.get_lock(redis_cluster, "foo", timeout=3)
        await redis_cluster.flushdb()
        assert await lock.acquire(blocking=False)
        await redis_cluster.set("foo", "a")
        with pytest.raises(LockError):
            await lock.extend(10)
