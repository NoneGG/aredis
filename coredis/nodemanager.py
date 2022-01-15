# -*- coding: utf-8 -*-

import random

from coredis.exceptions import ConnectionError, RedisClusterException
from coredis.utils import b, hash_slot


class NodeManager:
    """
    TODO: document
    """

    RedisClusterHashSlots = 16384

    def __init__(
        self,
        startup_nodes=None,
        reinitialize_steps=None,
        skip_full_coverage_check=False,
        nodemanager_follow_cluster=False,
        **connection_kwargs,
    ):
        """
        :skip_full_coverage_check:
            Skips the check of cluster-require-full-coverage config, useful for clusters
            without the CONFIG command (like aws)
        :nodemanager_follow_cluster:
            The node manager will during initialization try the last set of nodes that
            it was operating on. This will allow the client to drift along side the cluster
            if the cluster nodes move around a slot.
        """
        self.connection_kwargs = connection_kwargs
        self.nodes = {}
        self.slots = {}
        self.startup_nodes = [] if startup_nodes is None else startup_nodes
        self.orig_startup_nodes = self.startup_nodes[:]
        self.reinitialize_counter = 0
        self.reinitialize_steps = reinitialize_steps or 25
        self._skip_full_coverage_check = skip_full_coverage_check
        self.nodemanager_follow_cluster = nodemanager_follow_cluster

        if not self.startup_nodes:
            raise RedisClusterException("No startup nodes provided")

    def encode(self, value):
        """Returns a bytestring representation of the value"""
        if isinstance(value, bytes):
            return value
        elif isinstance(value, int):
            value = b(str(value))
        elif isinstance(value, float):
            value = b(repr(value))
        elif not isinstance(value, str):
            value = str(value)
        if isinstance(value, str):
            value = value.encode()
        return value

    def keyslot(self, key):
        """Calculates keyslot for a given key"""
        key = self.encode(key)
        return hash_slot(key)

    def node_from_slot(self, slot):
        for node in self.slots[slot]:
            if node["server_type"] == "master":
                return node

    def all_nodes(self):
        for node in self.nodes.values():
            yield node

    def all_masters(self):
        for node in self.nodes.values():
            if node["server_type"] == "master":
                yield node

    def random_startup_node(self):
        return random.choice(self.startup_nodes)

    def random_startup_node_iter(self):
        """A generator that returns a random startup nodes"""
        while True:
            yield random.choice(self.startup_nodes)

    def random_node(self):
        return random.choice(list(self.nodes.values()))

    def get_redis_link(self, host, port):
        from coredis.client import StrictRedis

        allowed_keys = (
            "password",
            "stream_timeout",
            "connect_timeout",
            "retry_on_timeout",
            "ssl_context",
            "parser_class",
            "reader_read_size",
            "loop",
        )
        connection_kwargs = {
            k: v for k, v in self.connection_kwargs.items() if k in allowed_keys
        }
        return StrictRedis(
            host=host, port=port, decode_responses=True, **connection_kwargs
        )

    async def initialize(self):
        """
        Initializes the slots cache by asking all startup nodes what the
        current cluster configuration is.

        TODO: Currently the last node will have the last say about how the configuration is setup.
        Maybe it should stop to try after it have correctly covered all slots or when one node is
        reached and it could execute CLUSTER SLOTS command.
        """
        nodes_cache = {}
        tmp_slots = {}

        all_slots_covered = False
        disagreements = []
        startup_nodes_reachable = False

        nodes = self.orig_startup_nodes

        # With this option the client will attempt to connect to any of the previous set of nodes
        # instead of the original set of nodes
        if self.nodemanager_follow_cluster:
            nodes = self.startup_nodes

        for node in nodes:
            try:
                r = self.get_redis_link(host=node["host"], port=node["port"])
                cluster_slots = await r.cluster_slots()
                startup_nodes_reachable = True
            except ConnectionError:
                continue
            except Exception:
                raise RedisClusterException(
                    f'ERROR sending "cluster slots" command to redis server: {node}'
                )

            all_slots_covered = True

            # If there's only one server in the cluster, its ``host`` is ''
            # Fix it to the host in startup_nodes
            if len(cluster_slots) == 1 and len(self.startup_nodes) == 1:
                single_node_slots = cluster_slots.get(
                    (0, self.RedisClusterHashSlots - 1)
                )[0]
                if len(single_node_slots["host"]) == 0:
                    single_node_slots["host"] = self.startup_nodes[0]["host"]
                    single_node_slots["server_type"] = "master"

            # No need to decode response because StrictRedis should handle that for us...
            for min_slot, max_slot in cluster_slots:
                nodes = cluster_slots.get((min_slot, max_slot))
                master_node, slave_nodes = nodes[0], nodes[1:]

                if master_node["host"] == "":
                    master_node["host"] = node["host"]
                self.set_node_name(master_node)
                nodes_cache[master_node["name"]] = master_node

                for i in range(min_slot, max_slot + 1):
                    if i not in tmp_slots:
                        tmp_slots[i] = [master_node]

                        for slave_node in slave_nodes:
                            self.set_node_name(slave_node)
                            nodes_cache[slave_node["name"]] = slave_node
                            tmp_slots[i].append(slave_node)
                    else:
                        # Validate that 2 nodes want to use the same slot cache setup
                        if tmp_slots[i][0]["name"] != node["name"]:
                            disagreements.append(
                                "{0} vs {1} on slot: {2}".format(
                                    tmp_slots[i][0]["name"], node["name"], i
                                ),
                            )

                            if len(disagreements) > 5:
                                raise RedisClusterException(
                                    (
                                        "startup_nodes could not agree on a valid slots cache."
                                        f" {', '.join(disagreements)}"
                                    )
                                )

                self.populate_startup_nodes()
                self.refresh_table_asap = False

            if self._skip_full_coverage_check:
                need_full_slots_coverage = False
            else:
                need_full_slots_coverage = await self.cluster_require_full_coverage(
                    nodes_cache
                )

            # Validate if all slots are covered or if we should try next startup node
            for i in range(0, self.RedisClusterHashSlots):
                if i not in tmp_slots and need_full_slots_coverage:
                    all_slots_covered = False

            if all_slots_covered:
                # All slots are covered and application can continue to execute
                break

        if not startup_nodes_reachable:
            raise RedisClusterException(
                "Redis Cluster cannot be connected. "
                "Please provide at least one reachable node."
            )

        if not all_slots_covered:
            raise RedisClusterException(
                "Not all slots are covered after query all startup_nodes. "
                "{0} of {1} covered...".format(
                    len(tmp_slots), self.RedisClusterHashSlots
                )
            )

        # Set the tmp variables to the real variables
        self.slots = tmp_slots
        self.nodes = nodes_cache
        self.reinitialize_counter = 0

    async def increment_reinitialize_counter(self, ct=1):
        for i in range(1, ct):
            self.reinitialize_counter += 1
            if self.reinitialize_counter % self.reinitialize_steps == 0:
                await self.initialize()

    async def cluster_require_full_coverage(self, nodes_cache):
        """
        If exists 'cluster-require-full-coverage no' config on redis servers,
        then even all slots are not covered, cluster still will be able to
        respond
        """
        nodes = nodes_cache or self.nodes

        async def node_require_full_coverage(node):
            r_node = self.get_redis_link(host=node["host"], port=node["port"])
            node_config = await r_node.config_get("cluster-require-full-coverage")
            return "yes" in node_config.values()

        # at least one node should have cluster-require-full-coverage yes
        for node in nodes.values():
            if await node_require_full_coverage(node):
                return True
        return False

    def set_node_name(self, n):
        """
        Formats the name for the given node object

        # TODO: This shold not be constructed this way. It should update the name of the node in
        the node cache dict
        """
        if "name" not in n:
            n["name"] = "{0}:{1}".format(n["host"], n["port"])

    def set_node(self, host, port, server_type=None):
        """Updates data for a node"""
        node_name = "{0}:{1}".format(host, port)
        node = {
            "host": host,
            "port": port,
            "name": node_name,
            "server_type": server_type,
        }
        self.nodes[node_name] = node
        return node

    def populate_startup_nodes(self):
        """
        Do something with all startup nodes and filters out any duplicates
        """
        for item in self.startup_nodes:
            self.set_node_name(item)

        for n in self.nodes.values():
            if n not in self.startup_nodes:
                self.startup_nodes.append(n)

        # freeze it so we can set() it
        uniq = {frozenset(node.items()) for node in self.startup_nodes}
        # then thaw it back out into a list of dicts
        self.startup_nodes = [dict(node) for node in uniq]

    async def reset(self):
        """Drops all node data and start over from startup_nodes"""
        await self.initialize()
