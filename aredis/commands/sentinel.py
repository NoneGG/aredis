import warnings
from aredis.utils import (dict_merge,
                          list_keys_to_dict,
                          NodeFlag, bool_ok)


SENTINEL_STATE_TYPES = {
    'can-failover-its-master': int,
    'config-epoch': int,
    'down-after-milliseconds': int,
    'failover-timeout': int,
    'info-refresh': int,
    'last-hello-message': int,
    'last-ok-ping-reply': int,
    'last-ping-reply': int,
    'last-ping-sent': int,
    'master-link-down-time': int,
    'master-port': int,
    'num-other-sentinels': int,
    'num-slaves': int,
    'o-down-time': int,
    'pending-commands': int,
    'parallel-syncs': int,
    'port': int,
    'quorum': int,
    'role-reported-time': int,
    's-down-time': int,
    'slave-priority': int,
    'slave-repl-offset': int,
    'voted-leader-epoch': int
}


def pairs_to_dict_typed(response, type_info):
    it = iter(response)
    result = {}
    for key, value in zip(it, it):
        if key in type_info:
            try:
                value = type_info[key](value)
            except:
                # if for some reason the value can't be coerced, just use
                # the string value
                pass
        result[key] = value
    return result


def parse_sentinel_state(item):
    result = pairs_to_dict_typed(item, SENTINEL_STATE_TYPES)
    flags = set(result['flags'].split(','))
    for name, flag in (('is_master', 'master'), ('is_slave', 'slave'),
                       ('is_sdown', 's_down'), ('is_odown', 'o_down'),
                       ('is_sentinel', 'sentinel'),
                       ('is_disconnected', 'disconnected'),
                       ('is_master_down', 'master_down')):
        result[name] = flag in flags
    return result


def parse_sentinel_master(response):
    return parse_sentinel_state(map(str, response))


def parse_sentinel_masters(response):
    result = {}
    for item in response:
        state = parse_sentinel_state(map(str, item))
        result[state['name']] = state
    return result


def parse_sentinel_slaves_and_sentinels(response):
    return [parse_sentinel_state(map(str, item)) for item in response]


def parse_sentinel_get_master(response):
    return response and (response[0], int(response[1])) or None


class SentinelCommandMixin:

    RESPONSE_CALLBACKS = {
        'SENTINEL GET-MASTER-ADDR-BY-NAME': parse_sentinel_get_master,
        'SENTINEL MASTER': parse_sentinel_master,
        'SENTINEL MASTERS': parse_sentinel_masters,
        'SENTINEL MONITOR': bool_ok,
        'SENTINEL REMOVE': bool_ok,
        'SENTINEL SENTINELS': parse_sentinel_slaves_and_sentinels,
        'SENTINEL SET': bool_ok,
        'SENTINEL SLAVES': parse_sentinel_slaves_and_sentinels,
    }

    async def sentinel(self, *args):
        "Redis Sentinel's SENTINEL command."
        warnings.warn(DeprecationWarning('Use the individual sentinel_* methods'))

    async def sentinel_get_master_addr_by_name(self, service_name):
        "Returns a (host, port) pair for the given ``service_name``"
        return await self.execute_command('SENTINEL GET-MASTER-ADDR-BY-NAME',
                                          service_name)

    async def sentinel_master(self, service_name):
        "Returns a dictionary containing the specified masters state."
        return await self.execute_command('SENTINEL MASTER', service_name)

    async def sentinel_masters(self):
        "Returns a list of dictionaries containing each master's state."
        return await self.execute_command('SENTINEL MASTERS')

    async def sentinel_monitor(self, name, ip, port, quorum):
        "Add a new master to Sentinel to be monitored"
        return await self.execute_command('SENTINEL MONITOR', name, ip, port, quorum)

    async def sentinel_remove(self, name):
        "Remove a master from Sentinel's monitoring"
        return await self.execute_command('SENTINEL REMOVE', name)

    async def sentinel_sentinels(self, service_name):
        "Returns a list of sentinels for ``service_name``"
        return await self.execute_command('SENTINEL SENTINELS', service_name)

    async def sentinel_set(self, name, option, value):
        "Set Sentinel monitoring parameters for a given master"
        return await self.execute_command('SENTINEL SET', name, option, value)

    async def sentinel_slaves(self, service_name):
        "Returns a list of slaves for ``service_name``"
        return await self.execute_command('SENTINEL SLAVES', service_name)


class ClusterSentinelCommands(SentinelCommandMixin):

    NODES_FLAGS = dict_merge(
        list_keys_to_dict(
            ["SENTINEL GET-MASTER-ADDR-BY-NAME", 'SENTINEL MASTER', 'SENTINEL MASTERS',
            'SENTINEL MONITOR', 'SENTINEL REMOVE', 'SENTINEL SENTINELS', 'SENTINEL SET',
            'SENTINEL SLAVES'], NodeFlag.BLOCKED
        )
    )
