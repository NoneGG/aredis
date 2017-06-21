from aredis.utils import (bool_ok,
                          nativestr,
                          NodeFlag,
                          list_keys_to_dict,
                          dict_merge)
from aredis.exceptions import (RedisError,
                               ClusterError)


def parse_cluster_info(response, **options):
    response = nativestr(response)
    return dict([line.split(':') for line in response.splitlines() if line])


def parse_cluster_nodes(resp, **options):
    """
    @see: http://redis.io/commands/cluster-nodes  # string
    @see: http://redis.io/commands/cluster-slaves # list of string
    """
    resp = nativestr(resp)
    current_host = options.get('current_host', '')

    def parse_slots(s):
        slots, migrations = [], []
        for r in s.split(' '):
            if '->-' in r:
                slot_id, dst_node_id = r[1:-1].split('->-', 1)
                migrations.append({
                    'slot': int(slot_id),
                    'node_id': dst_node_id,
                    'state': 'migrating'
                })
            elif '-<-' in r:
                slot_id, src_node_id = r[1:-1].split('-<-', 1)
                migrations.append({
                    'slot': int(slot_id),
                    'node_id': src_node_id,
                    'state': 'importing'
                })
            elif '-' in r:
                start, end = r.split('-')
                slots.extend(range(int(start), int(end) + 1))
            else:
                slots.append(int(r))

        return slots, migrations

    if isinstance(resp, str):
        resp = resp.splitlines()

    nodes = []
    for line in resp:
        parts = line.split(' ', 8)
        self_id, addr, flags, master_id, ping_sent, \
            pong_recv, config_epoch, link_state = parts[:8]

        host, port = addr.rsplit(':', 1)

        node = {
            'id': self_id,
            'host': host or current_host,
            'port': int(port),
            'flags': tuple(flags.split(',')),
            'master': master_id if master_id != '-' else None,
            'ping-sent': int(ping_sent),
            'pong-recv': int(pong_recv),
            'link-state': link_state,
            'slots': [],
            'migrations': [],
        }

        if len(parts) >= 9:
            slots, migrations = parse_slots(parts[8])
            node['slots'], node['migrations'] = tuple(slots), migrations

        nodes.append(node)

    return nodes


def parse_cluster_slots(response):
    res = dict()
    for slot_info in response:
        min_slot, max_slot = slot_info[:2]
        nodes = slot_info[2:]
        parse_node = lambda node: {
            'host': node[0],
            'port': node[1],
            'node_id': node[2] if len(node) > 2 else '',
            'server_type': 'slave'
        }
        res[(min_slot, max_slot)] = [parse_node(node) for node in nodes]
        res[(min_slot, max_slot)][0]['server_type'] = 'master'
    return res



