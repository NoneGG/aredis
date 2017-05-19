#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
from aredis import StrictRedisCluster
from aredis.connection import ClusterConnection
from aredis.commands.cluster import parse_cluster_slots


async def example():
    cluster = StrictRedisCluster(startup_nodes=[{'host': '127.0.0.1', 'port': 7002}])
    print(await cluster.cluster_slots())
    """
    {(10923, 16383): [
    {'node_id': b'7263d083837d9ed872123c1703e5d0f60dfe5a0c', 'host': b'172.17.0.2', 'port': 7002, 'server_type': 'master'},
    {'node_id': b'301f61c9553823fe526e81e69b4c89da7dafd5e0', 'host': b'172.17.0.2', 'port': 7005, 'server_type': 'slave'}
    ],
    (5461, 10922): [
    {'node_id': b'f1f08a81f4afd4bb5daaa44d3701175f57728cbc', 'host': b'172.17.0.2', 'port': 7001, 'server_type': 'master'},
    {'node_id': b'9ce65b448234223a9c92ec9c442ca3f3aeeefeb0', 'host': b'172.17.0.2', 'port': 7004, 'server_type': 'slave'}
    ],
    (0, 5460): [
    {'node_id': b'7172e3c463b79ef11cceea0da9b2ca91f9b1bc93', 'host': b'172.17.0.2', 'port': 7000, 'server_type': 'master'},
    {'node_id': b'06ae04a0320ad4b3654f469b3ffa6646a31cd3cb', 'host': b'172.17.0.2', 'port': 7003, 'server_type': 'slave'}
    ]
    }
    """
    conn = ClusterConnection(host='127.0.0.1', port=7002)
    await conn.send_command('cluster slots')
    res = await conn.read_response()
    print(res)
    assert parse_cluster_slots(res) == await cluster.cluster_slots()
    """
    [
    [
    5461, 10922,
    [b'172.17.0.2', 7001, b'f1f08a81f4afd4bb5daaa44d3701175f57728cbc'],
    [b'172.17.0.2', 7004, b'9ce65b448234223a9c92ec9c442ca3f3aeeefeb0']
    ],
    [
    10923, 16383,
    [b'172.17.0.2', 7002, b'7263d083837d9ed872123c1703e5d0f60dfe5a0c'],
    [b'172.17.0.2', 7005, b'301f61c9553823fe526e81e69b4c89da7dafd5e0']
    ],
    [0, 5460,
    [b'172.17.0.2', 7000, b'7172e3c463b79ef11cceea0da9b2ca91f9b1bc93'],
    [b'172.17.0.2', 7003, b'06ae04a0320ad4b3654f469b3ffa6646a31cd3cb']
    ]
    ]
    """

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
