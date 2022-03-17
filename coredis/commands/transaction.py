import asyncio
from abc import ABC
from typing import AnyStr

from coredis.exceptions import WatchError

from ..typing import SupportsPipeline, ValueT
from . import CommandMixin


class TransactionCommandMixin(CommandMixin[AnyStr], ABC):
    async def transaction(self: SupportsPipeline, func, *watches: ValueT, **kwargs):
        """
        Convenience method for executing the callable `func` as a transaction
        while watching all keys specified in `watches`. The 'func' callable
        should expect a single argument which is a Pipeline object.
        """
        value_from_callable = kwargs.pop("value_from_callable", False)
        watch_delay = kwargs.pop("watch_delay", None)
        async with await self.pipeline(True) as pipe:
            while True:
                try:
                    if watches:
                        await pipe.watch(*watches)
                    func_value = await func(pipe)
                    exec_value = await pipe.execute()
                    return func_value if value_from_callable else exec_value
                except WatchError:
                    if watch_delay is not None and watch_delay > 0:
                        await asyncio.sleep(watch_delay)
                    continue


class ClusterTransactionCommandMixin(TransactionCommandMixin[AnyStr], ABC):
    async def transaction(self: SupportsPipeline, func, *watches: ValueT, **kwargs):
        """
        Convenience method for executing the callable `func` as a transaction
        while watching all keys specified in `watches`. The 'func' callable
        should expect a single argument which is a Pipeline object.

        cluster transaction can only be run with commands in the same node,
        otherwise error will be raised.
        """
        value_from_callable = kwargs.pop("value_from_callable", False)
        watch_delay = kwargs.pop("watch_delay", None)
        async with await self.pipeline(True, watches=watches) as pipe:
            while True:
                try:
                    func_value = await func(pipe)
                    exec_value = await pipe.execute()
                    return func_value if value_from_callable else exec_value
                except WatchError:
                    if watch_delay is not None and watch_delay > 0:
                        await asyncio.sleep(watch_delay)
                    continue
