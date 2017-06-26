#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
import logging
from aredis import StrictRedisCluster


async def example():
    cluster = StrictRedisCluster(startup_nodes=[{'host': '127.0.0.1', 'port': 7001}])
    slots = await cluster.cluster_slots()
    master_node = slots[(5461, 10922)][0]['node_id']
    slave_node = slots[(5461, 10922)][1]['node_id']
    print('master: {}'.format(master_node))
    print('slave: {}'.format(slave_node))
    print('nodes: {}'.format(await cluster.cluster_info()))
    for time in range(2):
        # forget a node twice to see if error will be raised
        try:
            await cluster.cluster_forget(master_node)
        except Exception as exc:
            logging.error(exc)
    slots = await cluster.cluster_slots()
    print(slots[(5461, 10922)])


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
