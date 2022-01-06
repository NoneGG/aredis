import asyncio
import contextvars
import time as mod_time
import uuid
import warnings

from coredis.connection import ClusterConnection
from coredis.exceptions import LockError, WatchError
from coredis.utils import LOOP_DEPRECATED, b, dummy


class Lock:
    """
    A shared, distributed Lock. Using Redis for locking allows the Lock
    to be shared across processes and/or machines.

    It's left to the user to resolve deadlock issues and make sure
    multiple clients play nicely together.
    """

    def __init__(
        self,
        redis,
        name,
        timeout=None,
        sleep=0.1,
        blocking=True,
        blocking_timeout=None,
        thread_local=True,
    ):
        """
        Create a new Lock instance named ``name`` using the Redis client
        supplied by ``redis``.

        ``timeout`` indicates a maximum life for the lock.
        By default, it will remain locked until release() is called.
        ``timeout`` can be specified as a float or integer, both representing
        the number of seconds to wait.

        ``sleep`` indicates the amount of time to sleep per loop iteration
        when the lock is in blocking mode and another client is currently
        holding the lock.

        ``blocking`` indicates whether calling ``acquire`` should block until
        the lock has been acquired or to fail immediately, causing ``acquire``
        to return False and the lock not being acquired. Defaults to True.
        Note this value can be overridden by passing a ``blocking``
        argument to ``acquire``.

        ``blocking_timeout`` indicates the maximum amount of time in seconds to
        spend trying to acquire the lock. A value of ``None`` indicates
        continue trying forever. ``blocking_timeout`` can be specified as a
        float or integer, both representing the number of seconds to wait.

        ``thread_local`` indicates whether the lock token is placed in
        thread-local storage. By default, the token is placed in thread local
        storage so that a thread only sees its token, not a token set by
        another thread. Consider the following timeline:

            time: 0, thread-1 acquires `my-lock`, with a timeout of 5 seconds.
                     thread-1 sets the token to "abc"
            time: 1, thread-2 blocks trying to acquire `my-lock` using the
                     Lock instance.
            time: 5, thread-1 has not yet completed. redis expires the lock
                     key.
            time: 5, thread-2 acquired `my-lock` now that it's available.
                     thread-2 sets the token to "xyz"
            time: 6, thread-1 finishes its work and calls release(). if the
                     token is *not* stored in thread local storage, then
                     thread-1 would see the token value as "xyz" and would be
                     able to successfully release the thread-2's lock.

        In some use cases it's necessary to disable thread local storage. For
        example, if you have code where one thread acquires a lock and passes
        that lock instance to a worker thread to release later. If thread
        local storage isn't disabled in this case, the worker thread won't see
        the token set by the thread that acquired the lock. Our assumption
        is that these cases aren't common and as such default to using
        thread local storage.
        """
        self.redis = redis
        self.name = name
        self.timeout = timeout
        self.sleep = sleep
        self.blocking = blocking
        self.blocking_timeout = blocking_timeout
        self.thread_local = bool(thread_local)
        self.local = (
            contextvars.ContextVar("token", default=None)
            if self.thread_local
            else dummy()
        )
        if self.timeout and self.sleep > self.timeout:
            raise LockError("'sleep' must be less than 'timeout'")

    async def __aenter__(self):
        # force blocking, as otherwise the user would have to check whether
        # the lock was actually acquired or not.
        await self.acquire(blocking=True)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.release()

    async def acquire(self, blocking=None, blocking_timeout=None):
        """
        Use Redis to hold a shared, distributed lock named ``name``.
        Returns True once the lock is acquired.

        If ``blocking`` is False, always return immediately. If the lock
        was acquired, return True, otherwise return False.

        ``blocking_timeout`` specifies the maximum number of seconds to
        wait trying to acquire the lock.
        """
        sleep = self.sleep
        token = b(uuid.uuid1().hex)
        if blocking is None:
            blocking = self.blocking
        if blocking_timeout is None:
            blocking_timeout = self.blocking_timeout
        stop_trying_at = None
        if blocking_timeout is not None:
            stop_trying_at = mod_time.time() + blocking_timeout
        while True:
            if await self.do_acquire(token):
                self.local.set(token)
                return True
            if not blocking:
                return False
            if stop_trying_at is not None and mod_time.time() > stop_trying_at:
                return False
            if LOOP_DEPRECATED:
                await asyncio.sleep(sleep)
            else:
                await asyncio.sleep(sleep, loop=self.redis.connection_pool.loop)

    async def do_acquire(self, token):
        if self.timeout:
            # convert to milliseconds
            timeout = int(self.timeout * 1000)
        else:
            timeout = None
        return await self.redis.set(self.name, token, nx=True, px=timeout)

    async def release(self):
        """Releases the already acquired lock"""
        expected_token = self.local.get()
        if expected_token is None:
            raise LockError("Cannot release an unlocked lock")
        self.local.set(None)
        await self.do_release(expected_token)

    async def do_release(self, expected_token):
        name = self.name

        async def execute_release(pipe):
            lock_value = await pipe.get(name)
            if lock_value != expected_token:
                raise LockError("Cannot release a lock that's no longer owned")
            await pipe.delete(name)

        await self.redis.transaction(execute_release, name)

    async def extend(self, additional_time):
        """
        Adds more time to an already acquired lock.

        ``additional_time`` can be specified as an integer or a float, both
        representing the number of seconds to add.
        """
        if self.local.get() is None:
            raise LockError("Cannot extend an unlocked lock")
        if self.timeout is None:
            raise LockError("Cannot extend a lock with no timeout")
        return await self.do_extend(additional_time)

    async def do_extend(self, additional_time):
        pipe = await self.redis.pipeline()
        await pipe.watch(self.name)
        lock_value = await pipe.get(self.name)
        if lock_value != self.local.get():
            raise LockError("Cannot extend a lock that's no longer owned")
        expiration = await pipe.pttl(self.name)
        if expiration is None or expiration < 0:
            # Redis evicted the lock key between the previous get() and now
            # we'll handle this when we call pexpire()
            expiration = 0
        pipe.multi()
        await pipe.pexpire(self.name, expiration + int(additional_time * 1000))

        try:
            response = await pipe.execute()
        except WatchError:
            # someone else acquired the lock
            raise LockError("Cannot extend a lock that's no longer owned")
        if not response[0]:
            # pexpire returns False if the key doesn't exist
            raise LockError("Cannot extend a lock that's no longer owned")
        return True


