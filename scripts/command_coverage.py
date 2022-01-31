import datetime
import functools
import inspect
import os
import re
from typing import Any, List, Optional, Tuple, Union
try:
    from typing import Literal
except:
    from typing_extensions import Literal

import coredis
import inflect
import redis
import redis.cluster
import requests
from packaging import version

MAX_SUPPORTED_VERSION = version.parse("6.999.999")
MIN_SUPPORTED_VERSION = version.parse("5.0.0")

MAPPING = {"DEL": "delete"}
SKIP_SPEC = ["BITFIELD", "BITFIELD_RO"]

REDIS_ARGUMENT_TYPE_MAPPING = {
    "string": str,
    "pattern": str,
    "key": str,
    "integer": int,
    "double": float,
    "unix-time": Union[int, datetime.datetime],
    "pure-token": bool,
}
REDIS_ARGUMENT_NAME_OVERRIDES = {
    "BITPOS": {"end_index_index_unit": "end_index_unit"},
    "BITCOUNT": {"index_index_unit": "index_unit"},
}

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

VERSIONADDED_DOC = re.compile("(.. versionadded:: ([\d\.]+))")

inflection_engine = inflect.engine()

RESP = None

def get_commands():
    global RESP

    if not RESP:
        RESP = requests.get("https://redis.io/commands.json").json()

    return RESP

