from aredis.utils import (string_keys_to_dict,
                          dict_merge,
                          bool_ok)


class HyperLogCommandMixin:

    RESPONSE_CALLBACKS = dict_merge(
        string_keys_to_dict('PFADD PFCOUNT', int),
        {
            'PFMERGE': bool_ok,
        }
    )

    async def pfadd(self, name, *values):
        "Adds the specified elements to the specified HyperLogLog."
        return await self.execute_command('PFADD', name, *values)

    async def pfcount(self, *sources):
        """
        Return the approximated cardinality of
        the set observed by the HyperLogLog at key(s).
        """
        return await self.execute_command('PFCOUNT', *sources)

    async def pfmerge(self, dest, *sources):
        "Merge N different HyperLogLogs into a single one."
        return await self.execute_command('PFMERGE', dest, *sources)
