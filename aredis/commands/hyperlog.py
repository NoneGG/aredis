import string
import random
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


class ClusterHyperLogCommandMixin(HyperLogCommandMixin):

    async def pfmerge(self, dest, *sources):
        """
        Merge N different HyperLogLogs into a single one.

        Cluster impl:
            Very special implementation is required to make pfmerge() work
            But it works :]
            It works by first fetching all HLL objects that should be merged and
            move them to one hashslot so that pfmerge operation can be performed without
            any 'CROSSSLOT' error.
            After the PFMERGE operation is done then it will be moved to the correct location
            within the cluster and cleanup is done.

            This operation is no longer atomic because of all the operations that has to be done.
        """
        all_k = []

        # Fetch all HLL objects via GET and store them client side as strings
        all_hll_objects = list()
        for hll_key in sources:
            all_hll_objects.append(await self.get(hll_key))

        # Randomize a keyslot hash that should be used inside {} when doing SET
        random_hash_slot = self._random_id()

        # Special handling of dest variable if it allready exists, then it shold be included in the HLL merge
        # dest can exists anywhere in the cluster.
        dest_data = await self.get(dest)

        if dest_data:
            all_hll_objects.append(dest_data)

        # SET all stored HLL objects with SET {RandomHash}RandomKey hll_obj
        for hll_object in all_hll_objects:
            k = self._random_good_hashslot_key(random_hash_slot)
            all_k.append(k)
            await self.set(k, hll_object)

        # Do regular PFMERGE operation and store value in random key in {RandomHash}
        tmp_dest = self._random_good_hashslot_key(random_hash_slot)
        await self.execute_command("PFMERGE", tmp_dest, *all_k)

        # Do GET and SET so that result will be stored in the destination object any where in the cluster
        parsed_dest = await self.get(tmp_dest)
        await self.set(dest, parsed_dest)

        # Cleanup tmp variables
        await self.delete(tmp_dest)

        for k in all_k:
            await self.delete(k)

        return True

    def _random_good_hashslot_key(self, hashslot):
        """
        Generate a good random key with a low probability of collision between any other key.
        """
        # TODO: Check if the key exists or not. continue to randomize until a empty key is found
        random_id = "{{0}}{1}".format(hashslot, self._random_id())
        return random_id

    def _random_id(self, size=16, chars=string.ascii_uppercase + string.digits):
        """
        Generates a random id based on `size` and `chars` variable.

        By default it will generate a 16 character long string based on
        ascii uppercase letters and digits.
        """
        return ''.join(random.choice(chars) for _ in range(size))
