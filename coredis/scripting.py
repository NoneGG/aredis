import hashlib
from coredis.pipeline import BasePipeline
from coredis.exceptions import NoScriptError
from coredis.utils import b


class Script:
    """An executable Lua script object returned by ``register_script``"""

    def __init__(self, registered_client, script):
        self.registered_client = registered_client
        self.script = script
        self.sha = hashlib.sha1(b(script)).hexdigest()

    async def execute(self, keys=[], args=[], client=None):
        """Executes the script, passing any required ``args``"""
        if client is None:
            client = self.registered_client
        args = tuple(keys) + tuple(args)
        # make sure the Redis server knows about the script
        if isinstance(client, BasePipeline):
            # make sure this script is good to go on pipeline
            client.scripts.add(self)
        try:
            return await client.evalsha(self.sha, len(keys), *args)
        except NoScriptError:
            # Maybe the client is pointed to a differnet server than the client
            # that created this instance?
            # Overwrite the sha just in case there was a discrepancy.
            self.sha = await client.script_load(self.script)
            return await client.evalsha(self.sha, len(keys), *args)
