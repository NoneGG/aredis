from aredis.pipeline import BasePipeline
from aredis.exceptions import NoScriptError


class Script(object):
    "An executable Lua script object returned by ``register_script``"

    def __init__(self, registered_client, script):
        self.registered_client = registered_client
        self.script = script
        self.sha = ''

    async def execute(self, keys=[], args=[], client=None):
        "Execute the script, passing any required ``args``"
        if client is None:
            client = self.registered_client
        args = tuple(keys) + tuple(args)
        # make sure the Redis server knows about the script
        if isinstance(client, BasePipeline):
            # make sure this script is good to go on pipeline
            await client.script_load_for_pipeline(self)
        try:
            return await client.evalsha(self.sha, len(keys), *args)
        except NoScriptError:
            # Maybe the client is pointed to a differnet server than the client
            # that created this instance?
            self.sha = await client.script_load(self.script)
            return await client.evalsha(self.sha, len(keys), *args)
