#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
from aredis import StrictRedisCluster
from aredis.connection import ClusterConnection
from aredis.commands.cluster import parse_cluster_slots


async def example():
    cluster = StrictRedisCluster(startup_nodes=[{'host': '127.0.0.1', 'port': 7002}])
    slots = await cluster.cluster_slots()
    master_node = slots[(10923, 16383)][0]['node_id']
    slave_node = slots[(10923, 16383)][1]['node_id']
    print('master: {}'.format(master_node))
    print('slave: {}'.format(slave_node))
    await cluster.cluster_forget(master_node)
    slots = await cluster.cluster_slots()
    print(slots[(10923, 16383)])


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
