import collections
import datetime
import functools
import inspect
import os
import re
import typing  # noqa

from typing import (
    Any,
    AnyStr,
    Dict,
    Iterable,
    List,
    Literal,  # noqa
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import click
import inflect
import requests
from jinja2 import Environment
from packaging import version

import coredis
from coredis.response.callbacks.cluster import ClusterNode
from coredis.response.types import (
    ClientInfo,
    Command,
    GeoCoordinates,
    GeoSearchResult,
    LCSMatch,
    LCSResult,
    RoleInfo,
    ScoredMember,
    ScoredMembers,
    SlowLogInfo,
    StreamEntry,
    StreamInfo,
    StreamPending,
    StreamPendingExt, LibraryDefinition,
)
from coredis.typing import OrderedDict, ValueT, KeyT, StringT
from coredis import PureToken, NodeFlag  # noqa

MAX_SUPPORTED_VERSION = version.parse("7.999.999")
MIN_SUPPORTED_VERSION = version.parse("5.0.0")

MAPPING = {"DEL": "delete"}
SKIP_SPEC = ["BITFIELD", "BITFIELD_RO"]
SKIP_COMMANDS = [
    "REPLCONF",
    "PFDEBUG",
    "PFSELFTEST",
    "PSYNC",
    "RESTORE-ASKING",
    "SYNC",
    "XSETID",
]

REDIS_ARGUMENT_TYPE_MAPPING = {
    "array": Sequence,
    "simple-string": StringT,
    "bulk-string": StringT,
    "string": StringT,
    "pattern": StringT,
    "key": KeyT,
    "integer": int,
    "double": Union[int, float],
    "unix-time": Union[int, datetime.datetime],
    "pure-token": bool,
}
REDIS_RETURN_ARGUMENT_TYPE_MAPPING = {
    **REDIS_ARGUMENT_TYPE_MAPPING,
    **{
        "simple-string": AnyStr,
        "bulk-string": AnyStr,
        "string": AnyStr,
        "array": Tuple,
        "double": Union[int, float],
        "unix-time": datetime.datetime,
        "pure-token": bool,
    },
}
REDIS_ARGUMENT_NAME_OVERRIDES = {
    "BITPOS": {"end_index_index_unit": "end_index_unit"},
    "BITCOUNT": {"index_index_unit": "index_unit"},
    "CLIENT REPLY": {"on_off_skip": "mode"},
    "GEOSEARCH": {"bybox": "width", "byradius": "radius", "frommember": "member"},
    "GEOSEARCHSTORE": {"bybox": "width", "byradius": "radius", "frommember": "member"},
    "SORT": {"sorting": "alpha"},
    "SORT_RO": {"sorting": "alpha"},
    "SCRIPT FLUSH": {"async": "sync_type"},
    "ZADD": {"score_member": "member_score"},
}
REDIS_ARGUMENT_TYPE_OVERRIDES = {
    "CLIENT KILL": {"skipme": bool},
    "COMMAND GETKEYS": {"arguments": ValueT},
    "FUNCTION RESTORE": {"serialized_value": bytes},
    "MSET": {"key_values": Dict[KeyT, ValueT]},
    "MSETNX": {"key_values": Dict[KeyT, ValueT]},
    "HMSET": {"field_values": Dict[StringT, ValueT]},
    "HSET": {"field_values": Dict[StringT, ValueT]},
    "MIGRATE": {"port": int},
    "RESTORE": {"serialized_value": bytes},
    "SORT": {"gets": KeyT},
    "SORT_RO": {"gets": KeyT},
    "XADD": {"field_values": Dict[StringT, ValueT], "threshold": Optional[int]},
    "XAUTOCLAIM": {"min_idle_time": Union[int, datetime.timedelta]},
    "XCLAIM": {"min_idle_time": Union[int, datetime.timedelta]},
    "XREAD": {"streams": Dict[ValueT, ValueT]},
    "XREADGROUP": {"streams": Dict[ValueT, ValueT]},
    "XTRIM": {"threshold": int},
    "ZADD": {"member_scores": Dict[StringT, float]},
    "ZCOUNT": {"min": Union[ValueT, float], "max": Union[ValueT, float]},
    "ZREVRANGE": {"min": Union[int, ValueT], "max": Union[int, ValueT]},
    "ZRANGE": {"min": Union[int, ValueT], "max": Union[int, ValueT]},
    "ZRANGESTORE": {"min": Union[int, ValueT], "max": Union[int, ValueT]},
}
IGNORED_ARGUMENTS = {
    "FCALL": ["numkeys"],
    "FCALL_RO": ["numkeys"],
    "LMPOP": ["numkeys"],
    "BLMPOP": ["numkeys"],
    "BZMPOP": ["numkeys"],
    "EVAL": ["numkeys"],
    "EVAL_RO": ["numkeys"],
    "EVALSHA": ["numkeys"],
    "EVALSHA_RO": ["numkeys"],
    "MIGRATE": ["key_or_empty_string"],
    "SINTERCARD": ["numkeys"],
    "ZDIFF": ["numkeys"],
    "ZDIFFSTORE": ["numkeys"],
    "ZINTER": ["numkeys"],
    "ZINTERCARD": ["numkeys"],
    "ZINTERSTORE": ["numkeys"],
    "ZMPOP": ["numkeys"],
    "ZUNION": ["numkeys"],
    "ZUNIONSTORE": ["numkeys"],
    "XADD": ["auto_id"],
    "XGROUP CREATE": ["new_id"],
    "XGROUP SETID": ["new_id"],
}
REDIS_RETURN_OVERRIDES = {
    "ACL USERS": Tuple[AnyStr, ...],
    "ACL GETUSER": Dict[AnyStr, List[AnyStr]],
    "ACL LIST": Tuple[AnyStr, ...],
    "ACL LOG": Union[Tuple[Dict[AnyStr, AnyStr], ...], bool],
    "BGREWRITEAOF": bool,
    "BGSAVE": bool,
    "BZPOPMAX": Optional[Tuple[AnyStr, AnyStr, float]],
    "BZPOPMIN": Optional[Tuple[AnyStr, AnyStr, float]],
    "BZMPOP": Optional[Tuple[AnyStr, ScoredMembers]],
    "CLIENT LIST": Tuple[ClientInfo, ...],
    "CLIENT INFO": ClientInfo,
    "CLIENT TRACKINGINFO": Dict[AnyStr, AnyStr],
    "CLUSTER INFO": Dict[str, str],
    "CLUSTER NODES": List[Dict[str, str]],
    "CLUSTER REPLICAS": List[Dict[AnyStr, AnyStr]],
    "CLUSTER SLAVES": List[Dict[AnyStr, AnyStr]],
    "CLUSTER SLOTS": Dict[Tuple[int, int], Tuple[ClusterNode, ...]],
    "COMMAND": Dict[AnyStr, Command],
    "COMMAND INFO": Dict[AnyStr, Command],
    "CONFIG GET": Dict[AnyStr, AnyStr],
    "COPY": bool,
    "DUMP": bytes,
    "EXPIRE": bool,
    "EXPIREAT": bool,
    "EXPIRETIME": datetime.datetime,
    "FUNCTION DUMP": bytes,
    "FUNCTION STATS": Dict[AnyStr, Union[AnyStr, Dict]],
    "FUNCTION LIST": Dict[AnyStr, LibraryDefinition],
    "GEODIST": Optional[float],
    "GEOPOS": Tuple[Optional[GeoCoordinates], ...],
    "GEOSEARCH": Union[int, Tuple[Union[AnyStr, GeoSearchResult], ...]],
    "GEORADIUSBYMEMBER": Union[int, Tuple[Union[AnyStr, GeoSearchResult], ...]],
    "GEORADIUS": Union[int, Tuple[Union[AnyStr, GeoSearchResult], ...]],
    "HELLO": Dict[AnyStr, AnyStr],
    "HINCRBYFLOAT": float,
    "HRANDFIELD": Union[AnyStr, Tuple[AnyStr, ...], Dict[AnyStr, AnyStr]],
    "HSCAN": Tuple[int, Dict[AnyStr, AnyStr]],
    "INCRBYFLOAT": float,
    "INFO": Dict[AnyStr, AnyStr],
    "KEYS": Set[AnyStr],
    "LASTSAVE": datetime.datetime,
    "LATENCY LATEST": Dict[AnyStr, Tuple[int, int, int]],
    "LCS": Union[AnyStr, int, LCSResult],
    "LPOS": Optional[Union[int, List[int]]],
    "MEMORY STATS": Dict[AnyStr, Union[AnyStr, int, float]],
    "MGET": Tuple[Optional[AnyStr], ...],
    "MSETNX": bool,
    "PFADD": bool,
    "PERSIST": bool,
    "PSETEX": bool,
    "PEXPIRETIME": datetime.datetime,
    "PUBSUB NUMSUB": OrderedDict[AnyStr, int],
    "RPOPLPUSH": Optional[AnyStr],
    "RESET": None,
    "ROLE": RoleInfo,
    "SCAN": Tuple[int, Tuple[AnyStr, ...]],
    "SMISMEMBER": Tuple[bool, ...],
    "SCRIPT FLUSH": bool,
    "SCRIPT KILL": bool,
    "SCRIPT EXISTS": Tuple[bool, ...],
    "SLOWLOG GET": Tuple[SlowLogInfo, ...],
    "SSCAN": Tuple[int, Set[AnyStr]],
    "TIME": datetime.datetime,
    "XCLAIM": Union[Tuple[AnyStr, ...], Tuple[StreamEntry, ...]],
    "XAUTOCLAIM": Union[
        Tuple[AnyStr, Tuple[AnyStr, ...]],
        Tuple[AnyStr, Tuple[StreamEntry, ...], Tuple[AnyStr, ...]],
    ],
    "XINFO GROUPS": Tuple[Dict[AnyStr, AnyStr], ...],
    "XINFO CONSUMERS": Tuple[Dict[AnyStr, AnyStr], ...],
    "XINFO STREAM": StreamInfo,
    "XPENDING": Union[Tuple[StreamPendingExt, ...], StreamPending],
    "XRANGE": Tuple[StreamEntry, ...],
    "XREVRANGE": Tuple[StreamEntry, ...],
    "XREADGROUP": Dict[AnyStr, Tuple[StreamEntry, ...]],
    "XREAD": Optional[Dict[AnyStr, Tuple[StreamEntry, ...]]],
    "ZDIFF": Tuple[Union[AnyStr, ScoredMember], ...],
    "ZINTER": Tuple[Union[AnyStr, ScoredMember], ...],
    "ZMPOP": Optional[Tuple[AnyStr, ScoredMembers]],
    "ZPOPMAX": Union[ScoredMember, ScoredMembers],
    "ZPOPMIN": Union[ScoredMember, ScoredMembers],
    "ZRANDMEMBER": Optional[Union[AnyStr, List[AnyStr], ScoredMembers]],
    "ZRANGE": Tuple[Union[AnyStr, ScoredMember], ...],
    "ZRANGEBYSCORE": Tuple[Union[AnyStr, ScoredMember], ...],
    "ZREVRANGEBYSCORE": Tuple[Union[AnyStr, ScoredMember], ...],
    "ZREVRANGE": Tuple[Union[AnyStr, ScoredMember], ...],
    "ZUNION": Tuple[Union[AnyStr, ScoredMember], ...],
    "ZSCAN": Tuple[int, ScoredMembers],
    "ZSCORE": Optional[float],
}
ARGUMENT_DEFAULTS = {
    "HSCAN": {"cursor": 0},
    "SCAN": {"cursor": 0},
    "SSCAN": {"cursor": 0},
    "ZSCAN": {"cursor": 0},
}
ARGUMENT_DEFAULTS_NON_OPTIONAL = {
    "KEYS": {"pattern": "*"},
}
ARGUMENT_OPTIONALITY = {
    "EVAL_RO": {"key": True, "arg": True},
    "EVALSHA_RO": {"key": True, "arg": True},
    "FCALL": {"key": True, "arg": True},
    "FCALL_RO": {"key": True, "arg": True},
    "MIGRATE": {"keys": False},
    "XADD": {"id_or_auto": True},
    "SCAN": {"cursor": True},
    "HSCAN": {"cursor": True},
    "SSCAN": {"cursor": True},
    "ZSCAN": {"cursor": True},
    "XRANGE": {"start": True, "end": True},
    "XREVRANGE": {"start": True, "end": True},
}
ARGUMENT_VARIADICITY = {"SORT": {"gets": False}, "SORT_RO": {"gets": False}}
REDIS_ARGUMENT_FORCED_ORDER = {
    "SETEX": ["key", "value", "seconds"],
    "ZINCRBY": ["key", "member", "increment"],
    "EVALSHA": ["sha1", "keys", "args"],
    "EVALSHA_RO": ["sha1", "keys", "args"],
    "EVAL": ["script", "keys", "args"],
    "EVAL_RO": ["script", "keys", "args"],
    "CLIENT KILL": [
        "ip_port",
        "identifier",
        "type_",
        "user",
        "addr",
        "laddr",
        "skipme",
    ],
    "CLIENT LIST": ["type_", "identifiers"],
    "FCALL": ["function", "keys", "args"],
    "FCALL_RO": ["function", "keys", "args"],
}
REDIS_ARGUMENT_FORCED = {
    "COMMAND GETKEYS": [
        {"name": "command", "type": "string"},
        {"name": "arguments", "type": "bulk-string", "multiple": True},
    ],
}
READONLY_OVERRIDES = {"TOUCH": False}
BLOCK_ARGUMENT_FORCED_ORDER = {"ZADD": {"member_scores": ["member", "score"]}}
STD_GROUPS = [
    "generic",
    "string",
    "bitmap",
    "hash",
    "list",
    "set",
    "sorted-set",
    "hyperloglog",
    "geo",
    "stream",
    "scripting",
    "pubsub",
    "transactions",
]

VERSIONADDED_DOC = re.compile("(.. versionadded:: ([\d\.]+))", re.DOTALL)
VERSIONCHANGED_DOC = re.compile("(.. versionchanged:: ([\d\.]+))", re.DOTALL)

inflection_engine = inflect.engine()


def render_annotation(annotation):
    if not annotation:
        return "None"

    if isinstance(annotation, type):
        if not annotation.__name__ == "NoneType":
            return annotation.__name__

        if not annotation.__name__ == "Ellipsis":
            return None

    else:
        if hasattr(annotation, "__name__"):
            if hasattr(annotation, "__args__"):
                if annotation.__name__ == "Union":
                    args = list(annotation.__args__)

                    for a in annotation.__args__:
                        if getattr(a, "__name__") == "NoneType":
                            args.remove(a)

                        if getattr(a, "__name__") == "Ellipsis":
                            args.remove(a)

                    return f"Optional[{Union[tuple(args)]}]"
                else:
                    sub_annotations = [
                        render_annotation(arg) for arg in annotation.__args__
                    ]
                    sub = ",".join([k for k in sub_annotations if k])

                    return f"{annotation.__name__}[{sub}]"

        return str(annotation)


def version_changed_from_doc(doc):
    if not doc:
        return
    v = VERSIONCHANGED_DOC.findall(doc)

    if v:
        return version.parse(v[0][1])


def version_added_from_doc(doc):
    if not doc:
        return
    v = VERSIONADDED_DOC.findall(doc)

    if v:
        return version.parse(v[0][1])


@functools.lru_cache
def get_commands():
    return requests.get("https://redis.io/commands.json").json()


def render_signature(signature):
    v = str(signature)

    v = re.sub("<class '(.*?)'>", "\\1", v)
    v = re.sub("<PureToken.(.*?): '(.*?)'>", "PureToken.\\1", v)
    v = v.replace("~str", "str")
    v = v.replace("~AnyStr", "AnyStr")

    return v


def compare_signatures(s1, s2):
    return [(p.name, p.default, p.annotation) for p in s1.parameters.values()] == [
        (p.name, p.default, p.annotation) for p in s2.parameters.values()
    ]


def get_token_mapping():
    commands = get_commands()
    mapping = collections.OrderedDict()

    for command, details in commands.items():

        def _extract_tokens(obj):
            tokens = []

            if args := obj.get("arguments"):
                for arg in args:
                    if arg["type"] == "pure-token":
                        tokens.append((arg["name"], arg["token"]))

                    if arg.get("arguments"):
                        tokens.extend(_extract_tokens(arg))

            return tokens

        for token in sorted(_extract_tokens(details), key=lambda token: token[0]):
            mapping.setdefault(token, set()).add(command)

    return mapping


def read_command_docs(command, group):
    doc = open(
        "/var/tmp/redis-doc/commands/%s.md" % command.lower().replace(" ", "-")
    ).read()

    return_description = re.compile(
        "(@(.*?)-reply[:,]*\s*(.*?)$)", re.MULTILINE
    ).findall(doc)

    def sanitize_description(desc):
        if not desc:
            return ""
        return_description = (
            desc.replace("a nil bulk reply", "``None``")
            .replace("a null bulk reply", "``None``")
            .replace(", specifically:", "")
            .replace("specifically:", "")
            .replace("represented as a string", "")
        )
        return_description = re.sub("`(.*?)`", "``\\1``", return_description)
        return_description = return_description.replace("`nil`", "``None``")
        return_description = re.sub("_(.*?)_", "``\\1``", return_description)
        return_description = return_description.replace(
            "````None````", "``None``"
        )  # lol
        return_description = return_description.replace("@examples", "")  # more lol
        return_description = return_description.replace("@example", "")  # more more lol
        return_description = re.sub("^\s*([^\w]+)", "", return_description)

        return return_description

    full_description = re.compile("@return(.*)@examples", re.DOTALL).findall(doc)

    if not full_description:
        full_description = re.compile("@return(.*)##", re.DOTALL).findall(doc)

    if not full_description:
        full_description = re.compile("@return(.*)$", re.DOTALL).findall(doc)

    if full_description:
        full_description = full_description[0].strip()

    full_description = sanitize_description(full_description)

    if full_description:
        full_description = re.sub("((.*)-reply)", "", full_description)
        full_description = full_description.split("\n")
        full_description = [k.strip().lstrip(":") for k in full_description]
        full_description = [k.strip() for k in full_description if k.strip()]
    collection_type = Tuple

    if return_description:
        if len(return_description) > 0:
            rtypes = {k[1]: k[2].replace("@examples", "") for k in return_description}
            has_nil = False
            has_bool = False

            if "simple-string" in rtypes and (
                rtypes["simple-string"].find("OK") >= 0
                or rtypes["simple-string"].find("an error") >= 0
                or not rtypes["simple-string"].strip()
            ):
                has_bool = True
                rtypes.pop("simple-string")

            if "nil" in rtypes:
                rtypes.pop("nil")
                has_nil = True

            for t, description in list(rtypes.items()):
                if (
                    "`nil`" in description
                    or "`null`" in description
                    or "`NULL`" in description
                    or "`None`" in description
                    or "`none`" in description
                ) and "or" in description:
                    has_nil = True
                elif (
                    "`nil`" in description
                    or "`null`" in description
                    or "`NULL`" in description
                    or "`None`" in description
                    or "`none`" in description
                ):
                    has_nil = True
                    rtypes.pop(t)

            full_description_joined = "\n".join(full_description)

            if (
                "`nil`" in full_description_joined
                or "`null`" in full_description_joined
                or "`NULL`" in full_description_joined
                or "`None`" in full_description_joined
                or "`none`" in full_description_joined
            ):
                has_nil = True

            mapped_types = {
                k: REDIS_RETURN_ARGUMENT_TYPE_MAPPING.get(k, "Any") for k in rtypes
            }
            # special handling for special types

            if "array" in mapped_types:
                if group == "list":
                    collection_type = mapped_types["array"] = List

                if group == "set":
                    collection_type = mapped_types["array"] = Set

            if has_bool:
                mapped_types["bool"] = bool

            if len(mapped_types) > 1:
                if "array" in mapped_types:
                    if (
                        rtypes.get("bulk-string", "").find("floating point") >= 0
                        or rtypes.get("bulk-string", "").find("double precision") >= 0
                        or rtypes.get("bulk-string", "").find("a double") >= 0
                    ):
                        mapped_types["array"] = (
                            Tuple[float, ...]
                            if collection_type == Tuple
                            else collection_type[float]
                        )
                    elif rtypes["array"].find("elements") >= 0:
                        mapped_types["array"] = (
                            Tuple[AnyStr, ...]
                            if collection_type == Tuple
                            else collection_type[AnyStr]
                        )
                    else:
                        mapped_types["array"] = (
                            Tuple[AnyStr, ...]
                            if collection_type == Tuple
                            else collection_type[AnyStr]
                        )

                if "bulk-string" in mapped_types:
                    if (
                        rtypes.get("bulk-string", "").find("floating point") >= 0
                        or rtypes.get("bulk-string", "").find("double precision") >= 0
                        or rtypes.get("bulk-string", "").find("a double") >= 0
                    ):
                        mapped_types["bulk-string"] = float
                    if rtypes.get("bulk-string", "").lower().find("an error") >= 0:
                        mapped_types.pop("bulk-string")
                        rtypes.pop("bulk-string")

                rtype = (
                    Optional[Union[tuple(mapped_types.values())]]
                    if has_nil
                    else Union[tuple(mapped_types.values())]
                )
            else:
                return_details = "\n".join(full_description)
                sub_type = list(mapped_types.values())[0]

                if "array" in rtypes:
                    sub_type_nil = "nil" in rtypes["array"]

                    if rtypes["array"].find("nested") >= 0:
                        sub_type = sub_type[sub_type[Any]]
                    else:
                        if sub_type == Tuple:
                            if rtypes["array"].find("integer") >= 0:
                                sub_type = (
                                    sub_type[int, ...]
                                    if not sub_type_nil
                                    else sub_type[Optional[int], ...]
                                )
                            elif rtypes["array"].find("and their") >= 0:
                                sub_type = Dict[AnyStr, AnyStr]
                            elif rtypes["array"].find("a double") >= 0:
                                sub_type = (
                                    sub_type[float, ...]
                                    if not sub_type_nil
                                    else sub_type[Optional[float], ...]
                                )
                            else:
                                sub_type = (
                                    sub_type[AnyStr, ...]
                                    if not sub_type_nil
                                    else sub_type[Optional[AnyStr], ...]
                                )

                            if sub_type_nil:
                                has_nil = False
                        else:
                            if rtypes["array"].find("integer") >= 0:
                                sub_type = (
                                    sub_type[int]
                                    if not sub_type_nil
                                    else sub_type[Optional[int]]
                                )
                            elif rtypes["array"].find("and their") >= 0:
                                sub_type = (
                                    sub_type[Tuple[AnyStr, AnyStr]]
                                    if not sub_type_nil
                                    else sub_type[Tuple[AnyStr, AnyStr]]
                                )
                            elif rtypes["array"].find("a double") >= 0:
                                sub_type = (
                                    sub_type[float]
                                    if not sub_type_nil
                                    else sub_type[Optional[float]]
                                )
                            else:
                                sub_type = (
                                    sub_type[AnyStr]
                                    if not sub_type_nil
                                    else sub_type[Optional[AnyStr]]
                                )

                            if sub_type_nil:
                                has_nil = False

                if "integer" in rtypes:
                    if (
                        return_details.find("``0``") >= 0
                        and return_details.find("``1``") >= 0
                    ):
                        sub_type = bool

                if "simple-string" in rtypes:
                    if rtypes["simple-string"].find("a double") >= 0:
                        sub_type = float

                if "bulk-string" in rtypes:
                    if rtypes["bulk-string"].find("a double") >= 0:
                        sub_type = float

                rtype = Optional[sub_type] if has_nil else sub_type

            rdesc = [sanitize_description(k[2]) for k in return_description]
            rdesc = [k for k in rdesc if k.strip()]

            return rtype, full_description

    return Any, ""


@functools.lru_cache
def get_official_commands(group=None):
    response = get_commands()
    by_group = {}
    [
        by_group.setdefault(command["group"], []).append({**command, **{"name": name}})
        for name, command in response.items()
        if version.parse(command["since"]) < MAX_SUPPORTED_VERSION
        and name not in SKIP_COMMANDS
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
    if (
        command["name"].find(" HELP") >= 0
        or command["summary"].find("container for") >= 0
    ):
        return True

    return False


def is_deprecated(command, kls):
    if (
        command.get("deprecated_since")
        and version.parse(command["deprecated_since"]) >= MIN_SUPPORTED_VERSION
    ):
        replacement = command.get("replaced_by", "")
        replacement = re.sub("`(.*?)`", "``\\1``", replacement)
        replacement_tokens = [k for k in re.findall("(``(.*?)``)", replacement)]
        replacement_string = {}
        all_commands = get_commands()
        for token in replacement_tokens:
            if token[1] in all_commands:
                replacement_string[
                    token[0]
                ] = f":meth:`~coredis.{kls.__name__}.{sanitized(token[1], None)}`"
            else:
                replacement_string[token[1]] = sanitized(token[1], None)

        for token, mapped in replacement_string.items():
            replacement = replacement.replace(token, mapped)
        return version.parse(command["deprecated_since"]), replacement
    else:
        return [None, None]


def sanitized(x, command=None):
    cleansed_name = (
        x.lower().strip().replace("-", "_").replace(":", "_").replace(" ", "_")
    )

    if command:
        override = REDIS_ARGUMENT_NAME_OVERRIDES.get(command["name"], {}).get(
            cleansed_name
        )

        if override:
            cleansed_name = override

    if cleansed_name == "id":
        return "identifier"

    if cleansed_name in (list(globals()["__builtins__"].__dict__.keys()) + ["async"]):
        cleansed_name = cleansed_name + "_"

    return cleansed_name


def skip_arg(argument, command):
    arg_version = argument.get("since")

    if arg_version and version.parse(arg_version) > MAX_SUPPORTED_VERSION:
        return True

    if argument["name"] in IGNORED_ARGUMENTS.get(command["name"], []):
        return True

    return False


def relevant_min_version(v, min=True):
    if not v:
        return False
    if min:
        return version.parse(v) > MIN_SUPPORTED_VERSION
    else:
        return version.parse(v) <= MAX_SUPPORTED_VERSION


def get_type(arg, command):
    inferred_type = REDIS_ARGUMENT_TYPE_MAPPING.get(arg["type"], Any)
    sanitized_name = sanitized(arg["name"])
    command_arg_overrides = REDIS_ARGUMENT_TYPE_OVERRIDES.get(command["name"], {})
    if arg_type_override := command_arg_overrides.get(
        arg["name"], command_arg_overrides.get(sanitized_name)
    ):
        return arg_type_override

    if arg["name"] in ["seconds", "milliseconds"] and inferred_type == int:
        return Union[int, datetime.timedelta]

    if arg["name"] == "yes/no" and inferred_type in [StringT, ValueT]:
        return bool
    if (
        arg["name"]
        in ["value", "element", "pivot", "member", "id", "min", "max", "start", "end", "argument", "arg", "port"]
        and inferred_type == StringT
    ):
        return ValueT
    return inferred_type


def get_type_annotation(arg, command, parent=None, default=None):
    if arg["type"] == "oneof" and all(
        k["type"] == "pure-token" for k in arg["arguments"]
    ):
        tokens = ["PureToken.%s" % s["name"].upper() for s in arg["arguments"]]
        literal_type = eval(f"Literal[{','.join(tokens)}]")

        if arg.get("optional") and default is None or parent and parent.get("optional"):
            return Optional[literal_type]

        return literal_type
    else:
        return get_type(arg, command)


def get_argument(
    arg,
    parent,
    command,
    arg_type=inspect.Parameter.KEYWORD_ONLY,
    multiple=False,
    num_multiples=0,
):
    if skip_arg(arg, command):
        return [[], [], {}]
    min_version = arg.get("since", None)

    param_list = []
    decorators = []
    meta_mapping = {}

    if arg["type"] == "block":
        if arg.get("multiple") or all(
            c.get("multiple") for c in arg.get("arguments", [])
        ):
            name = sanitized(arg["name"], command)

            if not inflection_engine.singular_noun(name):
                name = inflection_engine.plural(name)
            forced_order = BLOCK_ARGUMENT_FORCED_ORDER.get(command["name"], {}).get(
                name
            )

            if forced_order:
                child_args = sorted(
                    arg["arguments"], key=lambda a: forced_order.index(a["name"])
                )
            else:
                child_args = arg["arguments"]
            child_types = [get_type(child, command) for child in child_args]
            for c in child_args:
                if relevant_min_version(c.get("since", None)):
                    meta_mapping.setdefault(c["name"], {})["version"] = c.get(
                        "since", None
                    )
            if arg_type_override := REDIS_ARGUMENT_TYPE_OVERRIDES.get(
                command["name"], {}
            ).get(name):
                annotation = arg_type_override
            else:
                if len(child_types) == 1:
                    annotation = Iterable[child_types[0]]
                elif len(child_types) == 2 and child_types[0] in [StringT, ValueT]:
                    annotation = Dict[child_types[0], child_types[1]]
                else:
                    child_types_repr = ",".join(
                        [
                            "%s" % k if hasattr(k, "_name") else k.__name__
                            for k in child_types
                        ]
                    )
                    annotation = Iterable[eval(f"Tuple[{child_types_repr}]")]

            extra = {}

            if arg.get("optional") or (parent and parent.get("optional")):
                extra["default"] = ARGUMENT_DEFAULTS.get(command["name"], {}).get(name)

                if extra.get("default") is None:
                    annotation = Optional[annotation]
            param_list.append(
                inspect.Parameter(name, arg_type, annotation=annotation, **extra)
            )
            if relevant_min_version(arg.get("since", None)):
                meta_mapping.setdefault(name, {})["version"] = arg.get("since", None)

        else:
            plist_d = []
            if len(arg["arguments"]) == 1 and not arg.get("multiple"):
                synthetic_parent = arg.copy()
                synthetic_parent["type"] = "pure-token"
                synthetic_parent.pop("arguments")
                plist_p, declist, vmap = get_argument(synthetic_parent, parent, command, arg_type, False)
                param_list.extend(plist_p)
                meta_mapping.update(vmap)
            for child in sorted(
                arg["arguments"], key=lambda v: int(v.get("optional") == True)
            ):
                plist, declist, vmap = get_argument(
                    child, arg, command, arg_type, arg.get("multiple"), num_multiples
                )
                param_list.extend(plist)
                meta_mapping.update(vmap)

                if not child.get("optional"):
                    plist_d.extend(plist)

            if len(plist_d) > 1:
                mutually_inclusive_params = ",".join(
                    ["'%s'" % child.name for child in plist_d]
                )
                decorators.append(
                    f"@mutually_inclusive_parameters({mutually_inclusive_params})"
                )

    elif arg["type"] == "oneof":
        extra_params = {}

        if all(child["type"] == "pure-token" for child in arg["arguments"]):
            if parent:
                syn_name = sanitized(f"{parent['name']}_{arg.get('name')}", command)
            else:
                syn_name = sanitized(f"{arg.get('token', arg.get('name'))}", command)

            if arg.get("optional") or parent and parent.get("optional"):
                extra_params["default"] = ARGUMENT_DEFAULTS.get(
                    command["name"], {}
                ).get(syn_name)
            param_list.append(
                inspect.Parameter(
                    syn_name,
                    arg_type,
                    annotation=get_type_annotation(
                        arg, command, parent, default=extra_params.get("default")
                    ),
                    **extra_params,
                )
            )
            if relevant_min_version(arg.get("since", None)):
                meta_mapping.setdefault(syn_name, {})["version"] = arg.get(
                    "since", None
                )
        else:
            plist_d = []

            for child in arg["arguments"]:
                plist, declist, vmap = get_argument(
                    child, arg, command, arg_type, multiple, num_multiples
                )
                param_list.extend(plist)
                plist_d.extend(plist)
                meta_mapping.update(vmap)
            if len(plist_d) > 1:
                mutually_exclusive_params = ",".join(["'%s'" % p.name for p in plist_d])
                decorators.append(
                    f"@mutually_exclusive_parameters({mutually_exclusive_params})"
                )
    else:
        name = sanitized(
            arg.get("token", arg["name"])
            if not arg.get("type") == "pure-token"
            else arg["name"],
            command,
        )
        type_annotation = get_type_annotation(
            arg,
            command,
            parent,
            default=ARGUMENT_DEFAULTS.get(command["name"], {}).get(name),
        )
        extra_params = {}

        if parent and (parent.get("optional") or parent.get("type") == "oneof"):
            type_annotation = Optional[type_annotation]
            extra_params = {"default": None}

        if is_arg_optional(arg, command) and not arg.get("multiple"):
            type_annotation = Optional[type_annotation]
            extra_params = {"default": None}
        else:
            default = ARGUMENT_DEFAULTS_NON_OPTIONAL.get(command["name"], {}).get(name)

            if default is not None:
                extra_params["default"] = default
                arg_type = inspect.Parameter.KEYWORD_ONLY

        if multiple:
            name = inflection_engine.plural(name)

            if not inflection_engine.singular_noun(name):
                name = inflection_engine.plural(name)
            is_variadic = arg.get("optional") and num_multiples <= 1
            forced_variadicity = ARGUMENT_VARIADICITY.get(command["name"], {}).get(
                name, None
            )
            if forced_variadicity is not None:
                is_variadic = forced_variadicity
            if not is_variadic:
                if (
                    default := ARGUMENT_DEFAULTS.get(command["name"], {}).get(name)
                ) is not None:
                    type_annotation = Iterable[type_annotation]
                    extra_params["default"] = default
                elif (
                    is_arg_optional(arg, command)
                    and extra_params.get("default") is None
                ):
                    type_annotation = Optional[Iterable[type_annotation]]
                    extra_params["default"] = None
                else:
                    type_annotation = Iterable[type_annotation]
            else:
                arg_type = inspect.Parameter.VAR_POSITIONAL

        if "default" in extra_params:
            extra_params["default"] = ARGUMENT_DEFAULTS.get(command["name"], {}).get(
                name, extra_params.get("default")
            )
        if relevant_min_version(min_version):
            meta_mapping.setdefault(name, {})["version"] = min_version
        else:
            if parent:
                if relevant_min_version(parent.get("since", None)):
                    meta_mapping.setdefault(name, {})["version"] = parent.get("since")

        if not multiple:
            if parent and parent.get("token"):
                meta_mapping.setdefault(name, {}).update(
                    {"prefix_token": parent.get("token")}
                )
        else:
            if arg.get("token"):
                meta_mapping.setdefault(name, {}).update(
                    {"prefix_token": arg.get("token")}
                )

        param_list.append(
            inspect.Parameter(
                name, arg_type, annotation=type_annotation, **extra_params
            )
        )
    return [param_list, decorators, meta_mapping]


def is_arg_optional(arg, command):
    command_optionality = ARGUMENT_OPTIONALITY.get(command["name"], {})
    override = command_optionality.get(
        sanitized(arg.get("name", ""), command)
    ) or command_optionality.get(sanitized(arg.get("token", ""), command))

    if override is not None:
        return override

    return arg.get("optional")


def get_command_spec(command):
    arguments = command.get("arguments", []) + REDIS_ARGUMENT_FORCED.get(
        command["name"], []
    )
    recommended_signature = []
    decorators = []
    forced_order = REDIS_ARGUMENT_FORCED_ORDER.get(command["name"], [])
    mapping = {}
    meta_mapping = {}
    arg_names = [k["name"] for k in arguments]
    initial_order = [(k["name"], k.get("token", "")) for k in arguments]
    history = command.get("history", [])
    extra_version_info = {}
    num_multiples = len([k for k in arguments if k.get("multiple")])
    for arg_name in arg_names:
        for version, entry in history:
            if "`%s`" % arg_name in entry and "added" in entry.lower():
                extra_version_info[arg_name] = version
    for k in arguments:
        version_added = extra_version_info.get(k["name"])
        if version_added and not k.get("since"):
            k["since"] = version_added

    for k in arguments:
        if not is_arg_optional(k, command) and not k.get("multiple"):
            plist, dlist, vmap = get_argument(
                k,
                None,
                command,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                num_multiples=num_multiples,
            )
            mapping[(k["name"], k.get("token", ""))] = (k, plist)
            recommended_signature.extend(plist)
            decorators.extend(dlist)
            meta_mapping.update(vmap)

    for k in arguments:
        if not is_arg_optional(k, command) and k.get("multiple"):
            plist, dlist, vmap = get_argument(
                k,
                None,
                command,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                True,
                num_multiples=num_multiples,
            )
            mapping[(k["name"], k.get("token", ""))] = (k, plist)
            recommended_signature.extend(plist)
            decorators.extend(dlist)
            meta_mapping.update(vmap)

    var_args = [
        k.name
        for k in recommended_signature
        if k.kind == inspect.Parameter.VAR_POSITIONAL
    ]

    if forced_order:
        recommended_signature = sorted(
            recommended_signature,
            key=lambda r: forced_order.index(r.name)
            if r.name in forced_order
            else recommended_signature.index(r),
        )

    if not var_args and not forced_order:
        recommended_signature = sorted(
            recommended_signature,
            key=lambda r: -5
            if r.name in ["key", "keys"]
            else -4
            if r.name in ["arg", "args"]
            else -3
            if r.name == "weights"
            else -2
            if r.name == "start" and "end" in arg_names
            else -1
            if r.name == "end" and "start" in arg_names
            else recommended_signature.index(r),
        )

        for idx, k in enumerate(recommended_signature):
            if k.name == "key":
                n = inspect.Parameter(
                    k.name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=k.default,
                    annotation=k.annotation,
                )
                recommended_signature.remove(k)
                recommended_signature.insert(idx, n)

    elif {"key"} & {r.name for r in recommended_signature} and not forced_order:
        new_recommended_signature = sorted(
            recommended_signature,
            key=lambda r: -1 if r.name in ["key"] else recommended_signature.index(r),
        )
        reordered = [k.name for k in new_recommended_signature] != [
            k.name for k in recommended_signature
        ]

        for idx, k in enumerate(new_recommended_signature):
            if reordered:
                if k.kind == inspect.Parameter.VAR_POSITIONAL:
                    n = inspect.Parameter(
                        k.name,
                        inspect.Parameter.KEYWORD_ONLY,
                        default=k.default,
                        annotation=Iterable[k.annotation],
                    )
                    new_recommended_signature.remove(k)
                    new_recommended_signature.insert(idx, n)

            if k.name == "key":
                n = inspect.Parameter(
                    k.name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=k.default,
                    annotation=k.annotation,
                )
                new_recommended_signature.remove(k)
                new_recommended_signature.insert(idx, n)
            recommended_signature = new_recommended_signature

    for k in sorted(arguments, key=lambda r: -1 if r["type"] == "oneof" else 0):
        if is_arg_optional(k, command) and k.get("multiple"):
            plist, dlist, vmap = get_argument(
                k,
                None,
                command,
                inspect.Parameter.KEYWORD_ONLY,
                True,
                num_multiples=num_multiples,
            )
            mapping[(k["name"], k.get("token", ""))] = (k, plist)
            recommended_signature.extend(plist)
            decorators.extend(dlist)
            meta_mapping.update(vmap)

    remaining = [
        k for k in arguments if is_arg_optional(k, command) and not k.get("multiple")
    ]
    remaining_signature = []

    for k in remaining:
        if skip_arg(k, command):
            continue
        plist, dlist, vmap = get_argument(k, None, command, num_multiples=num_multiples)
        mapping[(k["name"], k.get("token", ""))] = (k, plist)
        remaining_signature.extend(plist)
        decorators.extend(dlist)
        meta_mapping.update(vmap)

    if not forced_order:
        remaining_signature = sorted(
            remaining_signature,
            key=lambda s: -1
            if s.name in ["identifier", "identifiers"]
            else remaining_signature.index(s),
        )
    recommended_signature.extend(remaining_signature)

    if (
        len(recommended_signature) > 1
        and recommended_signature[-2].kind == inspect.Parameter.POSITIONAL_ONLY
    ):
        recommended_signature[-1] = inspect.Parameter(
            recommended_signature[-1].name,
            inspect.Parameter.POSITIONAL_ONLY,
            default=recommended_signature[-1].default,
            annotation=recommended_signature[-1].annotation,
        )

    mapping = OrderedDict(
        {
            k: v
            for k, v in sorted(
                mapping.items(), key=lambda tup: initial_order.index(tup[0])
            )
        }
    )
    return recommended_signature, decorators, mapping, meta_mapping


def generate_method_details(kls, method, debug):

    method_details = {"kls": kls, "command": method}

    if skip_command(method):
        return method_details
    name = MAPPING.get(
        method["name"],
        method["name"].strip().lower().replace(" ", "_").replace("-", "_"),
    )
    method_details["name"] = name
    method_details["redis_method"] = method
    method_details["located"] = find_method(kls, name)
    method_details["deprecation_info"] = is_deprecated(method, kls)

    version_introduced = version.parse(method["since"])
    if version_introduced > MIN_SUPPORTED_VERSION:
        method_details["redis_version_introduced"] = version_introduced
    else:
        method_details["redis_version_introduced"] = None
    method_details["summary"] = method["summary"]
    return_summary = ""

    if debug and not method["name"] in SKIP_SPEC:
        recommended_return = read_command_docs(method["name"], method["group"])

        if recommended_return:
            return_summary = recommended_return[1]
        rec_params, rec_decorators, arg_mapping, meta_mapping = get_command_spec(method)
        method_details["arg_mapping"] = arg_mapping
        method_details["arg_meta_mapping"] = meta_mapping
        method_details["rec_decorators"] = rec_decorators
        method_details["rec_params"] = rec_params
        try:
            rec_signature = inspect.Signature(
                [inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD)]
                + rec_params,
                return_annotation=REDIS_RETURN_OVERRIDES.get(
                    method["name"], recommended_return[0]
                )
                if recommended_return
                else None,
            )
            method_details["rec_signature"] = rec_signature
        except:
            print(method["name"], rec_params)
            raise Exception(method["name"], [(k.name, k.kind) for k in rec_params])

        method_details["readonly"] = READONLY_OVERRIDES.get(
            method["name"], "readonly" in method.get("command_flags", [])
        )
        method_details["return_summary"] = return_summary
    return method_details


def generate_compatibility_section(
    section,
    preamble,
    kls,
    parent_kls,
    groups,
    debug=False,
    next_version="6.6.6",
):
    env = Environment()
    section_template_str = """
{{section}}
{{len(section)*'^'}}

{% if preamble.strip() %} 
.. note:: {{preamble}}
{% endif %}
{% for group in groups %}
{% if group in methods_by_group %}
{{group.title()}}
{{len(group)*'-'}}

{% for method in methods_by_group[group]["supported"] %}
{% set command_link=redis_command_link(method['redis_method']['name']) -%}
{% if debug %}
{{ method['redis_method']['name'] }} {% if method["full_match"] -%}[✓]{% endif %}
{% else %}
{{ method['redis_method']['name'] }}
{% endif -%}
{{(len(method['redis_method']['name'])+(4 if debug and method["full_match"] else 0))*"*"}}

{{ method['summary'] }}

- Documentation: {{command_link}}
- Implementation: :meth:`~coredis.{{kls.__name__}}.{{method["located"].__name__}}`
{% if method["redis_version_introduced"] and method["redis_version_introduced"] > MIN_SUPPORTED_VERSION %}
- New in redis: {{method["redis_version_introduced"]}}
{% endif %}
{% if method["deprecation_info"][0] and method["deprecation_info"][0] >= MIN_SUPPORTED_VERSION %}
- Deprecated in redis: {{method["deprecation_info"][0] }}. Use {{method["deprecation_info"][1]}}
{% endif %}
{% if method["version_added"] %}
- {{method["version_added"]}}
{% endif %}
{% if method["version_changed"] %}
- {{method["version_changed"]}}
{% endif %}
{% if debug %}
- Current Signature {% if method.get("full_match") %} (Full Match) {% else %} ({{method["mismatch_reason"]}}) {% endif %}

  .. code::

     {% for decorator in method["rec_decorators"] -%}
     {{decorator}}
     {% endfor -%}
     {% if not method["full_match"] -%}
     @redis_command("{{method["command"]["name"]}}"
     {%- if method["redis_version_introduced"] and method["redis_version_introduced"] > MIN_SUPPORTED_VERSION -%}
     , version_introduced="{{method["command"].get("since")}}"
     {%- endif -%}
     {%- if method["deprecation_info"][0] and method["deprecation_info"][0] >= MIN_SUPPORTED_VERSION -%}
     , version_deprecated="{{method["command"].get("deprecated_since")}}"
     {%- endif -%}, group=CommandGroup.{{method["command"]["group"].upper().replace(" ", "_").replace("-", "_")}}
     {%- if len(method["arg_meta_mapping"]) > 0 -%}
     {% set argument_with_version = {} %}
     {%- for name, meta  in method["arg_meta_mapping"].items() -%}
     {%- if meta and meta["version"] and version_parse(meta["version"]) >= MIN_SUPPORTED_VERSION -%}
     {% set _ = argument_with_version.update({name: {"version_introduced": meta["version"]}}) %}
     {%- endif -%}
     {%- endfor -%}
     {% if method["readonly"] %}, readonly=True{% endif -%}
     {% if argument_with_version %}, arguments={{ argument_with_version }}{% endif %}
     {%- endif -%})
     {%- endif -%}
     {% set implementation = method["located"] -%}
     {% set implementation = inspect.getclosurevars(implementation).nonlocals.get("func", implementation) -%}
     {% if method["full_match"] %}
     async def {{method["name"]}}{{render_signature(method["current_signature"])}}:
     {% else %}
     - async def {{method["name"]}}{{render_signature(method["current_signature"])}}:
     + async def {{method["name"]}}{{render_signature(method["rec_signature"])}}:
     {% endif %}
         \"\"\"
         {% for line in (implementation.__doc__ or "").split("\n") -%}
         {{line.lstrip()}}
         {% endfor %}
         {% if method["return_summary"] and not method["located"].__doc__.find(":return:")>=1-%}
         \"\"\"

         \"\"\"
         Recommended docstring:

         {{method["summary"]}}

         {% if method["located"].__doc__.find(":param:") < 0 -%}
         {% for p in list(method["rec_signature"].parameters)[1:] -%}
         {% if p != "key" -%}
         :param {{p}}:
         {%- endif -%}
         {% endfor %}
         {% endif -%}
         {% if len(method["return_summary"]) == 1 -%}
         :return: {{method["return_summary"][0]}}
         {%- else -%}
         :return:
         {% for desc in method["return_summary"] -%}
         {{desc}}
         {%- endfor -%}
         {% endif %}
         {% endif -%}
         \"\"\"


         {% if "execute_command" not in inspect.getclosurevars(implementation).unbound -%}
         {% if len(method["arg_mapping"]) > 0 -%}
         pieces: CommandArgList = []
         {% for name, arg  in method["arg_mapping"].items() -%}
         
         {% if len(arg[1]) > 0 -%}
         {%- for param in arg[1] -%}
         {%- if not arg[0].get("optional") %}
         {%- if arg[0].get("multiple") %}
         {%- if arg[0].get("token") %}
         pieces.extend(*{{param.name}})
         {%- else %}
         pieces.extend(*{{param.name}})
         {%- endif %}
         {%- else %}
         {%- if arg[0].get("token") %}
         pieces.append("{{arg[0].get("token")}}")
         pieces.append({{param.name}})
         {%- else %}
         pieces.append({{param.name}})
         {%- endif %}
         {%- endif %}
         {%- else %}
         {% if arg[0].get("multiple") -%}
         if {{param.name}}:
         {%- if arg[0].get("multiple_token") %}
             for item in {{param.name}}:
                 pieces.append("{{arg[0].get("token")}}")
                 pieces.append(item)
         {%- else %}
             pieces.append("{{arg[0].get("token")}}")
             pieces.extend({{param.name}})
         {%- endif %}
         {%- else %}
         if {{param.name}}{% if arg[0].get("type") != "pure-token" %} is not None{%endif%}:
         {%- if arg[0].get("token") and arg[0].get("type") != "pure-token" %}
             pieces.append("{{arg[0].get("token")}}")
             pieces.extend({{param.name}})
         {%- else %}
             {%- if arg[0].get("type") == "oneof" %}
             pieces.append({{param.name}})
             {%- else %}
             pieces.append(PureToken.{{arg[0].get("token")}})
             {% endif %}
         {%- endif %}
         {%- endif %}
         {%- endif %}
         {%- endfor %}
         {%- endif %}
         {%- endfor %}

         return await self.execute_command("{{method["command"]["name"]}}", *pieces)
         {% else -%}

         return await self.execute_command("{{method["command"]["name"]}}")
         {% endif -%}
         {% endif -%}
{% endif %}
{% endfor %}
{% for method in methods_by_group[group]["missing"] %}
{% set command_link= redis_command_link(method['redis_method']['name']) -%}
{{ method["command"]["name"] }} [X]
{{(len(method["command"]["name"])+4)*"*"}}

{{ method['summary'] }}

- Documentation: {{ command_link }}
{% if debug %}
- Recommended Signature:

  .. code::
  
     {% for decorator in method["rec_decorators"] %}
     {{decorator}}
     {% endfor -%}
     @versionadded(version="{{next_version}}")
     @redis_command("{{method["command"]["name"]}}"
     {%- if method["redis_version_introduced"] and method["redis_version_introduced"] > MIN_SUPPORTED_VERSION -%}
     , version_introduced="{{method["command"].get("since")}}"
     {%- endif -%}, group=CommandGroup.{{method["command"]["group"].upper().replace(" ","_").replace("-","_")}}
     {%- if len(method["arg_mapping"]) > 0 -%}
     {% set argument_with_version = {} %}
     {%- for name, arg  in method["arg_mapping"].items() -%}
     {%- for param in arg[1] -%}
     {%- if arg[0].get("since") and version_parse(arg[0].get("since")) >= MIN_SUPPORTED_VERSION -%}
     {% set _ = argument_with_version.update({param.name: {"version_introduced": arg[0].get("since")}}) %}
     {%- endif -%}
     {%- endfor -%}
     {%- endfor -%}
     {% if method["readonly"] %}, readonly=True{% endif -%}
     {% if argument_with_version %}, arguments={{ argument_with_version }}{%endif%}
     {%- endif -%})
     async def {{method["name"]}}{{render_signature(method["rec_signature"])}}:
         \"\"\"
         {{method["summary"]}}
  
         {% if "rec_signature" in method %}
         {% for p in list(method["rec_signature"].parameters)[1:] %}
         :param {{p}}:
         {%- endfor %}
         {% endif %}
         {% if len(method["return_summary"]) == 0 %}
         :return: {{method["return_summary"][0]}}
         {% else %}
         :return:
         {% for desc in method["return_summary"] %}
         {{desc}}
         {%- endfor %}
         {% endif %}
         \"\"\"
         {% if len(method["arg_mapping"]) > 0 -%}
         pieces = []
         {%- for name, arg  in method["arg_mapping"].items() %}
         # Handle {{name}}
         {% if len(arg[1]) > 0 -%}
         {% for param in arg[1] -%}
         {% if not arg[0].get("optional") -%}
         {% if arg[0].get("multiple") -%}
         {% if arg[0].get("token") -%}
         pieces.extend(*{{param.name}})
         {% else -%}
         pieces.extend(*{{param.name}})
         {% endif -%}
         {% else -%}
         {%- if arg[0].get("token") %}
         pieces.append("{{arg[0].get("token")}}")
         pieces.append({{param.name}})
         {% else -%}
         pieces.append({{param.name}})
         {% endif -%}
         {% endif -%}
         {% else -%}
         {% if arg[0].get("multiple") %}
  
         if {{arg[1][0].name}}:
            pieces.extend({{param.name}})
         {% else %}
  
         if {{param.name}}{% if arg[0].get("type") != "pure-token" %} is not None{%endif%}:
         {%- if arg[0].get("token")  and arg[0].get("type") == "oneof" %}
            pieces.append({{param.name}}.value)
         {%- else %}
            pieces.extend(["{{arg[0].get("token")}}", {{param.name}}])
         {% endif -%}
         {% endif -%}
         {% endif %}
         {% endfor -%}
         {% endif -%}
         {% endfor -%}
  
         return await self.execute_command("{{method["command"]["name"]}}", *pieces)
         {% else -%}
 
        return await self.execute_command("{{method["command"]["name"]}}")
        {% endif -%}
{% else %} 
- Not Implemented
{% endif %}
{% endfor %}
{% endif %}
{% endfor %}

    """
    env.globals.update(
        MIN_SUPPORTED_VERSION=MIN_SUPPORTED_VERSION,
        MAX_SUPPORTED_VERSION=MAX_SUPPORTED_VERSION,
        get_official_commands=get_official_commands,
        inspect=inspect,
        len=len,
        list=list,
        version_parse=version.parse,
        skip_command=skip_command,
        redis_command_link=redis_command_link,
        find_method=find_method,
        kls=kls,
        render_signature=render_signature,
        next_version=next_version,
        preamble=preamble,
        debug=debug,
    )
    section_template = env.from_string(section_template_str)
    methods_by_group = {}

    for group in groups:

        methods = {"supported": [], "missing": []}
        for method in get_official_commands(group):
            method_details = generate_method_details(kls, method, debug)
            if debug and not method_details.get("rec_signature"):
                continue
            if not debug and skip_command(method):
                continue

            located = method_details.get("located")

            if (
                parent_kls
                and located
                and find_method(parent_kls, sanitized(method["name"])) == located
            ):
                continue
            if located:
                version_added = VERSIONADDED_DOC.findall(located.__doc__)
                version_added = (version_added and version_added[0][0]) or ""
                version_added.strip()

                version_changed = VERSIONCHANGED_DOC.findall(located.__doc__)
                version_changed = (version_changed and version_changed[0][0]) or ""
                method_details["version_changed"] = version_changed
                method_details["version_added"] = version_added

                command_details = getattr(located, "__coredis_command", None)
                if not method["name"] in SKIP_SPEC:
                    cur = inspect.signature(located)
                    current_signature = [k for k in cur.parameters]
                    method_details["current_signature"] = cur
                    if debug:
                        if (
                            compare_signatures(cur, method_details["rec_signature"])
                            and cur.return_annotation
                            == method_details["rec_signature"].return_annotation
                        ):
                            src = inspect.getsource(located)
                            version_introduced_valid = command_details and str(
                                command_details.version_introduced
                            ) == str(method_details["redis_version_introduced"])
                            version_deprecated_valid = command_details and str(
                                command_details.version_deprecated
                            ) == str(method_details.get("deprecation_info", [None])[0])
                            readonly_valid = (
                                command_details
                                and command_details.readonly
                                == method_details["readonly"]
                            )
                            arg_version_valid = command_details and len(
                                command_details.arguments
                            ) == len(
                                [
                                    k
                                    for k in method_details["arg_meta_mapping"]
                                    if method_details["arg_meta_mapping"]
                                    .get(k, {})
                                    .get("version")
                                ]
                            )
                            if (
                                src.find("@redis_command") >= 0
                                and src.find(method["name"]) >= 0
                                and command_details
                                and command_details.readonly
                                == method_details["readonly"]
                                and version_introduced_valid
                                and version_deprecated_valid
                                and arg_version_valid
                            ):
                                method_details["full_match"] = True
                            else:
                                method_details["mismatch_reason"] = (
                                    "Command wrapper missing"
                                    if not command_details
                                    else f"Incorrect version introduced {command_details.version_introduced} vs {method_details['redis_version_introduced']}"
                                    if not version_introduced_valid
                                    else f"Incorrect version deprecated"
                                    if not version_deprecated_valid
                                    else "Readonly flag mismatch"
                                    if not readonly_valid
                                    else "Argument version mismatch"
                                    if not arg_version_valid
                                    else "unknown"
                                )
                        elif (
                            cur.parameters == method_details["rec_signature"].parameters
                        ):
                            recommended_return = read_command_docs(
                                method["name"], method["group"]
                            )
                            method_details["mismatch_reason"] = "Missing return type."
                            if recommended_return:
                                new_sig = inspect.Signature(
                                    [
                                        inspect.Parameter(
                                            "self",
                                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                        )
                                    ]
                                    + method_details["rec_params"],
                                    return_annotation=recommended_return[0],
                                )
                        else:
                            method_details["mismatch_reason"] = "Arg mismatch"
                            diff_minus = [
                                str(k)
                                for k, v in method_details[
                                    "rec_signature"
                                ].parameters.items()
                                if k not in current_signature
                            ]
                            diff_plus = [
                                str(k)
                                for k in current_signature
                                if k not in method_details["rec_signature"].parameters
                            ]
                            method_details["diff_minus"] = diff_minus
                            method_details["diff_plus"] = diff_plus
                methods["supported"].append(method_details)
            elif is_deprecated(method, kls) == [None, None]:
                methods["missing"].append(method_details)
        if methods["supported"] or methods["missing"]:
            methods_by_group[group] = methods
    return section_template.render(
        section=section, groups=groups, methods_by_group=methods_by_group
    )


@click.group()
@click.option("--debug", default=False, help="Output debug")
@click.option("--next-version", default="6.6.6", help="Next version")
@click.pass_context
def code_gen(ctx, debug: bool, next_version: str):
    ctx.ensure_object(dict)
    if debug:
        if not os.path.isdir("/var/tmp/redis-doc"):
            os.system("git clone git@github.com:redis/redis-doc /var/tmp/redis-doc")
        else:
            os.system("cd /var/tmp/redis-doc && git pull")

    ctx.obj["DEBUG"] = debug
    ctx.obj["NEXT_VERSION"] = next_version


@code_gen.command()
@click.option("--path", default="docs/source/compatibility.rst")
@click.pass_context
def coverage_doc(ctx, path: str):
    output = f"""
Command compatibility
=====================

This document is generated by parsing the `official redis command documentation <https://redis.io/commands>`_

"""

    kls = coredis.Redis
    output += generate_compatibility_section(
        "Redis Client",
        "",
        kls,
        None,
        STD_GROUPS + ["server", "connection", "cluster"],
        debug=ctx.obj["DEBUG"],
        next_version=ctx.obj["NEXT_VERSION"],
    )

    # Cluster client
    cluster_kls = coredis.RedisCluster
    output += generate_compatibility_section(
        "Redis Cluster Client",
        f"""
        The Cluster client generally follows the API of :class:`~coredis.Redis`
        however for cross-slot commands certain commands have to be implemented
        client side. 
        """,
        cluster_kls,
        kls,
        STD_GROUPS + ["server", "connection", "cluster"],
        debug=ctx.obj["DEBUG"],
        next_version=ctx.obj["NEXT_VERSION"],
    )
    open(path, "w").write(output)
    print(f"Generated coverage doc at {path}")


@code_gen.command()
@click.option("--path", default="coredis/tokens.py")
@click.pass_context
def token_enum(ctx, path):
    mapping = get_token_mapping()
    env = Environment()
    env.globals.update(sorted=sorted)
    t = env.from_string(
        """

import enum


class PureToken(str, enum.Enum):
    \"\"\"
    Enum for using pure-tokens with the redis api.
    \"\"\"

    {% for token, command_usage in token_mapping.items() -%}

    #: Used by:
    #:
    {% for c in sorted(command_usage) -%}
    #:  - ``{{c}}``
    {% endfor -%}
    {{ token[0].upper() }} = "{{token[1]}}"
    
    {% endfor %}


    """
    )

    result = t.render(token_mapping=mapping)
    open(path, "w").write(result)
    print(f"Generated token enum at {path}")


@code_gen.command()
def generate_changes():
    cur_version = version.parse(coredis.__version__.split("+")[0])
    kls = coredis.Redis
    cluster_kls = coredis.RedisCluster
    new_methods = collections.defaultdict(list)
    changed_methods = collections.defaultdict(list)
    new_cluster_methods = collections.defaultdict(list)
    changed_cluster_methods = collections.defaultdict(list)
    for group in STD_GROUPS + ["server", "connection", "cluster"]:
        for cmd in get_official_commands(group):
            name = MAPPING.get(
                cmd["name"],
                cmd["name"].lower().replace(" ", "_").replace("-", "_"),
            )
            method = find_method(kls, name)
            cluster_method = find_method(cluster_kls, name)
            if method:
                vchanged = version_changed_from_doc(method.__doc__)
                vadded = version_added_from_doc(method.__doc__)
                if vadded and vadded > cur_version:
                    new_methods[group].append(method)
                if vchanged and vchanged > cur_version:
                    changed_methods[group].append(method)
            if cluster_method and method != cluster_method:
                vchanged = version_changed_from_doc(cluster_method.__doc__)
                vadded = version_added_from_doc(cluster_method.__doc__)
                if vadded and vadded > cur_version:
                    new_cluster_methods[group].append(cluster_method)
                if vchanged and vchanged > cur_version:
                    changed_cluster_methods[group].append(cluster_method)

    print("New APIs:")
    print()
    for group, methods in new_methods.items():
        print(f"    * {group.title()}:")
        print()
        for new_method in sorted(methods, key=lambda m: m.__name__):
            print(f"        * ``{kls.__name__}.{new_method.__name__}``")
        for new_method in sorted(
            new_cluster_methods.get(group, []), key=lambda m: m.__name__
        ):
            print(f"        * ``{cluster_kls.__name__}.{new_method.__name__}``")
        print()
    print()
    print("Changed APIs:")
    print()
    for group, methods in changed_methods.items():
        print(f"    * {group.title()}:")
        print()
        for changed_method in sorted(methods, key=lambda m: m.__name__):
            print(f"        * ``{kls.__name__}.{changed_method.__name__}``")
        for changed_method in sorted(
            changed_cluster_methods.get(group, []), key=lambda m: m.__name__
        ):
            print(f"        * ``{cluster_kls.__name__}.{changed_method.__name__}``")
        print()


@code_gen.command()
@click.option("--command", "-c", multiple=True)
@click.option("--group", "-g", default=None)
@click.option("--expr", "-e", default=None)
@click.pass_context
def generate_implementation(ctx, command, group, expr):
    cur_version = version.parse(coredis.__version__.split("+")[0])
    kls = coredis.Redis
    commands = []

    method_template_str = """

    {% for decorator in method["rec_decorators"] %}
    {{decorator}}
    {% endfor -%}
    @versionadded(version="{{next_version}}")
    @redis_command("{{method["command"]["name"]}}"
    {%- if method["redis_version_introduced"] > MIN_SUPPORTED_VERSION -%}
    , version_introduced="{{method["command"].get("since")}}"
    {%- endif -%}, group=CommandGroup.{{method["command"]["group"].upper().replace(" ","_").replace("-","_")}}
    {%- if len(method["arg_mapping"]) > 0 -%}
    {% set argument_with_version = {} %}
    {%- for name, arg  in method["arg_mapping"].items() -%}
    {%- for param in arg[1] -%}
    {%- if arg[0].get("since") and version_parse(arg[0].get("since")) >= MIN_SUPPORTED_VERSION -%}
    {% set _ = argument_with_version.update({param.name: {"version_introduced": arg[0].get("since")}}) %}
    {%- endif -%}
    {%- endfor -%}
    {%- endfor -%}
    {% if argument_with_version %}, arguments={{ argument_with_version }}{%endif%}
    {%- endif -%})
    async def {{method["name"]}}{{render_signature(method["rec_signature"])}}:
        \"\"\"
        {{method["summary"]}}

        {% if "rec_signature" in method %}
        {% for p in list(method["rec_signature"].parameters)[1:] %}
        :param {{p}}:
        {%- endfor %}
        {% endif %}
        {% if len(method["return_summary"]) == 0 %}
        :return: {{method["return_summary"][0]}}
        {% else %}
        :return:
        {% for desc in method["return_summary"] %}
        {{desc}}
        {%- endfor %}
        {% endif %}
        \"\"\"
        WTF?
        {% if len(method["arg_mapping"]) > 0 %}
        pieces = []
        {% for name, arg  in method["arg_mapping"].items() %}
        # Handle {{name}}
        {% if len(arg[1]) > 0 %}
        {% for param in arg[1] %}
        {% if not arg[0].get("optional") %}
        {% if arg[0].get("multiple") %}
        {% if arg[0].get("token") %}
        pieces.extend(*{{param.name}})
        {% else %}
        pieces.extend(*{{param.name}})
        {% endif %}
        {% else %}
        {% if arg[0].get("token") %}
        pieces.append("{{arg[0].get("token")}}")
        pieces.append({{param.name}})
        {% else %}
        pieces.append({{param.name}})
        {% endif %}
        {% endif %}
        {% else %}
        {% if arg[0].get("multiple") %}

        if {{arg[1][0].name}}:
            pieces.extend({{param.name}})
        {% else %}

        if {{param.name}}{% if arg[0].get("type") != "pure-token" %} is not None{%endif%}:
        {% if arg[0].get("token") %}
            pieces.append({{arg[0].get("token")}})
        {% else %}
            pieces.append({{param.name}})
        {% endif %}
        {% endif }
        {% endif %}
        {% endfor %}
        {% endif %}
        {% endfor %}

        return await self.execute_command("{{method["command"]["name"]}}", *pieces)
        {% else -%}

        return await self.execute_command("{{method["command"]["name"]}}")
        {% endif -%}
        pass
"""
    env = Environment()
    env.globals.update(
        MIN_SUPPORTED_VERSION=MIN_SUPPORTED_VERSION,
        MAX_SUPPORTED_VERSION=MAX_SUPPORTED_VERSION,
        get_official_commands=get_official_commands,
        inspect=inspect,
        len=len,
        list=list,
        version_parse=version.parse,
        skip_command=skip_command,
        redis_command_link=redis_command_link,
        find_method=find_method,
        kls=kls,
        render_signature=render_signature,
        next_version=ctx.obj["NEXT_VERSION"],
        debug=True,
    )
    method_template = env.from_string(method_template_str)

    if group:
        commands = get_official_commands(group)
    else:
        all_commands = get_official_commands()
        commands = []
        for g, group_commands in all_commands.items():
            if expr:
                rex = re.compile(expr)
                commands.extend([k for k in group_commands if rex.match(k["name"])])
            else:
                commands.extend([k for k in group_commands if k["name"] in command])

    for command in commands:
        method_details = generate_method_details(kls, command, debug)
        if method_details.get("rec_signature"):
            print(method_template.render(method=method_details))


@code_gen.command()
@click.pass_context
def generate_stubs(ctx):
    kls = coredis.Redis
    cluster_kls = coredis.RedisCluster
    commands = {}
    for group in STD_GROUPS + ["server", "connection", "cluster"]:
        for cmd in get_official_commands(group):
            name = MAPPING.get(
                cmd["name"],
                cmd["name"].lower().replace(" ", "_").replace("-", "_"),
            )
            method = find_method(kls, name)
            if method:
                signature = inspect.signature(method)
                if signature.return_annotation != inspect._empty:
                    commands[cmd["name"]] = signature.return_annotation

    stub_template_str = """
import typing
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple, Union
from coredis import BitFieldOperation

class Redis:
    {% for name, return_type in commands.items() -%}
    @overload
    async def execute_command(self, command: Literal["{{name}}"], *args: Any, **options: Any) -> {{render_annotation(return_type) }}: ...
    {% endfor %}

class RedisCluster:
    {% for name, return_type in commands.items() -%}
    @overload
    async def execute_command(self, command: Literal["{{name}}"], *args: Any, **options: Any) -> {{render_annotation(return_type) }}: ...
    {% endfor %}
"""
    env = Environment()
    env.globals.update(
        MIN_SUPPORTED_VERSION=MIN_SUPPORTED_VERSION,
        MAX_SUPPORTED_VERSION=MAX_SUPPORTED_VERSION,
        get_official_commands=get_official_commands,
        inspect=inspect,
        isinstance=isinstance,
        len=len,
        list=list,
        type=type,
        render_annotation=render_annotation,
        version_parse=version.parse,
        skip_command=skip_command,
        redis_command_link=redis_command_link,
        find_method=find_method,
        kls=kls,
        render_signature=render_signature,
        next_version=ctx.obj["NEXT_VERSION"],
        debug=True,
    )
    stub_template = env.from_string(stub_template_str)
    print(stub_template.render(commands=commands))


if __name__ == "__main__":
    code_gen()