class ClusterCommandMixin:

    NODES_FLAGS = dict_merge({
        'CLUSTER INFO': NodeFlag.ALL_NODES,
        'CLUSTER COUNTKEYSINSLOT': NodeFlag.SLOT_ID
    },
    list_keys_to_dict(
        ['CLUSTER NODES', 'CLUSTER SLOTS'], NodeFlag.RANDOM
    )
    )

    RESPONSE_CALLBACKS = {
        'CLUSTER ADDSLOTS': bool_ok,
        'CLUSTER COUNT-FAILURE-REPORTS': lambda x: int(x),
        'CLUSTER COUNTKEYSINSLOT': lambda x: int(x),
        'CLUSTER DELSLOTS': bool_ok,
        'CLUSTER FAILOVER': bool_ok,
        'CLUSTER FORGET': bool_ok,
        'CLUSTER INFO': parse_cluster_info,
        'CLUSTER KEYSLOT': lambda x: int(x),
        'CLUSTER MEET': bool_ok,
        'CLUSTER NODES': parse_cluster_nodes,
        'CLUSTER REPLICATE': bool_ok,
        'CLUSTER RESET': bool_ok,
        'CLUSTER SAVECONFIG': bool_ok,
        'CLUSTER SET-CONFIG-EPOCH': bool_ok,
        'CLUSTER SETSLOT': bool_ok,
        'CLUSTER SLAVES': parse_cluster_nodes,
        'CLUSTER SLOTS': parse_cluster_slots,
        'ASKING': bool_ok,
        'READONLY': bool_ok,
        'READWRITE': bool_ok,
    }

    RESULT_CALLBACKS = dict_merge(
        list_keys_to_dict(
            ['CLUSTER INFO', 'CLUSTER ADDSLOTS', 'CLUSTER COUNT-FAILURE-REPORTS',
            'CLUSTER DELSLOTS', 'CLUSTER FAILOVER', 'CLUSTER FORGET'], None
        )
    )

    def _nodes_slots_to_slots_nodes(self, mapping):
        """
        Converts a mapping of
        {id: <node>, slots: (slot1, slot2)}
        to
        {slot1: <node>, slot2: <node>}

        Operation is expensive so use with caution
        """
        out = {}
        for node in mapping:
            for slot in node['slots']:
                out[str(slot)] = node['id']
        return out

    async def cluster_addslots(self, node_id, *slots):
        """
        Assign new hash slots to receiving node

        Sends to specefied node
        """
        return await self.execute_command('CLUSTER ADDSLOTS', *slots, node_id=node_id)

    async def cluster_count_failure_report(self, node_id=''):
        """
        Return the number of failure reports active for a given node

        Sends to specefied node
        """
        return await self.execute_command('CLUSTER COUNT-FAILURE-REPORTS', node_id=node_id)

    async def cluster_countkeysinslot(self, slot_id):
        """
        Return the number of local keys in the specified hash slot

        Send to node based on specefied slot_id
        """
        return await self.execute_command('CLUSTER COUNTKEYSINSLOT', slot_id)

    async def cluster_delslots(self, *slots):
        """
        Set hash slots as unbound in the cluster.
        It determines by it self what node the slot is in and sends it there

        Returns a list of the results for each processed slot.
        """
        cluster_nodes = self._nodes_slots_to_slots_nodes(await self.cluster_nodes())
        res = list()
        for slot in slots:
            res.append(await self.execute_command('CLUSTER DELSLOTS', slot, node_id=cluster_nodes[slot]))
        return res

    async def cluster_failover(self, node_id, option):
        """
        Forces a slave to perform a manual failover of its master

        Sends to specefied node
        """
        if not isinstance(option, str) or option.upper() not in {'FORCE', 'TAKEOVER'}:
            raise ClusterError('Wrong option provided')
        return await self.execute_command('CLUSTER FAILOVER', option, node_id=node_id)

    # todo
    async def cluster_forget(self, node_id):
        """
        remove a node via its node ID from the set of known nodes
        of the Redis Cluster node receiving the command

        Sends to all nodes in the cluster
        """
        pass

    async def cluster_info(self):
        """
        Provides info about Redis Cluster node state

        Sends to random node in the cluster
        """
        return await self.execute_command('CLUSTER INFO')

    async def cluster_keyslot(self, name):
        """
        Returns the hash slot of the specified key

        Sends to random node in the cluster
        """
        return await self.execute_command('CLUSTER KEYSLOT', name)

    async def cluster_meet(self, node_id, host, port):
        """
        Force a node cluster to handshake with another node.

        Sends to specefied node
        """
        return await self.execute_command('CLUSTER MEET', host, port, node_id=node_id)

    async def cluster_nodes(self):
        """
        Force a node cluster to handshake with another node

        Sends to random node in the cluster
        """
        return await self.execute_command('CLUSTER NODES')

    async def cluster_replicate(self, target_node_id):
        """
        Reconfigure a node as a slave of the specified master node

        Sends to specefied node
        """
        return await self.execute_command('CLUSTER REPLICATE', target_node_id)

    async def cluster_reset(self, node_id, soft=True):
        """
        Reset a Redis Cluster node

        If 'soft' is True then it will send 'SOFT' argument
        If 'soft' is False then it will send 'HARD' argument

        Sends to specefied node
        """
        option = 'SOFT' if soft else 'HARD'
        return await self.execute_command('CLUSTER RESET', option, node_id=node_id)

    async def cluster_reset_all_nodes(self, soft=True):
        """
        Send CLUSTER RESET to all nodes in the cluster

        If 'soft' is True then it will send 'SOFT' argument
        If 'soft' is False then it will send 'HARD' argument

        Sends to all nodes in the cluster
        """
        option = 'SOFT' if soft else 'HARD'
        res = list()
        for node in await self.cluster_nodes():
            res.append(
                await self.execute_command(
                    'CLUSTER RESET', option, node_id=node['id']
                ))
        return res

    async def cluster_save_config(self):
        """
        Forces the node to save cluster state on disk

        Sends to all nodes in the cluster
        """
        return await self.execute_command('CLUSTER SAVECONFIG')

    async def cluster_set_config_epoch(self, node_id, epoch):
        """
        Set the configuration epoch in a new node

        Sends to specefied node
        """
        return await self.execute_command('CLUSTER SET-CONFIG-EPOCH', epoch, node_id=node_id)


    async def cluster_setslot(self, node_id, slot_id, state):
        """
        Bind an hash slot to a specific node

        Sends to specified node
        """
        if state.upper() in {'IMPORTING', 'MIGRATING', 'NODE'} and node_id is not None:
            return await self.execute_command('CLUSTER SETSLOT', slot_id, state, node_id)
        elif state.upper() == 'STABLE':
            return await self.execute_command('CLUSTER SETSLOT', slot_id, 'STABLE')
        else:
            raise RedisError('Invalid slot state: {0}'.format(state))

    async def cluster_get_keys_in_slot(self, slot_id, count):
        """
        Return local key names in the specified hash slot
        Sends to specified node
        """
        return await self.execute_command('CLUSTER GETKEYSINSLOT', slot_id, count)

    async def cluster_slaves(self, target_node_id):
        """
        Force a node cluster to handshake with another node

        Sends to targeted cluster node
        """
        return await self.execute_command('CLUSTER SLAVES', target_node_id)

    async def cluster_slots(self):
        """
        Get array of Cluster slot to node mappings

        Sends to random node in the cluster
        """
        return await self.execute_command('CLUSTER SLOTS')