def get_official_commands(group=None):
    response = get_commands()
    by_group = {}
    [
        by_group.setdefault(command["group"], []).append({**command, **{"name": name}})

        for name, command in response.items()

        if version.parse(command["since"]) < MAX_SUPPORTED_VERSION
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


def redis_command_link(command):
    return (
        f'`{command} <https://redis.io/commands/{command.lower().replace(" ", "-")}>`_'
    )


def skip_command(command):
    # if command["name"] == "MIGRATE":
    #    return False
    # return True

    if (
        command["name"].find(" HELP") >= 0
        or command["summary"].find("container for") >= 0
    ):
        return True

    return False


def is_deprecated(command, kls):
    if (
        command.get("deprecated_since")
        and version.parse(command["deprecated_since"]) < MAX_SUPPORTED_VERSION
    ):
        replacement = command.get("replaced_by", "")
        replacement = re.sub("`(.*?)`", "``\\1``", replacement)
        replacement_method = re.search("(``(.*?)``)", replacement)

        replacement_method = replacement_method.group()

        if replacement_method:
            preferred_method = f"Use :meth:`~coredis.{kls.__name__}.{sanitized(replacement_method, None).replace('`','')}` "
            replacement = replacement.replace(replacement_method, preferred_method)

        return command["deprecated_since"], replacement


def sanitized(x, command=None):
    cleansed_name = x.lower().replace("-", "_").replace(":", "_")

    if command:
        override = REDIS_ARGUMENT_NAME_OVERRIDES.get(command["name"], {}).get(
            cleansed_name
        )

        if override:
            return override

    return cleansed_name


def skip_arg(argument):
    arg_version = argument.get("since")

    if arg_version and version.parse(
            arg_version
    ) > MAX_SUPPORTED_VERSION:
        return True

    return False


def get_type(arg):
    inferred_type = REDIS_ARGUMENT_TYPE_MAPPING.get(arg["type"], Any)

    if arg["name"] in ["seconds", "milliseconds"] and inferred_type == int:
        return Union[int, datetime.timedelta]

    return inferred_type


def get_type_annotation(arg):
    if arg["type"] == "oneof" and all(
        k["type"] == "pure-token" for k in arg["arguments"]
    ):
        tokens = ["'%s'" % s["token"] for s in arg["arguments"]]
        literal_type = eval(f"Literal[{','.join(tokens)}]")

        if arg.get("optional"):
            return Optional[literal_type]

        return literal_type
    else:
        return get_type(arg)


def get_argument(
    arg, parent, command, arg_type=inspect.Parameter.KEYWORD_ONLY, multiple=False
):
    if skip_arg(arg):
        return []
    param_list = []

    if arg["type"] == "block":
        if arg.get("multiple"):
            name = inflection_engine.plural(sanitized(arg["name"], command))
            child_types = [get_type(child) for child in arg["arguments"]]
            child_types_repr = ",".join(["%s" % k.__name__ for k in child_types])
            param_list.append(
                inspect.Parameter(
                    name,
                    arg_type,
                    annotation=List[eval(f"Tuple[{child_types_repr}]")],
                )
            )

        else:
            for child in arg["arguments"]:
                param_list.extend(
                    get_argument(child, arg, command, arg_type, arg.get("multiple"))
                )
    elif arg["type"] == "oneof":
        if all(child["type"] == "pure-token" for child in arg["arguments"]):
            if parent:
                syn_name = sanitized(f"{parent['name']}_{arg.get('name')}", command)
            else:
                syn_name = sanitized(f"{arg.get('name')}", command)

            param_list.append(
                inspect.Parameter(
                    syn_name,
                    arg_type,
                    annotation=get_type_annotation(arg),
                )
            )
        else:
            for child in arg["arguments"]:
                param_list.extend(get_argument(child, arg, command, arg_type, multiple))
    else:
        name = sanitized(
            arg.get("token", arg["name"])

            if not arg.get("type") == "pure-token"
            else arg["name"],
            command,
        )
        is_variadic = False
        type_annotation = get_type_annotation(arg)

        if multiple:
            name = inflection_engine.plural(name)

            if not inflection_engine.singular_noun(name):
                name = inflection_engine.plural(name)
            is_variadic = not arg.get("optional")

            if not is_variadic:
                type_annotation = Optional[List[type_annotation]]
            else:
                arg_type = inspect.Parameter.VAR_POSITIONAL
        param_list.append(inspect.Parameter(name, arg_type, annotation=type_annotation))

    return param_list


def get_command_spec(command):
    arguments = command.get("arguments", [])
    recommended_signature = []

    for k in arguments:
        if not k.get("optional") and not k.get("multiple"):
            recommended_signature.extend(
                get_argument(k, None, command, inspect.Parameter.POSITIONAL_ONLY)
            )

    for k in arguments:
        if not k.get("optional") and k.get("multiple"):
            recommended_signature.extend(
                get_argument(k, None, command, inspect.Parameter.POSITIONAL_ONLY, True)
            )

    for k in arguments:
        if k.get("optional") and k.get("multiple"):
            recommended_signature.extend(
                get_argument(k, None, command, inspect.Parameter.KEYWORD_ONLY, True)
            )

    for k in [k for k in arguments if (k.get("optional") and not k.get("multiple"))]:
        if skip_arg(k):
            continue
        recommended_signature.extend(get_argument(k, None, command))

    return recommended_signature


def generate_compatibility_section(
    section, kls, sync_kls, redis_namespace, groups, debug=False
):
    doc = f"{section}\n"
    doc += f"{len(section)*'^'}\n"
    doc += "\n"

    for group in groups:
        doc += f"{group.title()}\n"
        doc += f"{len(group)*'-'}\n"
        doc += "\n"
        doc += f".. list-table::\n"
        doc += "    :header-rows: 1\n"
        doc += "    :class: command-table\n"
        doc += "\n"

        doc += """
    * - Redis Command
      - Compatibility"""
        if debug:
            doc += "\n      - Recommendations\n"
        doc += "\n"
        supported = []
        needs_porting = []
        missing = []

        for method in get_official_commands(group):
            if skip_command(method):
                continue
            name = MAPPING.get(
                method["name"],
                method["name"].lower().replace(" ", "_").replace("-", "_"),
            )
            located = find_method(kls, name)
            sync_located = find_method(sync_kls, name)
            redis_version_introduced = version.parse(method["since"])
            summary = method["summary"]

            if not method["name"] in SKIP_SPEC:
                rec_params = get_command_spec(method)
                try:
                    rec_signature = inspect.Signature(
                        [inspect.Parameter("self", inspect.Parameter.POSITIONAL_ONLY)]
                        + rec_params
                    )
                except:
                    print(method["name"], rec_params)
                    raise

            server_new_in = ""
            server_deprecated = ""
            recommended_replacement = ""

            deprecation_info = is_deprecated(method, kls)
            if deprecation_info:
                server_deprecated = f"☠️ Deprecated in redis: {deprecation_info[0]}."

                if deprecation_info[1]:
                    recommended_replacement = deprecation_info[1]

            if redis_version_introduced > MIN_SUPPORTED_VERSION:
                server_new_in = f"🎉 New in redis: {method['since']}"

            if located:
                version_added = VERSIONADDED_DOC.findall(located.__doc__)
                version_added = (version_added and version_added[0][0]) or ""
                version_added.strip()

                if not method["name"] in SKIP_SPEC:
                    current_signature = [
                        k for k in inspect.signature(located).parameters
                    ]

                    if sorted(current_signature) == sorted(
                        [k for k in rec_signature.parameters]
                    ):
                        recommendation = "- 👍"
                    else:
                        diff_minus = [
                            str(k)

                            for k, v in rec_signature.parameters.items()

                            if k not in current_signature
                        ]
                        diff_plus = [
                            str(k)

                            for k in current_signature

                            if k not in rec_signature.parameters
                        ]
                        recommendation = str(rec_signature)
                        recommendation = f"""- Current Signature:

        .. method:: {name}{inspect.signature(located)}
           :noindex:

        Recommended Signature:

        .. method:: {name}{recommendation}
           :noindex:

                     """
                        recommendation += f"\n\n{' '*8}\+ ``({','.join(diff_plus)})`` |  - ``({','.join(diff_minus)})``\n"
                else:
                    recommendation = f"""- Current Signature:

        .. method:: {name}{inspect.signature(located)}
           :noindex:

        Recommendation: 🤷
          """
                supported.append(
                    f"""
    * - {redis_command_link(method['name'])}

        {summary}
      - :meth:`~coredis.{kls.__name__}.{located.__name__}`

        {version_added and ("- " + version_added)}
        {server_deprecated and ("- " + server_deprecated)}
        {recommended_replacement and ("- " + recommended_replacement)}
        {server_new_in and ("- " + server_new_in)}


      {recommendation.strip() if debug else ""}
            """
                )
            elif sync_located and not is_deprecated(method, kls):
                recommendation = f"""- Recommended Signature:

        .. method:: {name}{str(rec_signature)}
           :noindex:
                """
                needs_porting.append(
                    f"""
    * - {redis_command_link(method['name'])}

        {summary}
      - Not Implemented

        redis-py reference: :meth:`~{redis_namespace}.{name}`
        {server_deprecated or ''}
        {server_new_in or ''}
      {recommendation if debug else ""}
                    """
                )
            elif not is_deprecated(method, kls):
                recommendation = f"""- Recommended Signature:

        .. method:: {name}{str(rec_signature)}
           :noindex:
           """
                missing.append(
                    f"""
    * - {redis_command_link(method['name'])}

        {summary}
      - Not Implemented.

        {server_new_in or ''}
        {server_deprecated or ''}
      {recommendation if debug else ""}
       """
                )
        doc += "\n".join(supported + needs_porting + missing)
        doc += "\n\n"
    return doc


if __name__ == "__main__":
    print("Command compatibility")
    print("=====================")

    # Strict Redis client
    kls = coredis.StrictRedis
    sync_kls = redis.StrictRedis
    print(
        generate_compatibility_section(
            "Redis Client",
            kls,
            sync_kls,
            "redis.commands.core.CoreCommands",
            STD_GROUPS + ["server", "connection"],
            debug=os.environ.get("DEBUG"),
        )
    )

    # Cluster client
    cluster_kls = coredis.StrictRedisCluster
    sync_cluster_kls = redis.cluster.RedisCluster
    print(
        generate_compatibility_section(
            "Redis Cluster Client",
            cluster_kls,
            sync_cluster_kls,
            "redis.commands.cluster.RedisClusterCommands",
            STD_GROUPS + ["cluster"],
            debug=os.environ.get("DEBUG"),
        )
    )
