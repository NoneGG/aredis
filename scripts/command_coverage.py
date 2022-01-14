import functools
import inspect

import coredis
import redis
import redis.cluster
import requests


@functools.cache
def get_official_commands(group=None):
    response = requests.get("https://redis.io/commands.json").json()
    by_group = {}
    [
        by_group.setdefault(command["group"], []).append(command | {"name": name})
        for name, command in response.items()
    ]

    return by_group if not group else by_group.get(group)


def find_method(kls, command_name):
    members = inspect.getmembers(kls)
    mapping = {
        k[0]: k[1]
        for k in members
        if inspect.ismethod(k[1]) or inspect.isfunction(k[1])
    }

    return mapping.get(command_name)


STD_GROUPS = [
    "string",
    "bitmap",
    "list",
    "sorted-set",
    "generic",
    "transactions",
    "scripting",
    "geo",
    "hash",
    "hyperloglog",
    "pubsub",
    "set",
    "stream",
]


def redis_command_link(command):
    return (
        f'`{command} <https://redis.io/commands/{command.lower().replace(" ", "-")}>`_'
    )


def generate_compatibility_section(section, kls, sync_kls, groups):
    doc = f"{section}\n"
    doc += f"{len(section)*'^'}\n"
    doc += "\n"

    for group in groups:
        doc += f"{group.title()}\n"
        doc += f"{len(group)*'-'}\n"
        doc += "\n"
        doc += f".. list-table::\n"
        doc += "    :class: command-table\n"
        doc += "\n"

        supported = []
        needs_porting = []
        missing = []

        for method in get_official_commands(group):
            name = method["name"].lower().replace(" ", "_")
            located = find_method(kls, name)
            sync_located = find_method(sync_kls, name)

            if located:
                supported.append(
                    f"    * - {redis_command_link(method['name'])}\n      - :meth:`~coredis.{kls.__name__}.{name}`"
                )
            elif sync_located:
                needs_porting.append(
                    f"    * - {redis_command_link(method['name'])}\n      - Needs porting from: :meth:`{sync_kls.__name__}.{name}`"
                )
            elif sync_located:
                missing.append(
                    f"    * - {redis_command_link(method['name'])}\n      - Not Implemented"
                )
        doc += "\n".join(supported + needs_porting + missing)
        doc += "\n"

    return doc


print("Command compatibilty")
print("==========================")

# Strict Redis client
kls = coredis.StrictRedis
sync_kls = redis.StrictRedis
print(
    generate_compatibility_section(
        "Redis", kls, sync_kls, STD_GROUPS + ["server", "connection"]
    )
)


# Cluster client
cluster_kls = coredis.StrictRedisCluster
sync_cluster_kls = redis.cluster.RedisCluster
print(
    generate_compatibility_section(
        "Redis Cluster", cluster_kls, sync_cluster_kls, STD_GROUPS + ["cluster"]
    )
)
