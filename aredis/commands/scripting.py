from aredis.utils import bool_ok


class ScriptingCommandMixin:

    RESPONSE_CALLBACKS = {
        'SCRIPT EXISTS': lambda r: list(map(bool, r)),
        'SCRIPT FLUSH': bool_ok,
        'SCRIPT KILL': bool_ok,
        'SCRIPT LOAD': lambda r: r.decode(),
    }

    async def eval(self, script, numkeys, *keys_and_args):
        """
        Execute the Lua ``script``, specifying the ``numkeys`` the script
        will touch and the key names and argument values in ``keys_and_args``.
        Returns the result of the script.

        In practice, use the object returned by ``register_script``. This
        function exists purely for Redis API completion.
        """
        return await self.execute_command('EVAL', script, numkeys, *keys_and_args)

    async def evalsha(self, sha, numkeys, *keys_and_args):
        """
        Use the ``sha`` to execute a Lua script already registered via EVAL
        or SCRIPT LOAD. Specify the ``numkeys`` the script will touch and the
        key names and argument values in ``keys_and_args``. Returns the result
        of the script.

        In practice, use the object returned by ``register_script``. This
        function exists purely for Redis API completion.
        """
        return await self.execute_command('EVALSHA', sha, numkeys, *keys_and_args)

    async def script_exists(self, *args):
        """
        Check if a script exists in the script cache by specifying the SHAs of
        each script as ``args``. Returns a list of boolean values indicating if
        if each already script exists in the cache.
        """
        return await self.execute_command('SCRIPT EXISTS', *args)

    async def script_flush(self):
        "Flush all scripts from the script cache"
        return await self.execute_command('SCRIPT FLUSH')

    async def script_kill(self):
        "Kill the currently executing Lua script"
        return await self.execute_command('SCRIPT KILL')

    async def script_load(self, script):
        "Load a Lua ``script`` into the script cache. Returns the SHA."
        return await self.execute_command('SCRIPT LOAD', script)

    def register_script(self, script):
        """
        Register a Lua ``script`` specifying the ``keys`` it will touch.
        Returns a Script object that is callable and hides the complexity of
        deal with scripts, keys, and shas. This is the preferred way to work
        with Lua scripts.
        """
        from aredis.scripting import Script
        return Script(self, script)
