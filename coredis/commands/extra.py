from coredis.exceptions import ResponseError
from coredis.lock import Lock, LuaLock


class ExtraCommandMixin:
    def lock(
        self,
        name,
        timeout=None,
        sleep=0.1,
        blocking_timeout=None,
        lock_class=None,
        thread_local=True,
    ):
        """
        Return a new Lock object using :paramref:`name` that mimics
        the behavior of threading.Lock.

        :param timeout: If specified indicates a maximum life for the lock.
         By default, it will remain locked until release() is called.
        :param sleep: indicates the amount of time to sleep per loop iteration
         when the lock is in blocking mode and another client is currently
         holding the lock.
        :param blocking_timeout: indicates the maximum amount of time in seconds to
         spend trying to acquire the lock. A value of ``None`` indicates
         continue trying forever. ``blocking_timeout`` can be specified as a
         float or integer, both representing the number of seconds to wait.
        :param lock_class: forces the specified lock implementation.
        :param thread_local: indicates whether the lock token is placed in
         thread-local storage.

         By default, the token is placed in thread local
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

        if lock_class is None:
            if self._use_lua_lock is None:  # type: ignore
                # the first time .lock() is called, determine if we can use
                # Lua by attempting to register the necessary scripts
                try:
                    LuaLock.register_scripts(self)
                    self._use_lua_lock = True
                except ResponseError:
                    self._use_lua_lock = False
            lock_class = self._use_lua_lock and LuaLock or Lock

        return lock_class(
            self,
            name,
            timeout=timeout,
            sleep=sleep,
            blocking_timeout=blocking_timeout,
            thread_local=thread_local,
        )
