from coredis.exceptions import DataError
from coredis.utils import NodeFlag, bool_ok, dict_merge, list_keys_to_dict, nativestr


class ScriptingCommandMixin:

    RESPONSE_CALLBACKS = {
        "SCRIPT EXISTS": lambda r: list(map(bool, r)),
        "SCRIPT FLUSH": bool_ok,
        "SCRIPT KILL": bool_ok,
        "SCRIPT LOAD": nativestr,
    }

    async def eval(self, script, numkeys, *keys_and_args):
        """
        Execute the Lua ``script``, specifying the ``numkeys`` the script
        will touch and the key names and argument values in ``keys_and_args``.
        Returns the result of the script.

        In practice, use the object returned by ``register_script``. This
        function exists purely for Redis API completion.
        """

        return await self.execute_command("EVAL", script, numkeys, *keys_and_args)

    async def evalsha(self, sha, numkeys, *keys_and_args):
        """
        Use the ``sha`` to execute a Lua script already registered via EVAL
        or SCRIPT LOAD. Specify the ``numkeys`` the script will touch and the
        key names and argument values in ``keys_and_args``. Returns the result
        of the script.

        In practice, use the object returned by ``register_script``. This
        function exists purely for Redis API completion.
        """

        return await self.execute_command("EVALSHA", sha, numkeys, *keys_and_args)

    async def script_exists(self, *args):
        """
        Check if a script exists in the script cache by specifying the SHAs of
        each script as ``args``. Returns a list of boolean values indicating if
        if each already script exists in the cache.
        """

        return await self.execute_command("SCRIPT EXISTS", *args)

    async def script_flush(self, sync_type=None):
        """
        Flushes all scripts from the script cache

        :param sync_type: ``SYNC`` or ``ASYNC``. Default ``SYNC``

        .. versionadded:: 2.1.0
        """

        if sync_type not in ["SYNC", "ASYNC", None]:
            raise DataError(
                "SCRIPT FLUSH defaults to SYNC in redis > 6.2, or "
                "accepts SYNC/ASYNC. For older versions, "
                "of redis leave as None."
            )

        if sync_type is None:
            pieces = []
        else:
            pieces = [sync_type]

        return await self.execute_command("SCRIPT FLUSH", *pieces)

    async def script_kill(self):
        """Kills the currently executing Lua script"""

        return await self.execute_command("SCRIPT KILL")

    async def script_load(self, script):
        """Loads a Lua ``script`` into the script cache. Returns the SHA."""

        return await self.execute_command("SCRIPT LOAD", script)

    def register_script(self, script):
        """
        Registers a Lua ``script`` specifying the ``keys`` it will touch.
        Returns a Script object that is callable and hides the complexity of
        dealing with scripts, keys, and shas. This is the preferred way of
        working with Lua scripts.
        """
        from coredis.scripting import Script

        return Script(self, script)


class ClusterScriptingCommandMixin(ScriptingCommandMixin):

    NODES_FLAGS = dict_merge(
        {"SCRIPT KILL": NodeFlag.BLOCKED},
        list_keys_to_dict(
            ["SCRIPT LOAD", "SCRIPT FLUSH", "SCRIPT EXISTS"], NodeFlag.ALL_MASTERS
        ),
    )

    RESULT_CALLBACKS = {
        "SCRIPT LOAD": lambda res: list(res.values()).pop(),
        "SCRIPT EXISTS": lambda res: [all(k) for k in zip(*res.values())],
        "SCRIPT FLUSH": lambda res: all(res.values()),
    }