class LuaLock(Lock):
    """
    A lock implementation that uses Lua scripts rather than pipelines
    and watches.
    """

    lua_release = None
    lua_extend = None

    # KEYS[1] - lock name
    # ARGS[1] - token
    # return 1 if the lock was released, otherwise 0
    LUA_RELEASE_SCRIPT = """
        local token = redis.call('get', KEYS[1])
        if not token or token ~= ARGV[1] then
            return 0
        end
        redis.call('del', KEYS[1])
        return 1
    """

    # KEYS[1] - lock name
    # ARGS[1] - token
    # ARGS[2] - additional milliseconds
    # return 1 if the locks time was extended, otherwise 0
    LUA_EXTEND_SCRIPT = """
        local token = redis.call('get', KEYS[1])
        if not token or token ~= ARGV[1] then
            return 0
        end
        local expiration = redis.call('pttl', KEYS[1])
        if not expiration then
            expiration = 0
        end
        if expiration < 0 then
            return 0
        end
        redis.call('pexpire', KEYS[1], expiration + ARGV[2])
        return 1
    """

    def __init__(self, *args, **kwargs):
        super(LuaLock, self).__init__(*args, **kwargs)
        LuaLock.register_scripts(self.redis)

    @classmethod
    def register_scripts(cls, redis):
        if cls.lua_release is None:
            cls.lua_release = redis.register_script(cls.LUA_RELEASE_SCRIPT)
        if cls.lua_extend is None:
            cls.lua_extend = redis.register_script(cls.LUA_EXTEND_SCRIPT)

    async def do_release(self, expected_token):
        if not bool(
            await self.lua_release.execute(
                keys=[self.name], args=[expected_token], client=self.redis
            )
        ):
            raise LockError("Cannot release a lock that's no longer owned")

    async def do_extend(self, additional_time):
        additional_time = int(additional_time * 1000)
        if not bool(
            await self.lua_extend.execute(
                keys=[self.name],
                args=[self.local.get(), additional_time],
                client=self.redis,
            )
        ):
            raise LockError("Cannot extend a lock that's no longer owned")
        return True


