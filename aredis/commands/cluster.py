from aredis.utils import bool_ok


def parse_cluster_info(response, **options):
    response = response.decode()
    return dict([line.split(':') for line in response.splitlines() if line])


def _parse_node_line(line):
    line_items = line.split(' ')
    node_id, addr, flags, master_id, ping, pong, epoch, \
        connected = line.split(' ')[:8]
    slots = [sl.split('-') for sl in line_items[8:]]
    node_dict = {
        'node_id': node_id,
        'flags': flags,
        'master_id': master_id,
        'last_ping_sent': ping,
        'last_pong_rcvd': pong,
        'epoch': epoch,
        'slots': slots,
        'connected': True if connected == 'connected' else False
    }
    return addr, node_dict


def parse_cluster_nodes(response, **options):
    raw_lines = response.decode()
    if isinstance(raw_lines, str):
        raw_lines = raw_lines.splitlines()
    return dict([_parse_node_line(line) for line in raw_lines])


class ClusterCommandMixin:

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
    }

    async def cluster(self, cluster_arg, *args):
        return await self.execute_command('CLUSTER {}'.format(cluster_arg.upper()), *args)
