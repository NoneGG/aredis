import asyncio
import warnings
from aredis.pipeline import (StrictClusterPipeline,
                             StrictPipeline)
from aredis.exceptions import (RedisClusterException,
                               WatchError)
from aredis.utils import (string_keys_to_dict,
                          bool_ok)


class TransactionCommandMixin:

    RESPONSE_CALLBACKS = string_keys_to_dict(
            'WATCH UNWATCH',
            bool_ok
        )

    async def pipeline(self, transaction=True, shard_hint=None):
        """
        Return a new pipeline object that can queue multiple commands for
        later execution. ``transaction`` indicates whether all commands
        should be executed atomically. Apart from making a group of operations
        atomic, pipelines are useful for reducing the back-and-forth overhead
        between the client and server.
        """
        pipeline = StrictPipeline(self.connection_pool, self.response_callbacks,
                                  transaction, shard_hint)
        await pipeline.reset()
        return pipeline

    async def transaction(self, func, *watches, **kwargs):
        """
        Convenience method for executing the callable `func` as a transaction
        while watching all keys specified in `watches`. The 'func' callable
        should expect a single argument which is a Pipeline object.
        """
        shard_hint = kwargs.pop('shard_hint', None)
        value_from_callable = kwargs.pop('value_from_callable', False)
        watch_delay = kwargs.pop('watch_delay', None)
        async with await self.pipeline(True, shard_hint) as pipe:
            while True:
                try:
                    if watches:
                        await pipe.watch(*watches)
                    func_value = await func(pipe)
                    exec_value = await pipe.execute()
                    return func_value if value_from_callable else exec_value
                except WatchError:
                    if watch_delay is not None and watch_delay > 0:
                        await asyncio.sleep(
                            watch_delay,
                            loop=self.connection_pool.loop
                        )
                    continue

    async def watch(self, *names):
        """
        Watches the values at keys ``names``, or None if the key doesn't exist
        """
        warnings.warn(DeprecationWarning('Call WATCH from a Pipeline object'))

    async def unwatch(self):
        """
        Unwatches the value at key ``name``, or None of the key doesn't exist
        """
        warnings.warn(
            DeprecationWarning('Call UNWATCH from a Pipeline object'))


class ClusterTransactionCommandMixin(TransactionCommandMixin):

    def pipeline(self, transaction=None, shard_hint=None):
        """
        Cluster impl:
            Pipelines do not work in cluster mode the same way they do in normal mode.
            Create a clone of this object so that simulating pipelines will work correctly.
            Each command will be called directly when used and when calling execute() will only return the result stack.
        """
        if shard_hint:
            raise RedisClusterException("shard_hint is deprecated in cluster mode")

        if transaction:
            raise RedisClusterException("transaction is deprecated in cluster mode")

        return StrictClusterPipeline(
            connection_pool=self.connection_pool,
            startup_nodes=self.connection_pool.nodes.startup_nodes,
            result_callbacks=self.result_callbacks,
            response_callbacks=self.response_callbacks,
        )

    def transaction(self, *args, **kwargs):
        """
        Transaction is not implemented in cluster mode yet.
        """
        raise RedisClusterException("method StrictRedisCluster.transaction() is not implemented")