class ClusterLock(LuaLock):
    """
    Cluster lock is supposed to solve lock problem in redis cluster.
    Since high availability is provided by redis cluster using master-slave model,
    the kind of lock aims to solve the fail-over problem referred in distributed lock
    post given by redis official.

    Why not use Redlock algorithm provided by official directly?
    It is impossible to make a key hashed to different nodes
    in a redis cluster and hard to generate keys
    in a specific rule and make sure they do not migrated in cluster.
    In the worst situation, all key slots may exists in one node.
    Then the availability will be the same as one key in one node.
    For more discussion please see:
    https://github.com/alisaifee/coredis/issues/55

    My solution is to take advantage of `READONLY` mode of slaves to ensure
    the lock key is synced from master to N/2 + 1 of its slaves to avoid the fail-over problem.
    Since it is a single-key solution, the migration problem also do no matter.

    Please read these article below before using this cluster lock in your app.
    https://redis.io/topics/distlock
    http://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html
    http://antirez.com/news/101
    """

    def __init__(self, *args, **kwargs):
        super(ClusterLock, self).__init__(*args, **kwargs)
        if not self.timeout:
            raise LockError("timeout must be provided for cluster lock")

    async def check_lock_in_slaves(self, token):
        node_manager = self.redis.connection_pool.nodes
        slot = node_manager.keyslot(self.name)
        master_node_id = node_manager.node_from_slot(slot)["node_id"]
        slave_nodes = await self.redis.cluster_slaves(master_node_id)
        count, quorum = 0, (len(slave_nodes) // 2) + 1
        conn_kwargs = self.redis.connection_pool.connection_kwargs
        conn_kwargs["readonly"] = True
        for node in slave_nodes:
            try:
                # todo: a little bit dirty here, try to reuse StrictRedis later
                # todo: it may be optimized by using a new connection pool
                conn = ClusterConnection(
                    host=node["host"], port=node["port"], **conn_kwargs
                )
                await conn.send_command("get", self.name)
                res = await conn.read_response()
                if res == token:
                    count += 1
                if count >= quorum:
                    return True
            except Exception as exc:
                warnings.warn(
                    "error {} during check lock {} status in slave nodes".format(
                        exc, self.name
                    )
                )
        return False

    async def acquire(self, blocking=None, blocking_timeout=None):
        """
        Use Redis to hold a shared, distributed lock named ``name``.
        Returns True once the lock is acquired.

        If ``blocking`` is False, always return immediately. If the lock
        was acquired, return True, otherwise return False.

        ``blocking_timeout`` specifies the maximum number of seconds to
        wait trying to acquire the lock. It should not be greater than
        expire time of the lock
        """
        sleep = self.sleep
        token = b(uuid.uuid1().hex)
        if blocking is None:
            blocking = self.blocking
        if blocking_timeout is None:
            blocking_timeout = self.blocking_timeout
        blocking_timeout = blocking_timeout or self.timeout
        stop_trying_at = mod_time.time() + min(blocking_timeout, self.timeout)

        while True:
            if await self.do_acquire(token):
                lock_acquired_at = mod_time.time()
                if await self.check_lock_in_slaves(token):
                    check_finished_at = mod_time.time()
                    # if time expends on acquiring lock is greater than given time
                    # the lock should be released manually
                    if check_finished_at > stop_trying_at:
                        await self.do_release(token)
                        return False
                    self.local.set(token)
                    # validity time is considered to be the
                    # initial validity time minus the time elapsed during check
                    await self.do_extend(lock_acquired_at - check_finished_at)
                    return True
                else:
                    await self.do_release(token)
                    return False
            if not blocking or mod_time.time() > stop_trying_at:
                return False
            if LOOP_DEPRECATED:
                await asyncio.sleep(sleep)
            else:
                await asyncio.sleep(sleep, loop=self.redis.connection_pool.loop)

    async def do_release(self, expected_token):
        await super(ClusterLock, self).do_release(expected_token)
        if await self.check_lock_in_slaves(expected_token):
            raise LockError("Lock is released in master but not in slave yet")
