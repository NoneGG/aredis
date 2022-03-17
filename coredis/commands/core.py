import datetime
import itertools
from typing import (
    Any,
    AnyStr,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Union,
    overload,
)

from deprecated.sphinx import deprecated, versionadded
from typing_extensions import OrderedDict

from coredis.commands import (
    ClusterCommandConfig,
    CommandGroup,
    CommandMixin,
    redis_command,
)
from coredis.exceptions import DataError, RedisError
from coredis.response.callbacks import (
    BoolCallback,
    BoolsCallback,
    DateTimeCallback,
    DictCallback,
    FloatCallback,
    OptionalFloatCallback,
    OptionalIntCallback,
    SetCallback,
    SimpleStringCallback,
    SimpleStringOrIntCallback,
    TupleCallback,
)
from coredis.response.callbacks.acl import ACLLogCallback
from coredis.response.callbacks.cluster import (
    ClusterInfoCallback,
    ClusterNode,
    ClusterNodesCallback,
    ClusterSlotsCallback,
)
from coredis.response.callbacks.command import CommandCallback
from coredis.response.callbacks.geo import GeoCoordinatessCallback, GeoSearchCallback
from coredis.response.callbacks.hash import (
    HGetAllCallback,
    HRandFieldCallback,
    HScanCallback,
)
from coredis.response.callbacks.keys import ScanCallback, SortCallback
from coredis.response.callbacks.server import (
    ClientInfoCallback,
    ClientListCallback,
    DebugCallback,
    InfoCallback,
    RoleCallback,
    SlowlogCallback,
    TimeCallback,
)
from coredis.response.callbacks.sets import ItemOrSetCallback, SScanCallback
from coredis.response.callbacks.sorted_set import (
    VALID_ZADD_OPTIONS,
    BZPopCallback,
    ZAddCallback,
    ZMembersOrScoredMembers,
    ZMScoreCallback,
    ZRandMemberCallback,
    ZScanCallback,
    ZSetScorePairCallback,
)
from coredis.response.callbacks.streams import (
    AutoClaimCallback,
    ClaimCallback,
    MultiStreamRangeCallback,
    PendingCallback,
    StreamInfoCallback,
    StreamRangeCallback,
    XInfoCallback,
)
from coredis.response.types import (
    ClientInfo,
    Command,
    GeoCoordinates,
    GeoSearchResult,
    RoleInfo,
    ScoredMember,
    ScoredMembers,
    SlowLogInfo,
    StreamEntry,
    StreamInfo,
    StreamPending,
    StreamPendingExt,
)
from coredis.tokens import PureToken
from coredis.typing import CommandArgList, KeyT, ValueT
from coredis.utils import (
    NodeFlag,
    b,
    defaultvalue,
    dict_to_flat_list,
    iteritems,
    normalized_milliseconds,
    normalized_seconds,
    normalized_time_milliseconds,
    normalized_time_seconds,
    pairs_to_dict,
    pairs_to_ordered_dict,
    quadruples_to_dict,
    tuples_to_flat_list,
)
from coredis.validators import (
    mutually_exclusive_parameters,
    mutually_inclusive_parameters,
)

from ..response.callbacks.strings import StringSetCallback
from .builders.bitfield import BitFieldOperation


class CoreCommands(CommandMixin[AnyStr]):
    @redis_command("APPEND", group=CommandGroup.STRING)
    async def append(self, key: KeyT, value: ValueT) -> int:
        """
        Append a value to a key

        :return: the length of the string after the append operation.
        """

        return await self.execute_command("APPEND", key, value)

    @redis_command("DECR", group=CommandGroup.STRING)
    async def decr(self, key: KeyT) -> int:
        """
        Decrement the integer value of a key by one

        :return: the value of ``key`` after the decrement
        """

        return await self.decrby(key, 1)

    @redis_command("DECRBY", group=CommandGroup.STRING)
    async def decrby(self, key: KeyT, decrement: int) -> int:
        """
        Decrement the integer value of a key by the given number

        :return: the value of ``key`` after the decrement
        """

        return await self.execute_command("DECRBY", key, decrement)

    @redis_command(
        "GET",
        readonly=True,
        group=CommandGroup.STRING,
    )
    async def get(self, key: KeyT) -> Optional[AnyStr]:
        """
        Get the value of a key

        :return: the value of ``key``, or ``None`` when ``key`` does not exist.
        """
        return await self.execute_command("GET", key)

    @redis_command(
        "GETDEL",
        group=CommandGroup.STRING,
        version_introduced="6.2.0",
    )
    async def getdel(self, key: KeyT) -> Optional[AnyStr]:
        """
        Get the value of a key and delete the key


        :return: the value of ``key``, ``None`` when ``key`` does not exist,
         or an error if the key's value type isn't a string.
        """

        return await self.execute_command("GETDEL", key)

    @mutually_exclusive_parameters("ex", "px", "exat", "pxat", "persist")
    @redis_command("GETEX", group=CommandGroup.STRING, version_introduced="6.2.0")
    async def getex(
        self,
        key: KeyT,
        ex: Optional[Union[int, datetime.timedelta]] = None,
        px: Optional[Union[int, datetime.timedelta]] = None,
        exat: Optional[Union[int, datetime.datetime]] = None,
        pxat: Optional[Union[int, datetime.datetime]] = None,
        persist: Optional[bool] = None,
    ) -> Optional[AnyStr]:
        """
        Get the value of a key and optionally set its expiration


        GETEX is similar to GET, but is a write command with
        additional options. All time parameters can be given as
        :class:`datetime.timedelta` or integers.

        :param key: name of the key
        :param ex: sets an expire flag on key ``key`` for ``ex`` seconds.
        :param px: sets an expire flag on key ``key`` for ``px`` milliseconds.
        :param exat: sets an expire flag on key ``key`` for ``ex`` seconds,
         specified in unix time.
        :param pxat: sets an expire flag on key ``key`` for ``ex`` milliseconds,
         specified in unix time.
        :param persist: remove the time to live associated with ``key``.

        :return: the value of ``key``, or ``None`` when ``key`` does not exist.
        """

        pieces: List[Union[str, int]] = []

        if ex is not None:
            pieces.append("EX")
            pieces.append(normalized_seconds(ex))

        if px is not None:
            pieces.append("PX")
            pieces.append(normalized_milliseconds(px))

        if exat is not None:
            pieces.append("EXAT")
            pieces.append(normalized_time_seconds(exat))

        if pxat is not None:
            pieces.append("PXAT")
            pieces.append(normalized_time_milliseconds(pxat))

        if persist:
            pieces.append("PERSIST")

        return await self.execute_command("GETEX", key, *pieces)

    @redis_command("GETRANGE", readonly=True, group=CommandGroup.STRING)
    async def getrange(self, key: KeyT, start: int, end: int) -> AnyStr:
        """
        Get a substring of the string stored at a key

        :return: The substring of the string value stored at ``key``,
         determined by the offsets ``start`` and ``end`` (both are inclusive)
        """

        return await self.execute_command("GETRANGE", key, start, end)

    @redis_command("GETSET", version_deprecated="6.2.0", group=CommandGroup.STRING)
    async def getset(self, key: KeyT, value: ValueT) -> Optional[AnyStr]:
        """
        Set the string value of a key and return its old value

        :return: the old value stored at ``key``, or ``None`` when ``key`` did not exist.
        """

        return await self.execute_command("GETSET", key, value)

    @redis_command("INCR", group=CommandGroup.STRING)
    async def incr(self, key: KeyT) -> int:
        """
        Increment the integer value of a key by one

        :return: the value of ``key`` after the increment.
         If no key exists, the value will be initialized as 1.
        """

        return await self.incrby(key, 1)

    @redis_command("INCRBY", group=CommandGroup.STRING)
    async def incrby(self, key: KeyT, increment: int) -> int:
        """
        Increment the integer value of a key by the given amount

        :return: the value of ``key`` after the increment
          If no key exists, the value will be initialized as ``increment``
        """

        return await self.execute_command("INCRBY", key, increment)

    @redis_command(
        "INCRBYFLOAT", group=CommandGroup.STRING, response_callback=FloatCallback()
    )
    async def incrbyfloat(self, key: KeyT, increment: Union[int, float]) -> float:
        """
        Increment the float value of a key by the given amount

        :return: the value of ``key`` after the increment.
         If no key exists, the value will be initialized as ``increment``
        """

        return await self.execute_command("INCRBYFLOAT", key, increment)

    @redis_command(
        "MGET",
        readonly=True,
        group=CommandGroup.STRING,
        response_callback=TupleCallback(),
    )
    async def mget(self, keys: Iterable[KeyT]) -> Tuple[Optional[AnyStr], ...]:
        """
        Returns values ordered identically to ``keys``
        """

        return await self.execute_command("MGET", *keys)

    @redis_command(
        "MSET",
        group=CommandGroup.STRING,
        response_callback=SimpleStringCallback(),
    )
    async def mset(self, key_values: Dict[KeyT, ValueT]) -> bool:
        """
        Sets multiple keys to multiple values
        """

        return await self.execute_command("MSET", *dict_to_flat_list(key_values))

    @redis_command(
        "MSETNX", group=CommandGroup.STRING, response_callback=BoolCallback()
    )
    async def msetnx(self, key_values: Dict[KeyT, ValueT]) -> bool:
        """
        Set multiple keys to multiple values, only if none of the keys exist

        :return: Whether all the keys were set
        """

        return await self.execute_command("MSETNX", *dict_to_flat_list(key_values))

    @redis_command(
        "PSETEX",
        group=CommandGroup.STRING,
        response_callback=SimpleStringCallback(),
    )
    async def psetex(
        self,
        key: KeyT,
        milliseconds: Union[int, datetime.timedelta],
        value: ValueT,
    ) -> bool:
        """
        Set the value and expiration in milliseconds of a key
        """

        if isinstance(milliseconds, datetime.timedelta):
            ms = int(milliseconds.microseconds / 1000)
            milliseconds = (
                milliseconds.seconds + milliseconds.days * 24 * 3600
            ) * 1000 + ms

        return await self.execute_command("PSETEX", key, milliseconds, value)

    @mutually_exclusive_parameters("ex", "px", "exat", "pxat", "keepttl")
    @redis_command(
        "SET",
        group=CommandGroup.STRING,
        arguments={
            "exat": {"version_introduced": "6.2.0"},
            "pxat": {"version_introduced": "6.2.0"},
            "keepttl": {"version_introduced": "6.0.0"},
            "get": {"version_introduced": "6.2.0"},
        },
        response_callback=StringSetCallback(),
    )
    async def set(
        self,
        key: KeyT,
        value: ValueT,
        ex: Optional[Union[int, datetime.timedelta]] = None,
        px: Optional[Union[int, datetime.timedelta]] = None,
        exat: Optional[Union[int, datetime.datetime]] = None,
        pxat: Optional[Union[int, datetime.datetime]] = None,
        keepttl: Optional[bool] = None,
        condition: Optional[Literal[PureToken.NX, PureToken.XX]] = None,
        get: Optional[bool] = None,
    ) -> Optional[Union[AnyStr, bool]]:
        """
        Set the string value of a key

        :return: Whether the operation was performed successfully.

         .. warning:: If the command is issued with the ``get`` argument, the old string value
            stored at ``key`` is return regardless of success or failure - except if the ``key``
            was not found.
        """
        pieces: CommandArgList = [key, value]

        if ex is not None:
            pieces.append("EX")
            pieces.append(normalized_seconds(ex))

        if px is not None:
            pieces.append("PX")
            pieces.append(normalized_milliseconds(px))

        if exat is not None:
            pieces.append("EXAT")
            pieces.append(normalized_time_seconds(exat))

        if pxat is not None:
            pieces.append("PXAT")
            pieces.append(normalized_time_seconds(pxat))
        if keepttl:
            pieces.append(PureToken.KEEPTTL.value)
        if get:
            pieces.append(PureToken.GET.value)

        if condition:
            pieces.append(condition.value)

        return await self.execute_command("SET", *pieces)

    @redis_command(
        "SETEX",
        group=CommandGroup.STRING,
        response_callback=SimpleStringCallback(),
    )
    async def setex(
        self,
        key: KeyT,
        value: ValueT,
        seconds: Union[int, datetime.timedelta],
    ) -> bool:
        """
        Set the value of key ``key`` to ``value`` that expires in ``seconds``
        """

        return await self.execute_command(
            "SETEX", key, normalized_seconds(seconds), value
        )

    @redis_command("SETNX", group=CommandGroup.STRING, response_callback=BoolCallback())
    async def setnx(self, key: KeyT, value: ValueT) -> bool:
        """
        Sets the value of key ``key`` to ``value`` if key doesn't exist
        """

        return await self.execute_command("SETNX", key, value)

    @redis_command("SETRANGE", group=CommandGroup.STRING)
    async def setrange(self, key: KeyT, offset: int, value: ValueT) -> int:
        """
        Overwrite bytes in the value of ``key`` starting at ``offset`` with
        ``value``. If ``offset`` plus the length of ``value`` exceeds the
        length of the original value, the new value will be larger than before.

        If ``offset`` exceeds the length of the original value, null bytes
        will be used to pad between the end of the previous value and the start
        of what's being injected.

        :return: the length of the string after it was modified by the command.
        """

        return await self.execute_command("SETRANGE", key, offset, value)

    @redis_command("STRLEN", readonly=True, group=CommandGroup.STRING)
    async def strlen(self, key: KeyT) -> int:
        """
        Get the length of the value stored in a key

        :return: the length of the string at ``key``, or ``0`` when ``key`` does not
        """

        return await self.execute_command("STRLEN", key)

    @redis_command("SUBSTR", readonly=True, group=CommandGroup.STRING)
    async def substr(self, key: KeyT, start: int, end: int) -> AnyStr:
        """
        Get a substring of the string stored at a key

        :return: the substring of the string value stored at key, determined by the offsets
         ``start`` and ``end`` (both are inclusive). Negative offsets can be used in order to
         provide an offset starting from the end of the string.
        """

        return await self.execute_command("SUBSTR", key, start, end)

    @staticmethod
    def nodes_slots_to_slots_nodes(mapping):
        """
        Converts a mapping of
        {id: <node>, slots: (slot1, slot2)}
        to
        {slot1: <node>, slot2: <node>}

        Operation is expensive so use with caution
        """
        out = {}

        for node in mapping:
            for slot in node["slots"]:
                out[str(slot)] = node["id"]

        return out

    @redis_command(
        "CLUSTER ADDSLOTS",
        group=CommandGroup.CLUSTER,
        response_callback=SimpleStringCallback(),
    )
    async def cluster_addslots(self, *slots: int) -> bool:
        """
        Assign new hash slots to receiving node
        """

        return await self.execute_command("CLUSTER ADDSLOTS", *slots)

    @versionadded(version="3.0.0")
    @redis_command("ASKING", group=CommandGroup.CLUSTER)
    async def asking(self) -> bool:
        """
        Sent by cluster clients after an -ASK redirect
        """
        return await self.execute_command("ASKING")

    @versionadded(version="3.0.0")
    @redis_command("CLUSTER BUMPEPOCH", group=CommandGroup.CLUSTER)
    async def cluster_bumpepoch(self) -> AnyStr:
        """
        Advance the cluster config epoch

        :return: ``BUMPED`` if the epoch was incremented, or ``STILL``
         if the node already has the greatest config epoch in the cluster.
        """
        return await self.execute_command("CLUSTER BUMPEPOCH")

    @redis_command("CLUSTER COUNT-FAILURE-REPORTS", group=CommandGroup.CLUSTER)
    async def cluster_count_failure_reports(self, node_id: ValueT) -> int:
        """
        Return the number of failure reports active for a given node

        """
        return await self.execute_command(
            "CLUSTER COUNT-FAILURE-REPORTS", node_id=node_id
        )

    @redis_command(
        "CLUSTER COUNTKEYSINSLOT",
        group=CommandGroup.CLUSTER,
        cluster=ClusterCommandConfig(flag=NodeFlag.SLOT_ID),
    )
    async def cluster_countkeysinslot(self, slot: int) -> int:
        """
        Return the number of local keys in the specified hash slot

        Send to node based on specified slot_id
        """

        return await self.execute_command("CLUSTER COUNTKEYSINSLOT", slot, slot_id=slot)

    @redis_command(
        "CLUSTER DELSLOTS",
        group=CommandGroup.CLUSTER,
        response_callback=SimpleStringCallback(),
    )
    async def cluster_delslots(self, *slots: int) -> bool:
        """
        Set hash slots as unbound in the cluster.
        It determines by it self what node the slot is in and sends it there

        Returns a list of the results for each processed slot.
        """
        cluster_nodes = CoreCommands.nodes_slots_to_slots_nodes(
            await self.cluster_nodes()
        )
        res = list()

        for slot in slots:
            res.append(
                await self.execute_command(
                    "CLUSTER DELSLOTS", slot, node_id=cluster_nodes[str(slot)]
                )
            )

        return len(res) > 0

    @redis_command(
        "CLUSTER FAILOVER",
        group=CommandGroup.CLUSTER,
        response_callback=SimpleStringCallback(),
    )
    async def cluster_failover(
        self,
        options: Optional[Literal[PureToken.FORCE, PureToken.TAKEOVER]] = None,
    ) -> bool:
        """
        Forces a replica to perform a manual failover of its master.
        """

        pieces: CommandArgList = []
        if options is not None:
            pieces.append(options.value)
        return await self.execute_command("CLUSTER FAILOVER", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "CLUSTER FLUSHSLOTS",
        group=CommandGroup.CLUSTER,
        response_callback=SimpleStringCallback(),
    )
    async def cluster_flushslots(self) -> bool:
        """
        Delete a node's own slots information
        """
        return await self.execute_command("CLUSTER FLUSHSLOTS")

    @redis_command(
        "CLUSTER FORGET",
        group=CommandGroup.CLUSTER,
        response_callback=SimpleStringCallback(),
    )
    async def cluster_forget(self, node_id: ValueT) -> bool:
        """
        remove a node via its node ID from the set of known nodes
        of the Redis Cluster node receiving the command

        Sends to all nodes in the cluster
        """

        return await self.execute_command("CLUSTER FORGET", node_id)

    @versionadded(version="3.0.0")
    @redis_command(
        "CLUSTER GETKEYSINSLOT",
        group=CommandGroup.CLUSTER,
        response_callback=TupleCallback(),
    )
    async def cluster_getkeysinslot(self, slot: int, count: int) -> Tuple[AnyStr, ...]:
        """
        Return local key names in the specified hash slot

        :return: :paramref:`count` key names

        """
        pieces = [slot, count]
        return await self.execute_command("CLUSTER GETKEYSINSLOT", *pieces)

    @redis_command(
        "CLUSTER INFO",
        group=CommandGroup.CLUSTER,
        response_callback=ClusterInfoCallback(),
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def cluster_info(self) -> Dict[str, str]:
        """
        Provides info about Redis Cluster node state

        Sends to random node in the cluster
        """

        return await self.execute_command("CLUSTER INFO")

    @redis_command(
        "CLUSTER KEYSLOT",
        group=CommandGroup.CLUSTER,
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def cluster_keyslot(self, key: ValueT) -> int:
        """
        Returns the hash slot of the specified key
        """

        return await self.execute_command("CLUSTER KEYSLOT", key)

    @redis_command(
        "CLUSTER MEET",
        group=CommandGroup.CLUSTER,
        response_callback=SimpleStringCallback(),
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def cluster_meet(self, ip: ValueT, port: int) -> bool:
        """
        Force a node cluster to handshake with another node.
        """

        return await self.execute_command("CLUSTER MEET", ip, port)

    @redis_command(
        "CLUSTER NODES",
        group=CommandGroup.CLUSTER,
        response_callback=ClusterNodesCallback(),
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def cluster_nodes(self) -> List[Dict[str, str]]:
        """
        Get Cluster config for the node
        """

        return await self.execute_command("CLUSTER NODES")

    @redis_command(
        "CLUSTER REPLICATE",
        group=CommandGroup.CLUSTER,
        response_callback=SimpleStringCallback(),
    )
    async def cluster_replicate(self, node_id: ValueT) -> bool:
        """
        Reconfigure a node as a replica of the specified master node

        Sends to specified node
        """

        return await self.execute_command("CLUSTER REPLICATE", node_id)

    @redis_command(
        "CLUSTER RESET",
        group=CommandGroup.CLUSTER,
        response_callback=SimpleStringCallback(),
    )
    async def cluster_reset(
        self,
        *,
        hard_soft: Optional[Literal[PureToken.HARD, PureToken.SOFT]] = None,
    ) -> bool:
        """
        Reset a Redis Cluster node
        """

        pieces: CommandArgList = []
        if hard_soft is not None:
            pieces.append(hard_soft.value)
        return await self.execute_command("CLUSTER RESET", *pieces)

    @redis_command(
        "CLUSTER SAVECONFIG",
        group=CommandGroup.CLUSTER,
        response_callback=SimpleStringCallback(),
    )
    async def cluster_saveconfig(self) -> bool:
        """
        Forces the node to save cluster state on disk

        Sends to all nodes in the cluster
        """

        return await self.execute_command("CLUSTER SAVECONFIG")

    @redis_command(
        "CLUSTER SET-CONFIG-EPOCH",
        group=CommandGroup.CLUSTER,
        response_callback=SimpleStringCallback(),
    )
    async def cluster_set_config_epoch(self, config_epoch: int) -> bool:
        """
        Set the configuration epoch in a new node
        """

        return await self.execute_command("CLUSTER SET-CONFIG-EPOCH", config_epoch)

    @mutually_exclusive_parameters("importing", "migrating", "node", "stable")
    @redis_command(
        "CLUSTER SETSLOT",
        group=CommandGroup.CLUSTER,
        response_callback=SimpleStringCallback(),
    )
    async def cluster_setslot(
        self,
        slot: int,
        importing: Optional[ValueT] = None,
        migrating: Optional[ValueT] = None,
        node: Optional[ValueT] = None,
        stable: Optional[bool] = None,
    ) -> bool:
        """
        Bind a hash slot to a specific node
        """

        pieces: CommandArgList = []
        if importing is not None:
            pieces.extend(["IMPORTING", importing])
        if migrating is not None:
            pieces.extend(["MIGRATING", migrating])
        if node is not None:
            pieces.extend(["NODE", node])
        if stable is not None:
            pieces.append(PureToken.STABLE.value)
        return await self.execute_command("CLUSTER SETSLOT", slot, *pieces)

    async def cluster_get_keys_in_slot(self, slot_id, count):
        """
        Return local key names in the specified hash slot
        Sends to specified node
        """

        return await self.execute_command("CLUSTER GETKEYSINSLOT", slot_id, count)

    @redis_command(
        "CLUSTER REPLICAS",
        group=CommandGroup.CLUSTER,
        response_callback=ClusterNodesCallback(),
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def cluster_replicas(self, node_id: ValueT) -> List[Dict[AnyStr, AnyStr]]:
        """
        List replica nodes of the specified master node
        """

        return await self.execute_command("CLUSTER REPLICAS", node_id)

    @redis_command(
        "CLUSTER SLAVES",
        version_deprecated="5.0.0",
        group=CommandGroup.CLUSTER,
        response_callback=ClusterNodesCallback(),
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def cluster_slaves(self, node_id: ValueT) -> List[Dict[AnyStr, AnyStr]]:
        """
        List replica nodes of the specified master node
        """

        return await self.execute_command("CLUSTER SLAVES", node_id)

    @redis_command(
        "CLUSTER SLOTS",
        group=CommandGroup.CLUSTER,
        response_callback=ClusterSlotsCallback(),
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def cluster_slots(
        self,
    ) -> Dict[Tuple[int, int], Tuple[ClusterNode, ...]]:
        """
        Get mapping of Cluster slot to nodes
        """

        return await self.execute_command("CLUSTER SLOTS")

    @versionadded(version="3.0.0")
    @redis_command(
        "AUTH",
        group=CommandGroup.CONNECTION,
        arguments={"username": {"version_introduced": "6.0.0"}},
        response_callback=SimpleStringCallback(),
    )
    async def auth(self, password: ValueT, username: Optional[ValueT] = None) -> bool:
        """
        Authenticate to the server
        """
        pieces = []
        pieces.append(password)

        if username is not None:
            pieces.append(username)

        return await self.execute_command("AUTH", *pieces)

    @redis_command(
        "ECHO",
        group=CommandGroup.CONNECTION,
    )
    async def echo(self, message: ValueT) -> AnyStr:
        "Echo the string back from the server"

        return await self.execute_command("ECHO", message)

    @versionadded(version="3.0.0")
    @redis_command(
        "HELLO",
        version_introduced="6.0.0",
        group=CommandGroup.CONNECTION,
        response_callback=DictCallback(transform_function=pairs_to_dict),
    )
    async def hello(
        self,
        protover: Optional[int] = None,
        username: Optional[ValueT] = None,
        password: Optional[ValueT] = None,
        setname: Optional[ValueT] = None,
    ) -> Dict[AnyStr, AnyStr]:
        """
        Handshake with Redis

        :return: a mapping of server properties.
        """
        pieces: CommandArgList = []
        if protover is not None:
            pieces.append(protover)
        if username is not None:
            pieces.append(username)
        if password is not None:
            pieces.append(password)
        if setname is not None:
            pieces.append(setname)
        return await self.execute_command("HELLO", *pieces)

    @redis_command(
        "PING",
        group=CommandGroup.CONNECTION,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def ping(self, message: Optional[ValueT] = None) -> AnyStr:
        """
        Ping the server

        :return: ``PONG``, when no argument is provided.
         the argument provided, when applicable.
        """
        pieces: CommandArgList = []

        if message:
            pieces.append(message)

        return await self.execute_command("PING", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "SELECT",
        group=CommandGroup.CONNECTION,
        response_callback=SimpleStringCallback(),
    )
    async def select(self, index: int) -> bool:
        """
        Change the selected database for the current connection
        """
        return await self.execute_command("SELECT", index)

    @redis_command(
        "QUIT",
        group=CommandGroup.CONNECTION,
        response_callback=SimpleStringCallback(),
    )
    async def quit(self) -> bool:
        """
        Close the connection

        :return: always OK.
        """

        return await self.execute_command("QUIT")

    @versionadded(version="3.0.0")
    @redis_command("RESET", version_introduced="6.2.0", group=CommandGroup.CONNECTION)
    async def reset(self) -> None:
        """
        Reset the connection
        """
        await self.execute_command("RESET")

    @redis_command(
        "GEOADD",
        group=CommandGroup.GEO,
        arguments={
            "condition": {"version_introduced": "6.2.0"},
            "change": {"version_introduced": "6.2.0"},
        },
    )
    async def geoadd(
        self,
        key: KeyT,
        longitude_latitude_members: Iterable[
            Tuple[Union[int, float], Union[int, float], ValueT]
        ],
        condition: Optional[Literal[PureToken.NX, PureToken.XX]] = None,
        change: Optional[bool] = None,
    ) -> int:
        """
        Add the specified geospatial items to the specified key identified
        by the ``key`` argument. The Geospatial items are given as ordered
        members of the ``values`` argument, each item or place is formed by
        the triad latitude, longitude and name."""

        return await self.execute_command(
            "GEOADD", key, *tuples_to_flat_list(longitude_latitude_members)
        )

    @redis_command(
        "GEODIST",
        readonly=True,
        group=CommandGroup.GEO,
        response_callback=OptionalFloatCallback(),
    )
    async def geodist(
        self,
        key: KeyT,
        member1: ValueT,
        member2: ValueT,
        unit: Optional[
            Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI]
        ] = None,
    ) -> Optional[float]:
        """
        Return the distance between ``place1`` and ``place2`` members of the
        ``key`` key.
        The units must be one of the following : m, km mi, ft. By async default
        meters are used.
        """
        pieces: CommandArgList = [key, member1, member2]

        if unit:
            pieces.append(unit.value.lower())

        return await self.execute_command("GEODIST", *pieces)

    @redis_command(
        "GEOHASH",
        readonly=True,
        group=CommandGroup.GEO,
        response_callback=TupleCallback(),
    )
    async def geohash(self, key: KeyT, members: Iterable[ValueT]) -> Tuple[AnyStr, ...]:
        """
        Return the geo hash string for each item of ``values`` members of
        the specified key identified by the ``key`` argument.
        """

        return await self.execute_command("GEOHASH", key, *members)

    @redis_command(
        "GEOPOS",
        readonly=True,
        group=CommandGroup.GEO,
        response_callback=GeoCoordinatessCallback(),
    )
    async def geopos(
        self, key: KeyT, *members: ValueT
    ) -> Tuple[Optional[GeoCoordinates], ...]:
        """
        Return the positions of each item of ``values`` as members of
        the specified key identified by the ``key`` argument. Each position
        is represented by the pairs lon and lat.
        """

        return await self.execute_command("GEOPOS", key, *members)

    @overload
    async def georadius(
        self,
        key: KeyT,
        longitude: Union[int, float],
        latitude: Union[int, float],
        radius: Union[int, float],
        unit: Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI],
    ) -> Tuple[AnyStr, ...]:
        ...

    @overload
    async def georadius(
        self,
        key: KeyT,
        longitude: Union[int, float],
        latitude: Union[int, float],
        radius: Union[int, float],
        unit: Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI],
        *,
        withcoord: Literal[True],
        withdist: Any = ...,
        withhash: Any = ...,
    ) -> Tuple[GeoSearchResult, ...]:
        ...

    @overload
    async def georadius(
        self,
        key: KeyT,
        longitude: Union[int, float],
        latitude: Union[int, float],
        radius: Union[int, float],
        unit: Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI],
        *,
        withcoord: Any = ...,
        withdist: Literal[True],
        withhash: Any = ...,
    ) -> Tuple[GeoSearchResult, ...]:
        ...

    @overload
    async def georadius(
        self,
        key: KeyT,
        longitude: Union[int, float],
        latitude: Union[int, float],
        radius: Union[int, float],
        unit: Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI],
        *,
        withcoord: Any = ...,
        withdist: Any = ...,
        withhash: Literal[True],
    ) -> Tuple[GeoSearchResult, ...]:
        ...

    @overload
    async def georadius(
        self,
        key: KeyT,
        longitude: Union[int, float],
        latitude: Union[int, float],
        radius: Union[int, float],
        unit: Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI],
        *,
        store: KeyT,
    ) -> int:
        ...

    @overload
    async def georadius(
        self,
        key: KeyT,
        longitude: Union[int, float],
        latitude: Union[int, float],
        radius: Union[int, float],
        unit: Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI],
        *,
        withcoord: Any = ...,
        withdist: Any = ...,
        withhash: Any = ...,
        storedist: KeyT,
    ) -> int:
        ...

    @mutually_exclusive_parameters("store", "storedist")
    @mutually_exclusive_parameters("store", ("withdist", "withhash", "withcoord"))
    @mutually_exclusive_parameters("storedist", ("withdist", "withhash", "withcoord"))
    @redis_command(
        "GEORADIUS",
        version_deprecated="6.2.0",
        group=CommandGroup.GEO,
        arguments={"any_": {"version_introduced": "6.2.0"}},
        response_callback=GeoSearchCallback(),
    )
    async def georadius(
        self,
        key: KeyT,
        longitude: Union[int, float],
        latitude: Union[int, float],
        radius: Union[int, float],
        unit: Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI],
        *,
        withcoord: Optional[bool] = None,
        withdist: Optional[bool] = None,
        withhash: Optional[bool] = None,
        count: Optional[int] = None,
        any_: Optional[bool] = None,
        order: Optional[Literal[PureToken.ASC, PureToken.DESC]] = None,
        store: Optional[KeyT] = None,
        storedist: Optional[KeyT] = None,
    ) -> Union[int, Tuple[Union[AnyStr, GeoSearchResult], ...]]:
        """ """

        return await self._georadiusgeneric(
            "GEORADIUS",
            key,
            longitude,
            latitude,
            radius,
            unit=unit,
            withdist=withdist,
            withcoord=withcoord,
            withhash=withhash,
            count=count,
            order=order,
            store=store,
            storedist=storedist,
            any_=any_,
        )

    @redis_command(
        "GEORADIUSBYMEMBER",
        version_deprecated="6.2.0",
        group=CommandGroup.GEO,
        response_callback=GeoSearchCallback(),
    )
    async def georadiusbymember(
        self,
        key: KeyT,
        member: ValueT,
        radius: Union[int, float],
        unit: Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI],
        withcoord: Optional[bool] = None,
        withdist: Optional[bool] = None,
        withhash: Optional[bool] = None,
        count: Optional[int] = None,
        any_: Optional[bool] = None,
        order: Optional[Literal[PureToken.ASC, PureToken.DESC]] = None,
        store: Optional[KeyT] = None,
        storedist: Optional[KeyT] = None,
    ) -> Union[int, Tuple[Union[AnyStr, GeoSearchResult], ...]]:
        """
        This command is exactly like ``georadius`` with the sole difference
        that instead of taking, as the center of the area to query, a longitude
        and latitude value, it takes the name of a member already existing
        inside the geospatial index represented by the sorted set.
        """

        return await self._georadiusgeneric(
            "GEORADIUSBYMEMBER",
            key,
            member,
            radius,
            unit=unit,
            withdist=withdist,
            withcoord=withcoord,
            withhash=withhash,
            count=count,
            order=order,
            store=store,
            storedist=storedist,
            any_=any_,
        )

    async def _georadiusgeneric(self, command, *args, **kwargs):
        pieces = list(args)

        if kwargs["unit"]:
            pieces.append(kwargs["unit"].value.lower())

        if kwargs["any_"] and kwargs["count"] is None:
            raise DataError("``any`` can't be provided without ``count``")

        for arg_name, byte_repr in (
            ("withdist", "WITHDIST"),
            ("withcoord", "WITHCOORD"),
            ("withhash", "WITHHASH"),
        ):
            if kwargs[arg_name]:
                pieces.append(byte_repr)

        if kwargs["count"] is not None:
            pieces.extend(["COUNT", kwargs["count"]])

            if kwargs["any_"]:
                pieces.append("ANY")

        if kwargs["order"]:
            pieces.append(kwargs["order"].value)

        if kwargs["store"] and kwargs["storedist"]:
            raise DataError("GEORADIUS store and storedist cant be set" " together")

        if kwargs["store"]:
            pieces.extend(["STORE", kwargs["store"]])

        if kwargs["storedist"]:
            pieces.extend(["STOREDIST", kwargs["storedist"]])

        return await self.execute_command(command, *pieces, **kwargs)

    @mutually_inclusive_parameters("longitude", "latitude")
    @mutually_inclusive_parameters("radius", "circle_unit")
    @mutually_inclusive_parameters("width", "height", "box_unit")
    @redis_command(
        "GEOSEARCH",
        readonly=True,
        version_introduced="6.2.0",
        group=CommandGroup.GEO,
        response_callback=GeoSearchCallback(),
    )
    async def geosearch(
        self,
        key: KeyT,
        member: Optional[ValueT] = None,
        longitude: Optional[Union[int, float]] = None,
        latitude: Optional[Union[int, float]] = None,
        radius: Optional[Union[int, float]] = None,
        circle_unit: Optional[
            Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI]
        ] = None,
        width: Optional[Union[int, float]] = None,
        height: Optional[Union[int, float]] = None,
        box_unit: Optional[
            Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI]
        ] = None,
        order: Optional[Literal[PureToken.ASC, PureToken.DESC]] = None,
        count: Optional[int] = None,
        any_: Optional[bool] = None,
        withcoord: Optional[bool] = None,
        withdist: Optional[bool] = None,
        withhash: Optional[bool] = None,
    ) -> Union[int, Tuple[Union[AnyStr, GeoSearchResult], ...]]:
        """ """

        return await self._geosearchgeneric(
            "GEOSEARCH",
            key,
            member=member,
            longitude=longitude,
            latitude=latitude,
            unit=circle_unit or box_unit,
            radius=radius,
            width=width,
            height=height,
            order=order,
            count=count,
            any_=any_,
            withcoord=withcoord,
            withdist=withdist,
            withhash=withhash,
            store=None,
            storedist=None,
        )

    @mutually_inclusive_parameters("longitude", "latitude")
    @mutually_inclusive_parameters("radius", "circle_unit")
    @mutually_inclusive_parameters("width", "height", "box_unit")
    @redis_command("GEOSEARCHSTORE", version_introduced="6.2.0", group=CommandGroup.GEO)
    async def geosearchstore(
        self,
        destination: KeyT,
        source: KeyT,
        member: Optional[ValueT] = None,
        longitude: Optional[Union[int, float]] = None,
        latitude: Optional[Union[int, float]] = None,
        radius: Optional[Union[int, float]] = None,
        circle_unit: Optional[
            Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI]
        ] = None,
        width: Optional[Union[int, float]] = None,
        height: Optional[Union[int, float]] = None,
        box_unit: Optional[
            Literal[PureToken.M, PureToken.KM, PureToken.FT, PureToken.MI]
        ] = None,
        order: Optional[Literal[PureToken.ASC, PureToken.DESC]] = None,
        count: Optional[int] = None,
        any_: Optional[bool] = None,
        storedist: Optional[bool] = None,
    ) -> int:
        """ """

        return await self._geosearchgeneric(
            "GEOSEARCHSTORE",
            destination,
            source,
            member=member,
            longitude=longitude,
            latitude=latitude,
            unit=circle_unit or box_unit,
            radius=radius,
            width=width,
            height=height,
            count=count,
            order=order,
            any_=any_,
            withcoord=None,
            withdist=None,
            withhash=None,
            store=None,
            storedist=storedist,
        )

    async def _geosearchgeneric(self, command, *args, **kwargs):
        pieces = list(args)

        if kwargs["member"] is None:
            if kwargs["longitude"] is None or kwargs["latitude"] is None:
                raise DataError(
                    "GEOSEARCH must have member or" " longitude and latitude"
                )

        if kwargs["member"]:
            if kwargs["longitude"] or kwargs["latitude"]:
                raise DataError(
                    "GEOSEARCH member and longitude or latitude" " cant be set together"
                )
            pieces.extend(["FROMMEMBER", kwargs["member"]])

        if kwargs["longitude"] and kwargs["latitude"]:
            pieces.extend(["FROMLONLAT", kwargs["longitude"], kwargs["latitude"]])

        # BYRADIUS or BYBOX

        if kwargs["radius"] is None:
            if kwargs["width"] is None or kwargs["height"] is None:
                raise DataError("GEOSEARCH must have radius or" " width and height")

        if kwargs["unit"] is None:
            raise DataError("GEOSEARCH must have unit")

        if kwargs["unit"].value.lower() not in ("m", "km", "mi", "ft"):
            raise DataError("GEOSEARCH invalid unit")

        if kwargs["radius"]:
            if kwargs["width"] or kwargs["height"]:
                raise DataError(
                    "GEOSEARCH radius and width or height" " cant be set together"
                )
            pieces.extend(["BYRADIUS", kwargs["radius"], kwargs["unit"].value.lower()])

        if kwargs["width"] and kwargs["height"]:
            pieces.extend(
                [
                    "BYBOX",
                    kwargs["width"],
                    kwargs["height"],
                    kwargs["unit"].value.lower(),
                ]
            )

        # sort

        if kwargs["order"]:
            pieces.append(kwargs["order"].value)

        # count any

        if kwargs["count"]:
            pieces.extend(["COUNT", kwargs["count"]])

            if kwargs["any_"]:
                pieces.append(PureToken.ANY.value)
        elif kwargs["any_"]:
            raise DataError("GEOSEARCH ``any`` can't be provided " "without count")

        # other properties

        for arg_name, byte_repr in (
            ("withdist", PureToken.WITHDIST.value),
            ("withcoord", PureToken.WITHCOORD.value),
            ("withhash", PureToken.WITHHASH.value),
            ("storedist", PureToken.STOREDIST.value),
        ):
            if kwargs[arg_name]:
                pieces.append(byte_repr)

        return await self.execute_command(command, *pieces, **kwargs)

    @redis_command("HDEL", group=CommandGroup.HASH)
    async def hdel(self, key: KeyT, fields: Iterable[ValueT]) -> int:
        """Deletes ``fields`` from hash ``key``"""

        return await self.execute_command("HDEL", key, *fields)

    @redis_command(
        "HEXISTS",
        readonly=True,
        group=CommandGroup.HASH,
        response_callback=BoolCallback(),
    )
    async def hexists(self, key: KeyT, field: ValueT) -> bool:
        """
        Returns a boolean indicating if ``field`` exists within hash ``key``
        """

        return await self.execute_command("HEXISTS", key, field)

    @redis_command("HGET", readonly=True, group=CommandGroup.HASH)
    async def hget(self, key: KeyT, field: ValueT) -> Optional[AnyStr]:
        """Returns the value of ``field`` within the hash ``key``"""

        return await self.execute_command("HGET", key, field)

    @redis_command(
        "HGETALL",
        readonly=True,
        group=CommandGroup.HASH,
        response_callback=HGetAllCallback(),
    )
    async def hgetall(self, key: KeyT) -> Dict[AnyStr, AnyStr]:
        """Returns a Python dict of the hash's name/value pairs"""

        return await self.execute_command("HGETALL", key)

    @redis_command("HINCRBY", group=CommandGroup.HASH)
    async def hincrby(self, key: KeyT, field: ValueT, increment: int) -> int:
        """Increments the value of ``field`` in hash ``key`` by ``increment``"""

        return await self.execute_command("HINCRBY", key, field, increment)

    @redis_command(
        "HINCRBYFLOAT", group=CommandGroup.HASH, response_callback=FloatCallback()
    )
    async def hincrbyfloat(
        self, key: KeyT, field: ValueT, increment: Union[int, float]
    ) -> float:
        """
        Increments the value of ``field`` in hash ``key`` by floating
        ``increment``
        """

        return await self.execute_command("HINCRBYFLOAT", key, field, increment)

    @redis_command(
        "HKEYS",
        readonly=True,
        group=CommandGroup.HASH,
        response_callback=TupleCallback(),
    )
    async def hkeys(self, key: KeyT) -> Tuple[AnyStr, ...]:
        """Returns the list of keys within hash ``key``"""

        return await self.execute_command("HKEYS", key)

    @redis_command("HLEN", readonly=True, group=CommandGroup.HASH)
    async def hlen(self, key: KeyT) -> int:
        """Returns the number of elements in hash ``key``"""

        return await self.execute_command("HLEN", key)

    @redis_command("HSET", group=CommandGroup.HASH)
    async def hset(self, key: KeyT, field_values: Dict[ValueT, ValueT]) -> int:
        """
        Sets ``field`` to ``value`` within hash ``key``

        :return: number of fields that were added
        """

        return await self.execute_command("HSET", key, *dict_to_flat_list(field_values))

    @redis_command("HSETNX", group=CommandGroup.HASH, response_callback=BoolCallback())
    async def hsetnx(self, key: KeyT, field: ValueT, value: ValueT) -> bool:
        """
        Sets ``field`` to ``value`` within hash ``key`` if ``field`` does not
        exist.

        :return: whether the field was created
        """

        return await self.execute_command("HSETNX", key, field, value)

    @redis_command(
        "HMSET",
        group=CommandGroup.HASH,
        response_callback=SimpleStringCallback(),
    )
    async def hmset(self, key: KeyT, field_values: Dict[ValueT, ValueT]) -> bool:
        """
        Sets key to value within hash ``key`` for each corresponding
        key and value from the ``field_items`` dict.
        """

        if not field_values:
            raise DataError("'hmset' with 'field_values' of length 0")
        pieces: CommandArgList = []

        for pair in iteritems(field_values):
            pieces.extend(pair)

        return await self.execute_command("HMSET", key, *pieces)

    @redis_command(
        "HMGET",
        readonly=True,
        group=CommandGroup.HASH,
        response_callback=TupleCallback(),
    )
    async def hmget(self, key: KeyT, fields: Iterable[ValueT]) -> Tuple[AnyStr, ...]:
        """Returns values ordered identically to ``fields``"""

        return await self.execute_command("HMGET", key, *fields)

    @redis_command(
        "HVALS",
        readonly=True,
        group=CommandGroup.HASH,
        response_callback=TupleCallback(),
    )
    async def hvals(self, key: KeyT) -> Tuple[AnyStr, ...]:
        """
        Get all the values in a hash

        :return: list of values in the hash, or an empty list when ``key`` does not exist.
        """

        return await self.execute_command("HVALS", key)

    @redis_command(
        "HSCAN",
        readonly=True,
        group=CommandGroup.HASH,
        response_callback=HScanCallback(),
    )
    async def hscan(
        self,
        key: KeyT,
        cursor: Optional[int] = 0,
        match: Optional[ValueT] = None,
        count: Optional[int] = None,
    ) -> Tuple[int, Dict[AnyStr, AnyStr]]:

        """
        Incrementallys return key/value slices in a hash. Also returns a
        cursor pointing to the scan position.

        :param match: allows for filtering the keys by pattern
        :param count: allows for hint the minimum number of returns
        """
        pieces: CommandArgList = [key, cursor or "0"]

        if match is not None:
            pieces.extend([b("MATCH"), match])

        if count is not None:
            pieces.extend([b("COUNT"), count])

        return await self.execute_command("HSCAN", *pieces)

    @redis_command("HSTRLEN", readonly=True, group=CommandGroup.HASH)
    async def hstrlen(self, key: KeyT, field: ValueT) -> int:
        """
        Get the length of the value of a hash field

        :return: the string length of the value associated with ``field``,
         or zero when ``field`` is not present in the hash or ``key`` does not exist at all.
        """

        return await self.execute_command("HSTRLEN", key, field)

    @redis_command(
        "HRANDFIELD",
        readonly=True,
        version_introduced="6.2.0",
        group=CommandGroup.HASH,
        response_callback=HRandFieldCallback(),
    )
    async def hrandfield(
        self,
        key: KeyT,
        count: Optional[int] = None,
        withvalues: Optional[bool] = None,
    ) -> Union[AnyStr, Tuple[AnyStr, ...], Dict[AnyStr, AnyStr]]:
        """
        Return a random field from the hash value stored at key.

        :return:  Without the additional ``count`` argument, the command returns a randomly
         selected field, or ``None`` when ``key`` does not exist.
         When the additional ``count`` argument is passed, the command returns fields,
         or an empty tuple when ``key`` does not exist.

         If ``withvalues``  is ``True``, the reply is a mapping of fields and
         their values from the hash.

        """
        params: CommandArgList = []
        options = {"withvalues": withvalues, "count": count}

        if count is not None:
            params.append(count)

        if withvalues:
            params.append("WITHVALUES")
            options["withvalues"] = True

        return await self.execute_command("HRANDFIELD", key, *params, **options)

    @redis_command(
        "PFADD", group=CommandGroup.HYPERLOGLOG, response_callback=BoolCallback()
    )
    async def pfadd(
        self, key: KeyT, elements: Optional[Iterable[ValueT]] = None
    ) -> bool:

        """
        Adds the specified elements to the specified HyperLogLog.

        :return: Whether atleast 1 HyperLogLog internal register was altered
        """
        pieces: CommandArgList = []
        if elements:
            pieces.extend(elements)
        return await self.execute_command("PFADD", key, *pieces)

    @redis_command(
        "PFCOUNT",
        readonly=True,
        group=CommandGroup.HYPERLOGLOG,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def pfcount(self, keys: Iterable[KeyT]) -> int:
        """
        Return the approximated cardinality of the set(s) observed by the HyperLogLog at key(s).

        :return: The approximated number of unique elements observed via :meth:`pfadd`.
        """

        return await self.execute_command("PFCOUNT", *keys)

    @redis_command(
        "PFMERGE",
        group=CommandGroup.HYPERLOGLOG,
        response_callback=SimpleStringCallback(),
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def pfmerge(self, destkey: KeyT, sourcekeys: Iterable[KeyT]) -> bool:
        """
        Merge N different HyperLogLogs into a single one
        """

        return await self.execute_command("PFMERGE", destkey, *sourcekeys)

    @versionadded(version="3.0.0")
    @redis_command(
        "COPY",
        version_introduced="6.2.0",
        group=CommandGroup.GENERIC,
        response_callback=BoolCallback(),
    )
    async def copy(
        self,
        source: KeyT,
        destination: KeyT,
        db: Optional[int] = None,
        replace: Optional[bool] = None,
    ) -> bool:
        """
        Copy a key
        """
        pieces: CommandArgList = []

        if db is not None:
            pieces.extend(["DB", db])

        if replace:
            pieces.append("REPLACE")

        return await self.execute_command("COPY", source, destination, *pieces)

    @redis_command("DEL", group=CommandGroup.GENERIC)
    async def delete(self, keys: Iterable[KeyT]) -> int:
        """
        Delete one or more keys specified by ``keys``

        :return: The number of keys that were removed.
        """

        return await self.execute_command("DEL", *keys)

    @redis_command("DUMP", readonly=True, group=CommandGroup.GENERIC)
    async def dump(self, key: KeyT) -> bytes:
        """
        Return a serialized version of the value stored at the specified key.

        :return: the serialized value
        """

        return await self.execute_command("DUMP", key, decode=False)

    @redis_command(
        "EXISTS",
        readonly=True,
        group=CommandGroup.GENERIC,
        response_callback=BoolCallback(),
    )
    async def exists(self, keys: Iterable[KeyT]) -> int:
        """
        Determine if a key exists

        :return: the number of keys that exist from those specified as arguments.
        """

        return await self.execute_command("EXISTS", *keys)

    @redis_command(
        "EXPIRE", group=CommandGroup.GENERIC, response_callback=BoolCallback()
    )
    async def expire(self, key: KeyT, seconds: Union[int, datetime.timedelta]) -> bool:
        """
        Set a key's time to live in seconds



        :return: if the timeout was set or not set.
         e.g. key doesn't exist, or operation skipped due to the provided arguments.
        """

        return await self.execute_command("EXPIRE", key, normalized_seconds(seconds))

    @redis_command(
        "EXPIREAT", group=CommandGroup.GENERIC, response_callback=BoolCallback()
    )
    async def expireat(
        self,
        key: KeyT,
        unix_time_seconds: Union[int, datetime.datetime],
    ) -> bool:
        """
        Set the expiration for a key to a specific time


        :return: if the timeout was set or no.
         e.g. key doesn't exist, or operation skipped due to the provided arguments.

        """

        return await self.execute_command(
            "EXPIREAT", key, normalized_time_seconds(unix_time_seconds)
        )

    @redis_command(
        "KEYS",
        readonly=True,
        group=CommandGroup.GENERIC,
        response_callback=SetCallback(),
        cluster=ClusterCommandConfig(
            flag=NodeFlag.PRIMARIES,
            combine=lambda r: set(itertools.chain(*r.values())),
            pipeline=False,
        ),
    )
    async def keys(self, pattern: ValueT = "*") -> Set[AnyStr]:
        """
        Find all keys matching the given pattern

        :return: keys matching ``pattern``.
        """

        return await self.execute_command("KEYS", pattern)

    @versionadded(version="3.0.0")
    @mutually_inclusive_parameters("username", "password")
    @redis_command(
        "MIGRATE",
        group=CommandGroup.GENERIC,
        arguments={
            "username": {"version_introduced": "6.0.0"},
            "password": {"version_introduced": "6.0.0"},
        },
        response_callback=SimpleStringCallback(),
    )
    async def migrate(
        self,
        host: ValueT,
        port: int,
        destination_db: int,
        timeout: int,
        *keys: KeyT,
        copy: Optional[bool] = None,
        replace: Optional[bool] = None,
        auth: Optional[ValueT] = None,
        username: Optional[ValueT] = None,
        password: Optional[ValueT] = None,
    ) -> bool:
        """
        Atomically transfer key(s) from a Redis instance to another one.


        :return: If all keys were found found in the source instance.
        """

        if not keys:
            raise DataError("MIGRATE requires at least one key")
        pieces: CommandArgList = []

        if copy:
            pieces.append("COPY")

        if replace:
            pieces.append("REPLACE")

        if auth:
            pieces.append("AUTH")
            pieces.append(auth)

        if username and password:
            pieces.append("AUTH2")
            pieces.append(username)
            pieces.append(password)

        pieces.append("KEYS")
        pieces.extend(keys)

        return await self.execute_command(
            "MIGRATE", host, port, "", destination_db, timeout, *pieces
        )

    @redis_command("MOVE", group=CommandGroup.GENERIC, response_callback=BoolCallback())
    async def move(self, key: KeyT, db: int) -> bool:
        """Move a key to another database"""

        return await self.execute_command("MOVE", key, db)

    @redis_command("OBJECT ENCODING", readonly=True, group=CommandGroup.GENERIC)
    async def object_encoding(self, key: KeyT) -> Optional[AnyStr]:
        """
        Return the internal encoding for the object stored at ``key``

        :return: the encoding of the object, or ``None`` if the key doesn't exist
        """

        return await self.execute_command("OBJECT ENCODING", key)

    @redis_command("OBJECT FREQ", readonly=True, group=CommandGroup.GENERIC)
    async def object_freq(self, key: KeyT) -> int:
        """
        Return the logarithmic access frequency counter for the object
        stored at ``key``

        :return: The counter's value.
        """

        return await self.execute_command("OBJECT FREQ", key)

    @redis_command("OBJECT IDLETIME", readonly=True, group=CommandGroup.GENERIC)
    async def object_idletime(self, key: KeyT) -> int:
        """
        Return the time in seconds since the last access to the object
        stored at ``key``

        :return: The idle time in seconds.
        """

        return await self.execute_command("OBJECT IDLETIME", key)

    @redis_command("OBJECT REFCOUNT", readonly=True, group=CommandGroup.GENERIC)
    async def object_refcount(self, key: KeyT) -> int:
        """
        Return the reference count of the object stored at ``key``

        :return: The number of references.
        """

        return await self.execute_command("OBJECT REFCOUNT", key)

    @deprecated(
        reason="""
            Use explicit methods:

                - :meth:`object_encoding`
                - :meth:`object_freq`
                - :meth:`object_idletime`
                - :meth:`object_refcount`
            """,
        version="3.0.0",
    )
    async def object(self, infotype, key):
        """Returns the encoding, idletime, or refcount about the key"""

        return await self.execute_command("OBJECT", infotype, key, infotype=infotype)

    @redis_command(
        "PERSIST", group=CommandGroup.GENERIC, response_callback=BoolCallback()
    )
    async def persist(self, key: KeyT) -> bool:
        """Removes an expiration on ``key``"""

        return await self.execute_command("PERSIST", key)

    @redis_command(
        "PEXPIRE", group=CommandGroup.GENERIC, response_callback=BoolCallback()
    )
    async def pexpire(
        self, key: KeyT, milliseconds: Union[int, datetime.timedelta]
    ) -> bool:
        """
        Set a key's time to live in milliseconds

        :return: if the timeout was set or not.
         e.g. key doesn't exist, or operation skipped due to the provided arguments.
        """

        return await self.execute_command(
            "PEXPIRE", key, normalized_milliseconds(milliseconds)
        )

    @redis_command(
        "PEXPIREAT", group=CommandGroup.GENERIC, response_callback=BoolCallback()
    )
    async def pexpireat(
        self,
        key: KeyT,
        unix_time_milliseconds: Union[int, datetime.datetime],
    ) -> bool:
        """
        Set the expiration for a key as a UNIX timestamp specified in milliseconds

        :return: if the timeout was set or not.
         e.g. key doesn't exist, or operation skipped due to the provided arguments.
        """

        return await self.execute_command(
            "PEXPIREAT", key, normalized_time_milliseconds(unix_time_milliseconds)
        )

    @redis_command("PTTL", readonly=True, group=CommandGroup.GENERIC)
    async def pttl(self, key: KeyT) -> int:
        """
        Returns the number of milliseconds until the key ``key`` will expire

        :return: TTL in milliseconds, or a negative value in order to signal an error
        """

        return await self.execute_command("PTTL", key)

    @redis_command(
        "RANDOMKEY",
        readonly=True,
        group=CommandGroup.GENERIC,
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM, pipeline=False),
    )
    async def randomkey(self) -> Optional[AnyStr]:
        """
        Returns the name of a random key

        :return: the random key, or ``None`` when the database is empty.
        """

        return await self.execute_command("RANDOMKEY")

    @redis_command(
        "RENAME",
        group=CommandGroup.GENERIC,
        response_callback=BoolCallback(),
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def rename(self, key: KeyT, newkey: KeyT) -> bool:
        """
        Rekeys key ``key`` to ``newkey``
        """

        return await self.execute_command("RENAME", key, newkey)

    @redis_command(
        "RENAMENX",
        group=CommandGroup.GENERIC,
        response_callback=BoolCallback(),
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def renamenx(self, key: KeyT, newkey: KeyT) -> bool:
        """
        Rekeys key ``key`` to ``newkey`` if ``newkey`` doesn't already exist

        :return: False when ``newkey`` already exists.
        """

        return await self.execute_command("RENAMENX", key, newkey)

    @redis_command(
        "RESTORE",
        group=CommandGroup.GENERIC,
        response_callback=SimpleStringCallback(),
    )
    async def restore(
        self,
        key: KeyT,
        ttl: int,
        serialized_value: bytes,
        replace: Optional[bool] = None,
        absttl: Optional[bool] = None,
        idletime: Optional[Union[int, datetime.timedelta]] = None,
        freq: Optional[int] = None,
    ) -> bool:
        """
        Create a key using the provided serialized value, previously obtained using DUMP.
        """
        params = [key, ttl, serialized_value]

        if replace:
            params.append("REPLACE")

        if absttl:
            params.append("ABSTTL")

        if idletime is not None:
            params.extend(["IDLETIME", normalized_milliseconds(idletime)])

        if freq:
            params.extend(["FREQ", freq])

        return await self.execute_command("RESTORE", *params)

    @mutually_inclusive_parameters("offset", "count")
    @redis_command("SORT", group=CommandGroup.GENERIC, response_callback=SortCallback())
    async def sort(
        self,
        key: KeyT,
        gets: Optional[Iterable[ValueT]] = None,
        by: Optional[ValueT] = None,
        offset: Optional[int] = None,
        count: Optional[int] = None,
        order: Optional[Literal[PureToken.ASC, PureToken.DESC]] = None,
        alpha: Optional[bool] = None,
        store: Optional[KeyT] = None,
    ) -> Union[Tuple[AnyStr, ...], int]:

        """
        Sort the elements in a list, set or sorted set

        :return: sorted elements.

         When the ``store`` option is specified the command returns the number of sorted elements
         in the destination list.
        """

        pieces: CommandArgList = [key]
        options = {}

        if by is not None:
            pieces.append("BY")
            pieces.append(by)

        if offset is not None and count is not None:
            pieces.append("LIMIT")
            pieces.append(offset)
            pieces.append(count)

        for g in gets or []:
            pieces.append("GET")
            pieces.append(g)

        if order:
            pieces.append(order.value)

        if alpha is not None:
            pieces.append("ALPHA")

        if store is not None:
            pieces.append("STORE")
            pieces.append(store)
            options["store"] = True

        return await self.execute_command("SORT", *pieces, **options)

    @redis_command("TOUCH", group=CommandGroup.GENERIC)
    async def touch(self, keys: Iterable[KeyT]) -> int:
        """
        Alters the last access time of a key(s).
        Returns the number of existing keys specified.

        :return: The number of keys that were touched.
        """
        return await self.execute_command("TOUCH", *keys)

    @redis_command("TTL", readonly=True, group=CommandGroup.GENERIC)
    async def ttl(self, key: KeyT) -> int:
        """
        Get the time to live for a key in seconds

        :return: TTL in seconds, or a negative value in order to signal an error
        """

        return await self.execute_command("TTL", key)

    @redis_command("TYPE", readonly=True, group=CommandGroup.GENERIC)
    async def type(self, key: KeyT) -> Optional[AnyStr]:
        """
        Determine the type stored at key

        :return: type of ``key``, or ``None`` when ``key`` does not exist.
        """

        return await self.execute_command("TYPE", key)

    @redis_command("UNLINK", group=CommandGroup.GENERIC)
    async def unlink(self, keys: Iterable[KeyT]) -> int:
        """
        Delete a key asynchronously in another thread.
        Otherwise it is just as :meth:`delete`, but non blocking.

        :return: The number of keys that were unlinked.
        """

        return await self.execute_command("UNLINK", *keys)

    @redis_command("WAIT", group=CommandGroup.GENERIC)
    async def wait(self, numreplicas: int, timeout: int) -> int:
        """
        Wait for the synchronous replication of all the write commands sent in the context of
        the current connection

        :return: The command returns the number of replicas reached by all the writes performed
         in the context of the current connection.
        """

        return await self.execute_command("WAIT", numreplicas, timeout)

    @redis_command(
        "SCAN",
        readonly=True,
        group=CommandGroup.GENERIC,
        arguments={"type_": {"version_introduced": "6.0.0"}},
        response_callback=ScanCallback(),
        cluster=ClusterCommandConfig(flag=NodeFlag.PRIMARIES, pipeline=False),
    )
    async def scan(
        self,
        cursor: Optional[int] = 0,
        match: Optional[ValueT] = None,
        count: Optional[int] = None,
        type_: Optional[ValueT] = None,
    ) -> Tuple[int, Tuple[AnyStr, ...]]:
        """
        Incrementally iterate the keys space
        """
        pieces: CommandArgList = [cursor or "0"]

        if match is not None:
            pieces.extend([b("MATCH"), match])

        if count is not None:
            pieces.extend([b("COUNT"), count])

        if type_ is not None:
            pieces.extend([b("TYPE"), type_])

        return await self.execute_command("SCAN", *pieces)

    @redis_command("BLMOVE", version_introduced="6.2.0", group=CommandGroup.LIST)
    async def blmove(
        self,
        source: KeyT,
        destination: KeyT,
        wherefrom: Literal[PureToken.LEFT, PureToken.RIGHT],
        whereto: Literal[PureToken.LEFT, PureToken.RIGHT],
        timeout: Union[int, float],
    ) -> Optional[AnyStr]:
        """
        Pop an element from a list, push it to another list and return it;
        or block until one is available


        :return: the element being popped from ``source`` and pushed to ``destination``
        """
        params: CommandArgList = [
            source,
            destination,
            wherefrom.value,
            whereto.value,
            timeout,
        ]

        return await self.execute_command("BLMOVE", *params)

    @redis_command("BLPOP", group=CommandGroup.LIST)
    async def blpop(
        self, keys: Iterable[KeyT], timeout: Union[int, float]
    ) -> Optional[List[AnyStr]]:
        """
        Remove and get the first element in a list, or block until one is available

        :return:
         - ``None`` when no element could be popped and the timeout expired.
         - A list with the first element being the name of the key
           where an element was popped and the second element being the value of the
           popped element.
        """

        return await self.execute_command("BLPOP", *keys, timeout)

    @redis_command("BRPOP", group=CommandGroup.LIST)
    async def brpop(
        self, keys: Iterable[KeyT], timeout: Union[int, float]
    ) -> Optional[List[AnyStr]]:
        """
        Remove and get the last element in a list, or block until one is available

        :return:
         - ``None`` when no element could be popped and the timeout expired.
         - A list with the first element being the name of the key
           where an element was popped and the second element being the value of the
           popped element.
        """

        return await self.execute_command("BRPOP", *keys, timeout)

    @redis_command("BRPOPLPUSH", version_deprecated="6.2.0", group=CommandGroup.LIST)
    async def brpoplpush(
        self, source: KeyT, destination: KeyT, timeout: Union[int, float]
    ) -> Optional[AnyStr]:
        """
        Pop an element from a list, push it to another list and return it;
        or block until one is available

        :return: the element being popped from ``source`` and pushed to
         ``destination``.
        """

        return await self.execute_command("BRPOPLPUSH", source, destination, timeout)

    @redis_command("LINDEX", readonly=True, group=CommandGroup.LIST)
    async def lindex(self, key: KeyT, index: int) -> Optional[AnyStr]:
        """

        Get an element from a list by its index

        :return: the requested element, or ``None`` when ``index`` is out of range.
        """

        return await self.execute_command("LINDEX", key, index)

    @redis_command("LINSERT", group=CommandGroup.LIST)
    async def linsert(
        self,
        key: KeyT,
        where: Literal[PureToken.BEFORE, PureToken.AFTER],
        pivot: ValueT,
        element: ValueT,
    ) -> int:
        """
        Inserts element in the list stored at key either before or after the reference
        value pivot.

        :return: the length of the list after the insert operation, or ``-1`` when
         the value pivot was not found.
        """

        return await self.execute_command("LINSERT", key, where.value, pivot, element)

    @redis_command("LLEN", readonly=True, group=CommandGroup.LIST)
    async def llen(self, key: KeyT) -> int:
        """
        :return: the length of the list at ``key``.
        """

        return await self.execute_command("LLEN", key)

    @redis_command("LMOVE", version_introduced="6.2.0", group=CommandGroup.LIST)
    async def lmove(
        self,
        source: KeyT,
        destination: KeyT,
        wherefrom: Literal[PureToken.LEFT, PureToken.RIGHT],
        whereto: Literal[PureToken.LEFT, PureToken.RIGHT],
    ) -> AnyStr:
        """
        Pop an element from a list, push it to another list and return it

        :return: the element being popped and pushed.
        """
        params = [source, destination, wherefrom.value, whereto.value]

        return await self.execute_command("LMOVE", *params)

    @redis_command(
        "LPOP",
        group=CommandGroup.LIST,
        arguments={"count": {"version_introduced": "6.2.0"}},
        # response_callback=item_or_list
    )
    async def lpop(
        self, key: KeyT, count: Optional[int] = None
    ) -> Optional[Union[AnyStr, List[AnyStr]]]:
        """
        Remove and get the first ``count`` elements in a list

        :return: the value of the first element, or ``None`` when ``key`` does not exist.
         If ``count`` is provided the return is a list of popped elements,
         or ``None`` when ``key`` does not exist.
        """
        pieces = []
        if count is not None:
            pieces.append(count)
        return await self.execute_command("LPOP", key, *pieces)

    @redis_command(
        "LPOS", readonly=True, version_introduced="6.0.6", group=CommandGroup.LIST
    )
    async def lpos(
        self,
        key: KeyT,
        element: ValueT,
        rank: Optional[int] = None,
        count: Optional[int] = None,
        maxlen: Optional[int] = None,
    ) -> Union[Optional[int], List[int]]:
        """

        Return the index of matching elements on a list


        :return: The command returns the integer representing the matching element,
         or ``None`` if there is no match.

         If the ``count`` argument is given a list of integers representing
         the matching elements.
        """
        pieces: CommandArgList = [key, element]

        if count is not None:
            pieces.extend(["COUNT", count])

        if rank is not None:
            pieces.extend(["RANK", rank])

        if maxlen is not None:
            pieces.extend(["MAXLEN", maxlen])

        return await self.execute_command("LPOS", *pieces)

    @redis_command("LPUSH", group=CommandGroup.LIST)
    async def lpush(self, key: KeyT, elements: Iterable[ValueT]) -> int:
        """
        Prepend one or multiple elements to a list

        :return: the length of the list after the push operations.
        """

        return await self.execute_command("LPUSH", key, *elements)

    @redis_command("LPUSHX", group=CommandGroup.LIST)
    async def lpushx(self, key: KeyT, elements: Iterable[ValueT]) -> int:
        """
        Prepend an element to a list, only if the list exists

        :return: the length of the list after the push operation.
        """

        return await self.execute_command("LPUSHX", key, *elements)

    @redis_command("LRANGE", readonly=True, group=CommandGroup.LIST)
    async def lrange(self, key: KeyT, start: int, stop: int) -> List[AnyStr]:
        """
        Get a range of elements from a list

        :return: list of elements in the specified range.
        """

        return await self.execute_command("LRANGE", key, start, stop)

    @redis_command("LREM", group=CommandGroup.LIST)
    async def lrem(self, key: KeyT, count: int, element: ValueT) -> int:
        """
        Removes the first ``count`` occurrences of elements equal to ``element``
        from the list stored at ``key``.

        The count argument influences the operation in the following ways:
            count > 0: Remove elements equal to value moving from head to tail.
            count < 0: Remove elements equal to value moving from tail to head.
            count = 0: Remove all elements equal to value.

        :return: the number of removed elements.
        """

        return await self.execute_command("LREM", key, count, element)

    @redis_command(
        "LSET",
        group=CommandGroup.LIST,
        response_callback=SimpleStringCallback(),
    )
    async def lset(self, key: KeyT, index: int, element: ValueT) -> bool:
        """Sets ``index`` of list ``key`` to ``element``"""

        return await self.execute_command("LSET", key, index, element)

    @redis_command(
        "LTRIM",
        group=CommandGroup.LIST,
        response_callback=SimpleStringCallback(),
    )
    async def ltrim(self, key: KeyT, start: int, stop: int) -> bool:
        """
        Trims the list ``key``, removing all values not within the slice
        between ``start`` and ``stop``

        ``start`` and ``stop`` can be negative numbers just like
        Python slicing notation
        """

        return await self.execute_command("LTRIM", key, start, stop)

    @overload
    async def rpop(self, key: KeyT) -> Optional[AnyStr]:
        ...

    @overload
    async def rpop(self, key: KeyT, count: int) -> Optional[List[AnyStr]]:
        ...

    @redis_command(
        "RPOP",
        group=CommandGroup.LIST,
        arguments={"count": {"version_introduced": "6.2.0"}},
    )
    async def rpop(
        self, key: KeyT, count: Optional[int] = None
    ) -> Optional[Union[AnyStr, List[AnyStr]]]:
        """
        Remove and get the last elements in a list

        :return: When called without the ``count`` argument the value of the last element, or
         ``None`` when ``key`` does not exist.

         When called with the ``count`` argument list of popped elements, or ``None`` when
         ``key`` does not exist.
        """

        pieces = []

        if count is not None:
            pieces.extend([count])

        return await self.execute_command("RPOP", key, *pieces)

    @redis_command("RPOPLPUSH", version_deprecated="6.2.0", group=CommandGroup.LIST)
    async def rpoplpush(self, source: KeyT, destination: KeyT) -> Optional[AnyStr]:
        """
        Remove the last element in a list, prepend it to another list and return it

        :return: the element being popped and pushed.
        """

        return await self.execute_command("RPOPLPUSH", source, destination)

    @redis_command("RPUSH", group=CommandGroup.LIST)
    async def rpush(self, key: KeyT, elements: Iterable[ValueT]) -> int:
        """
        Append an element(s) to a list

        :return: the length of the list after the push operation.
        """

        return await self.execute_command("RPUSH", key, *elements)

    @redis_command("RPUSHX", group=CommandGroup.LIST)
    async def rpushx(self, key: KeyT, elements: Iterable[ValueT]) -> int:
        """
        Append a element(s) to a list, only if the list exists

        :return: the length of the list after the push operation.
        """

        return await self.execute_command("RPUSHX", key, *elements)

    @redis_command("SADD", group=CommandGroup.SET)
    async def sadd(self, key: KeyT, members: Iterable[ValueT]) -> int:
        """
        Add one or more members to a set

        :return: the number of elements that were added to the set, not including
         all the elements already present in the set.
        """

        return await self.execute_command("SADD", key, *members)

    @redis_command("SCARD", readonly=True, group=CommandGroup.SET)
    async def scard(self, key: KeyT) -> int:
        """
        Returns the number of members in the set

        :return the cardinality (number of elements) of the set, or ``0`` if ``key``
         does not exist.
        """

        return await self.execute_command("SCARD", key)

    @redis_command(
        "SDIFF", readonly=True, group=CommandGroup.SET, response_callback=SetCallback()
    )
    async def sdiff(self, keys: Iterable[KeyT]) -> Set[AnyStr]:
        """
        Subtract multiple sets

        :return: members of the resulting set.
        """

        return await self.execute_command("SDIFF", *keys)

    @redis_command("SDIFFSTORE", group=CommandGroup.SET)
    async def sdiffstore(self, keys: Iterable[KeyT], destination: KeyT) -> int:
        """
        Subtract multiple sets and store the resulting set in a key

        """

        return await self.execute_command("SDIFFSTORE", destination, *keys)

    @redis_command(
        "SINTER", readonly=True, group=CommandGroup.SET, response_callback=SetCallback()
    )
    async def sinter(self, keys: Iterable[KeyT]) -> Set[AnyStr]:
        """
        Intersect multiple sets

        :return: members of the resulting set
        """

        return await self.execute_command("SINTER", *keys)

    @redis_command("SINTERSTORE", group=CommandGroup.SET)
    async def sinterstore(self, keys: Iterable[KeyT], destination: KeyT) -> int:
        """
        Intersect multiple sets and store the resulting set in a key

        :return: the number of elements in the resulting set.
        """

        return await self.execute_command("SINTERSTORE", destination, *keys)

    @redis_command(
        "SISMEMBER",
        readonly=True,
        group=CommandGroup.SET,
        response_callback=BoolCallback(),
    )
    async def sismember(self, key: KeyT, member: ValueT) -> bool:
        """
        Determine if a given value is a member of a set

        :return: If the element is a member of the set. ``False`` if ``key`` does not exist.
        """

        return await self.execute_command("SISMEMBER", key, member)

    @redis_command(
        "SMEMBERS",
        readonly=True,
        group=CommandGroup.SET,
        response_callback=SetCallback(),
    )
    async def smembers(self, key: KeyT) -> Set[AnyStr]:
        """Returns all members of the set"""

        return await self.execute_command("SMEMBERS", key)

    @redis_command(
        "SMISMEMBER",
        readonly=True,
        version_introduced="6.2.0",
        group=CommandGroup.SET,
        response_callback=BoolsCallback(),
    )
    async def smismember(
        self, key: KeyT, members: Iterable[ValueT]
    ) -> Tuple[bool, ...]:
        """
        Returns the membership associated with the given elements for a set

        :return: tuple representing the membership of the given elements, in the same
         order as they are requested.
        """

        return await self.execute_command("SMISMEMBER", key, *members)

    @redis_command("SMOVE", group=CommandGroup.SET, response_callback=BoolCallback())
    async def smove(self, source: KeyT, destination: KeyT, member: ValueT) -> bool:
        """
        Move a member from one set to another

        :return:
            * ``1`` if the element is moved.
            * ``0`` if the element is not a member of ``source`` and no operation was performed.
        """

        return await self.execute_command("SMOVE", source, destination, member)

    @redis_command(
        "SPOP", group=CommandGroup.SET, response_callback=ItemOrSetCallback()
    )
    async def spop(
        self, key: KeyT, count: Optional[int] = None
    ) -> Optional[Union[AnyStr, Set[AnyStr]]]:
        """
        Remove and return one or multiple random members from a set

        :return: When called without the ``count`` argument the removed member, or ``None``
         when ``key`` does not exist.

         When called with the ``count`` argument the removed members, or an empty array when
         ``key`` does not exist.
        """

        if count and isinstance(count, int):
            return await self.execute_command("SPOP", key, count, count=count)
        else:
            return await self.execute_command("SPOP", key)

    @redis_command(
        "SRANDMEMBER",
        readonly=True,
        group=CommandGroup.SET,
        response_callback=ItemOrSetCallback(),
    )
    async def srandmember(
        self, key: KeyT, count: Optional[int] = None
    ) -> Optional[Union[AnyStr, Set[AnyStr]]]:
        """
        Get one or multiple random members from a set



        :return: without the additional ``count`` argument, the command returns a  randomly
         selected element, or ``None`` when ``key`` does not exist.

         When the additional ``count`` argument is passed, the command returns elements,
         or an empty set when ``key`` does not exist.
        """
        pieces: CommandArgList = []
        if count is not None:
            pieces.append(count)

        return await self.execute_command("SRANDMEMBER", key, *pieces, count=count)

    @redis_command("SREM", group=CommandGroup.SET)
    async def srem(self, key: KeyT, members: Iterable[ValueT]) -> int:
        """
        Remove one or more members from a set


        :return: the number of members that were removed from the set, not
         including non existing members.
        """

        return await self.execute_command("SREM", key, *members)

    @redis_command(
        "SUNION", readonly=True, group=CommandGroup.SET, response_callback=SetCallback()
    )
    async def sunion(self, keys: Iterable[KeyT]) -> Set[AnyStr]:
        """
        Add multiple sets

        :return: members of the resulting set.
        """

        return await self.execute_command("SUNION", *keys)

    @redis_command("SUNIONSTORE", group=CommandGroup.SET)
    async def sunionstore(self, keys: Iterable[KeyT], destination: KeyT) -> int:
        """
        Add multiple sets and store the resulting set in a key

        :return: the number of elements in the resulting set.

        """

        return await self.execute_command("SUNIONSTORE", destination, *keys)

    @redis_command(
        "SSCAN",
        readonly=True,
        group=CommandGroup.SET,
        response_callback=SScanCallback(),
        cluster=ClusterCommandConfig(combine=lambda res: list(res.values()).pop()),
    )
    async def sscan(
        self,
        key: KeyT,
        cursor: Optional[int] = 0,
        match: Optional[ValueT] = None,
        count: Optional[int] = None,
    ) -> Tuple[int, Set[AnyStr]]:
        """
        Incrementally returns subsets of elements in a set. Also returns a
        cursor pointing to the scan position.

        :param match: is for filtering the keys by pattern
        :param count: is for hint the minimum number of returns
        """
        pieces: CommandArgList = [key, cursor or "0"]

        if match is not None:
            pieces.extend(["MATCH", match])

        if count is not None:
            pieces.extend(["COUNT", count])

        return await self.execute_command("SSCAN", *pieces)

    @redis_command(
        "BZPOPMAX",
        group=CommandGroup.SORTED_SET,
        response_callback=BZPopCallback(),
    )
    async def bzpopmax(
        self, keys: Iterable[KeyT], timeout: Union[int, float]
    ) -> Optional[Tuple[AnyStr, AnyStr, float]]:
        """
        Remove and return the member with the highest score from one or more sorted sets,
        or block until one is available.

        :return: A triplet with the first element being the name of the key
         where a member was popped, the second element is the popped member itself,
         and the third element is the score of the popped element.
        """
        params: CommandArgList = []
        params.extend(keys)
        params.append(timeout)

        return await self.execute_command("BZPOPMAX", *params)

    @redis_command(
        "BZPOPMIN",
        group=CommandGroup.SORTED_SET,
        response_callback=BZPopCallback(),
    )
    async def bzpopmin(
        self, keys: Iterable[KeyT], timeout: Union[int, float]
    ) -> Optional[Tuple[AnyStr, AnyStr, float]]:
        """
        Remove and return the member with the lowest score from one or more sorted sets,
        or block until one is available

        :return: A triplet with the first element being the name of the key
         where a member was popped, the second element is the popped member itself,
         and the third element is the score of the popped element.
        """

        params: CommandArgList = []
        params.extend(keys)
        params.append(timeout)

        return await self.execute_command("BZPOPMIN", *params)

    @redis_command(
        "ZADD",
        group=CommandGroup.SORTED_SET,
        arguments={"comparison": {"version_introduced": "6.2.0"}},
        response_callback=ZAddCallback(),
    )
    async def zadd(
        self,
        key: KeyT,
        member_scores: Dict[ValueT, float],
        condition: Optional[Literal[PureToken.NX, PureToken.XX]] = None,
        comparison: Optional[Literal[PureToken.GT, PureToken.LT]] = None,
        change: Optional[bool] = None,
        increment: Optional[bool] = None,
    ) -> Optional[Union[int, float]]:
        """
        Add one or more members to a sorted set, or update its score if it already exists

        :return:
         - When used without optional arguments, the number of elements added to the sorted set
           (excluding score updates).
         - If the ``change`` option is specified, the number of elements that were changed
           (added or updated).
         - If the ``condition``argument is specified, the new score of ``member``
           (a double precision floating point number) represented as string
         - ``None`` if the operation is aborted

        """
        pieces: CommandArgList = []

        if change is not None:
            pieces.append("CH")

        if increment is not None:
            pieces.append("INCR")

        if condition:
            pieces.append(condition.value)

        if comparison:
            pieces.append(comparison.value)

        flat_member_scores = dict_to_flat_list(member_scores, reverse=True)
        pieces.extend(flat_member_scores)
        return await self.execute_command("ZADD", key, *pieces)

    @redis_command("ZCARD", readonly=True, group=CommandGroup.SORTED_SET)
    async def zcard(self, key: KeyT) -> int:
        """
        Get the number of members in a sorted set

        :return: the cardinality (number of elements) of the sorted set, or ``0``
         if the ``key`` does not exist

        """

        return await self.execute_command("ZCARD", key)

    @redis_command("ZCOUNT", readonly=True, group=CommandGroup.SORTED_SET)
    async def zcount(
        self,
        key: KeyT,
        min_: ValueT,
        max_: ValueT,
    ) -> int:
        """
        Count the members in a sorted set with scores within the given values

        :return: the number of elements in the specified score range.
        """

        return await self.execute_command("ZCOUNT", key, min_, max_)

    @redis_command(
        "ZDIFF",
        readonly=True,
        version_introduced="6.2.0",
        group=CommandGroup.SORTED_SET,
        response_callback=ZMembersOrScoredMembers(),
    )
    async def zdiff(
        self, keys: Iterable[KeyT], withscores: Optional[bool] = None
    ) -> Tuple[Union[AnyStr, ScoredMember], ...]:
        """
        Subtract multiple sorted sets

        :return: the result of the difference (optionally with their scores, in case
         the ``withscores`` option is given).
        """
        pieces = [len(list(keys)), *keys]

        if withscores:
            pieces.append("WITHSCORES")

        return await self.execute_command("ZDIFF", *pieces, withscores=withscores)

    @redis_command(
        "ZDIFFSTORE", version_introduced="6.2.0", group=CommandGroup.SORTED_SET
    )
    async def zdiffstore(self, keys: Iterable[KeyT], destination: KeyT) -> int:
        """
        Subtract multiple sorted sets and store the resulting sorted set in a new key

        :return: the number of elements in the resulting sorted set at ``destination``.
        """
        pieces = [len(list(keys)), *keys]

        return await self.execute_command("ZDIFFSTORE", destination, *pieces)

    @redis_command(
        "ZINCRBY",
        group=CommandGroup.SORTED_SET,
        response_callback=OptionalFloatCallback(),
    )
    async def zincrby(self, key: KeyT, member: ValueT, increment: int) -> float:
        """
        Increment the score of a member in a sorted set

        :return: the new score of ``member`` (a double precision floating point number),
         represented as string.
        """

        return await self.execute_command("ZINCRBY", key, increment, member)

    @redis_command(
        "ZINTER",
        readonly=True,
        version_introduced="6.2.0",
        group=CommandGroup.SORTED_SET,
        response_callback=ZMembersOrScoredMembers(),
    )
    async def zinter(
        self,
        keys: Iterable[KeyT],
        weights: Optional[Iterable[int]] = None,
        aggregate: Optional[
            Literal[PureToken.SUM, PureToken.MIN, PureToken.MAX]
        ] = None,
        withscores: Optional[bool] = None,
    ) -> Tuple[Union[AnyStr, ScoredMember], ...]:
        """

        Intersect multiple sorted sets

        :return: the result of intersection (optionally with their scores, in case
         the ``withscores`` option is given).

        """

        return await self._zaggregate(
            "ZINTER", keys, None, weights, aggregate, withscores=withscores
        )

    @redis_command("ZINTERSTORE", group=CommandGroup.SORTED_SET)
    async def zinterstore(
        self,
        keys: Iterable[KeyT],
        destination: KeyT,
        weights: Optional[Iterable[int]] = None,
        aggregate: Optional[
            Literal[PureToken.SUM, PureToken.MIN, PureToken.MAX]
        ] = None,
    ) -> int:
        """
        Intersect multiple sorted sets and store the resulting sorted set in a new key

        :return: the number of elements in the resulting sorted set at ``destination``.
        """

        return await self._zaggregate(
            "ZINTERSTORE", keys, destination, weights, aggregate
        )

    @redis_command("ZLEXCOUNT", readonly=True, group=CommandGroup.SORTED_SET)
    async def zlexcount(self, key: KeyT, min_: ValueT, max_: ValueT) -> int:
        """
        Count the number of members in a sorted set between a given lexicographical range

        :return: the number of elements in the specified score range.
        """

        return await self.execute_command("ZLEXCOUNT", key, min_, max_)

    @redis_command(
        "ZMSCORE",
        readonly=True,
        version_introduced="6.2.0",
        group=CommandGroup.SORTED_SET,
        response_callback=ZMScoreCallback(),
    )
    async def zmscore(
        self, key: KeyT, members: Iterable[ValueT]
    ) -> Tuple[Optional[float], ...]:
        """
        Get the score associated with the given members in a sorted set

        :return: scores or ``None`` associated with the specified ``members``
         values (a double precision floating point number), represented as strings

        """
        if not members:
            raise DataError("ZMSCORE members must be a non-empty list")

        return await self.execute_command("ZMSCORE", key, *members)

    @redis_command(
        "ZPOPMAX",
        group=CommandGroup.SORTED_SET,
        response_callback=ZSetScorePairCallback(),
    )
    async def zpopmax(
        self, key: KeyT, count: Optional[int] = None
    ) -> Union[ScoredMember, ScoredMembers]:
        """
        Remove and return members with the highest scores in a sorted set

        :return: popped elements and scores.
        """
        args = (count is not None) and [count] or []
        options = {"count": count}
        return await self.execute_command("ZPOPMAX", key, *args, **options)

    @redis_command(
        "ZPOPMIN",
        group=CommandGroup.SORTED_SET,
        response_callback=ZSetScorePairCallback(),
    )
    async def zpopmin(
        self, key: KeyT, count: Optional[int] = None
    ) -> Union[ScoredMember, ScoredMembers]:
        """
        Remove and return members with the lowest scores in a sorted set

        :return: popped elements and scores.
        """
        args = (count is not None) and [count] or []
        options = {"count": count}

        return await self.execute_command("ZPOPMIN", key, *args, **options)

    @redis_command(
        "ZRANDMEMBER",
        readonly=True,
        version_introduced="6.2.0",
        group=CommandGroup.SORTED_SET,
        response_callback=ZRandMemberCallback(),
    )
    async def zrandmember(
        self,
        key: KeyT,
        count: Optional[int] = None,
        withscores: Optional[bool] = None,
    ) -> Optional[Union[AnyStr, List[AnyStr], ScoredMembers]]:
        """
        Get one or multiple random elements from a sorted set


        :return: without the additional ``count`` argument, the command returns a
         randomly selected element, or ``None`` when ``key`` does not exist.

         If the additional ``count`` argument is passed,
         the command returns the elements, or an empty tuple when ``key`` does not exist.

         If the ``withscores`` argument is used, the return is a list elements and their scores
         from the sorted set.
        """
        params: CommandArgList = []
        options = {}

        if count is not None:
            params.append(count)
            options["count"] = count

        if withscores:
            params.append("WITHSCORES")
            options["withscores"] = True
        return await self.execute_command("ZRANDMEMBER", key, *params, **options)

    @overload
    async def zrange(
        self,
        key: KeyT,
        min_: Union[int, ValueT],
        max_: Union[int, ValueT],
        sortby: Optional[Literal[PureToken.BYSCORE, PureToken.BYLEX]] = None,
        rev: Optional[bool] = None,
        offset: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Tuple[AnyStr, ...]:
        ...

    @overload
    async def zrange(
        self,
        key: KeyT,
        min_: Union[int, ValueT],
        max_: Union[int, ValueT],
        sortby: Optional[Literal[PureToken.BYSCORE, PureToken.BYLEX]] = None,
        rev: Optional[bool] = None,
        offset: Optional[int] = None,
        count: Optional[int] = None,
        *,
        withscores: Literal[True],
    ) -> Tuple[ScoredMember, ...]:
        ...

    @mutually_inclusive_parameters("offset", "count")
    @redis_command(
        "ZRANGE",
        readonly=True,
        group=CommandGroup.SORTED_SET,
        arguments={
            "sortby": {"version_introduced": "6.2.0"},
            "rev": {"version_introduced": "6.2.0"},
            "offset": {"version_introduced": "6.2.0"},
            "count": {"version_introduced": "6.2.0"},
        },
        response_callback=ZMembersOrScoredMembers(),
    )
    async def zrange(
        self,
        key: KeyT,
        min_: Union[int, ValueT],
        max_: Union[int, ValueT],
        sortby: Optional[Literal[PureToken.BYSCORE, PureToken.BYLEX]] = None,
        rev: Optional[bool] = None,
        offset: Optional[int] = None,
        count: Optional[int] = None,
        withscores: Optional[bool] = None,
    ) -> Tuple[Union[AnyStr, ScoredMember], ...]:
        """

        Return a range of members in a sorted set

        :return: elements in the specified range (optionally with their scores, in case
         the ``withscores`` argument is given).
        """
        return await self._zrange(
            "ZRANGE",
            key,
            min_,
            max_,
            None,
            rev,
            sortby,
            withscores,
            offset,
            count,
        )

    @mutually_inclusive_parameters("offset", "count")
    @redis_command(
        "ZRANGEBYLEX",
        readonly=True,
        version_deprecated="6.2.0",
        group=CommandGroup.SORTED_SET,
        response_callback=TupleCallback(),
    )
    async def zrangebylex(
        self,
        key: KeyT,
        min_: ValueT,
        max_: ValueT,
        offset: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Tuple[AnyStr, ...]:
        """

        Return a range of members in a sorted set, by lexicographical range

        :return: elements in the specified score range.
        """

        pieces: CommandArgList = [key, min_, max_]

        if offset is not None and count is not None:
            pieces.extend(["LIMIT", offset, count])

        return await self.execute_command("ZRANGEBYLEX", *pieces)

    @mutually_inclusive_parameters("offset", "count")
    @redis_command(
        "ZRANGEBYSCORE",
        readonly=True,
        version_deprecated="6.2.0",
        group=CommandGroup.SORTED_SET,
        response_callback=ZMembersOrScoredMembers(),
    )
    async def zrangebyscore(
        self,
        key: KeyT,
        min_: Union[int, float],
        max_: Union[int, float],
        withscores: Optional[bool] = None,
        offset: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Tuple[Union[AnyStr, ScoredMember], ...]:
        """

        Return a range of members in a sorted set, by score

        :return: elements in the specified score range (optionally with their scores).
        """

        pieces: CommandArgList = [key, min_, max_]

        if offset is not None and count is not None:
            pieces.extend([b("LIMIT"), offset, count])

        if withscores:
            pieces.append(b("WITHSCORES"))
        options = {"withscores": withscores}

        return await self.execute_command("ZRANGEBYSCORE", *pieces, **options)

    @mutually_inclusive_parameters("offset", "count")
    @redis_command(
        "ZRANGESTORE",
        version_introduced="6.2.0",
        group=CommandGroup.SORTED_SET,
    )
    async def zrangestore(
        self,
        dst: KeyT,
        src: KeyT,
        min_: Union[int, ValueT],
        max_: Union[int, ValueT],
        sortby: Optional[Literal[PureToken.BYSCORE, PureToken.BYLEX]] = None,
        rev: Optional[bool] = None,
        offset: Optional[int] = None,
        count: Optional[int] = None,
    ) -> int:
        """
        Store a range of members from sorted set into another key

        :return: the number of elements in the resulting sorted set
        """

        return await self._zrange(
            "ZRANGESTORE",
            src,
            min_,
            max_,
            dst,
            rev,
            sortby,
            False,
            offset,
            count,
        )

    @redis_command(
        "ZRANK",
        readonly=True,
        group=CommandGroup.SORTED_SET,
        response_callback=OptionalIntCallback(),
    )
    async def zrank(self, key: KeyT, member: ValueT) -> Optional[int]:
        """
        Determine the index of a member in a sorted set

        :return: the rank of ``member``
        """

        return await self.execute_command("ZRANK", key, member)

    @redis_command(
        "ZREM",
        group=CommandGroup.SORTED_SET,
    )
    async def zrem(self, key: KeyT, members: Iterable[ValueT]) -> int:
        """
        Remove one or more members from a sorted set

        :return: The number of members removed from the sorted set, not including non existing
         members.
        """

        return await self.execute_command("ZREM", key, *members)

    @redis_command("ZREMRANGEBYLEX", group=CommandGroup.SORTED_SET)
    async def zremrangebylex(self, key: KeyT, min_: ValueT, max_: ValueT) -> int:
        """
        Remove all members in a sorted set between the given lexicographical range

        :return: the number of elements removed.
        """

        return await self.execute_command("ZREMRANGEBYLEX", key, min_, max_)

    @redis_command("ZREMRANGEBYRANK", group=CommandGroup.SORTED_SET)
    async def zremrangebyrank(self, key: KeyT, start: int, stop: int) -> int:
        """
        Remove all members in a sorted set within the given indexes

        :return: the number of elements removed.
        """

        return await self.execute_command("ZREMRANGEBYRANK", key, start, stop)

    @redis_command("ZREMRANGEBYSCORE", group=CommandGroup.SORTED_SET)
    async def zremrangebyscore(
        self, key: KeyT, min_: Union[int, float], max_: Union[int, float]
    ) -> int:
        """
        Remove all members in a sorted set within the given scores

        :return: the number of elements removed.
        """

        return await self.execute_command("ZREMRANGEBYSCORE", key, min_, max_)

    @redis_command(
        "ZREVRANGE",
        readonly=True,
        version_deprecated="6.2.0",
        group=CommandGroup.SORTED_SET,
        response_callback=ZMembersOrScoredMembers(),
    )
    async def zrevrange(
        self,
        key: KeyT,
        start: int,
        stop: int,
        withscores: Optional[bool] = None,
    ) -> Tuple[Union[AnyStr, ScoredMember], ...]:
        """

        Return a range of members in a sorted set, by index, with scores ordered from
        high to low

        :return: elements in the specified range (optionally with their scores).
        """
        pieces = ["ZREVRANGE", key, start, stop]

        if withscores:
            pieces.append("WITHSCORES")
        options = {"withscores": withscores}

        return await self.execute_command(*pieces, **options)

    @mutually_inclusive_parameters("offset", "count")
    @redis_command(
        "ZREVRANGEBYLEX",
        readonly=True,
        version_deprecated="6.2.0",
        group=CommandGroup.SORTED_SET,
        response_callback=ZMembersOrScoredMembers(),
    )
    async def zrevrangebylex(
        self,
        key: KeyT,
        max_: ValueT,
        min_: ValueT,
        offset: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Tuple[AnyStr, ...]:
        """

        Return a range of members in a sorted set, by lexicographical range, ordered from
        higher to lower strings.

        :return: elements in the specified score range
        """

        pieces: CommandArgList = [key, max_, min_]

        if offset is not None and count is not None:
            pieces.extend(["LIMIT", offset, count])

        return await self.execute_command("ZREVRANGEBYLEX", *pieces)

    @mutually_inclusive_parameters("offset", "count")
    @redis_command(
        "ZREVRANGEBYSCORE",
        readonly=True,
        version_deprecated="6.2.0",
        group=CommandGroup.SORTED_SET,
        response_callback=ZMembersOrScoredMembers(),
    )
    async def zrevrangebyscore(
        self,
        key: KeyT,
        max_: Union[int, float],
        min_: Union[int, float],
        withscores: Optional[bool] = None,
        offset: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Tuple[Union[AnyStr, ScoredMember], ...]:
        """

        Return a range of members in a sorted set, by score, with scores ordered from high to low

        :return: elements in the specified score range (optionally with their scores)
        """

        pieces: CommandArgList = [key, max_, min_]

        if offset is not None and count is not None:
            pieces.extend(["LIMIT", offset, count])

        if withscores:
            pieces.append("WITHSCORES")
        options = {"withscores": withscores}

        return await self.execute_command("ZREVRANGEBYSCORE", *pieces, **options)

    @redis_command(
        "ZREVRANK",
        readonly=True,
        group=CommandGroup.SORTED_SET,
        response_callback=OptionalIntCallback(),
    )
    async def zrevrank(self, key: KeyT, member: ValueT) -> Optional[int]:
        """
        Determine the index of a member in a sorted set, with scores ordered from high to low

        :return: the rank of ``member``
        """

        return await self.execute_command("ZREVRANK", key, member)

    @redis_command(
        "ZSCAN",
        readonly=True,
        group=CommandGroup.SORTED_SET,
        response_callback=ZScanCallback(),
    )
    async def zscan(
        self,
        key: KeyT,
        cursor: Optional[int] = 0,
        match: Optional[ValueT] = None,
        count: Optional[int] = None,
    ) -> Tuple[int, ScoredMembers]:
        """
        Incrementally iterate sorted sets elements and associated scores

        """
        pieces: CommandArgList = [key, cursor or "0"]

        if match is not None:
            pieces.extend(["MATCH", match])

        if count is not None:
            pieces.extend(["COUNT", count])
        return await self.execute_command("ZSCAN", *pieces)

    @redis_command(
        "ZSCORE",
        readonly=True,
        group=CommandGroup.SORTED_SET,
        response_callback=OptionalFloatCallback(),
    )
    async def zscore(self, key: KeyT, member: ValueT) -> Optional[float]:
        """
        Get the score associated with the given member in a sorted set

        :return: the score of ``member`` (a double precision floating point number),
         represented as string or ``None`` if the member doesn't exist.
        """

        return await self.execute_command("ZSCORE", key, member)

    @redis_command(
        "ZUNION",
        readonly=True,
        version_introduced="6.2.0",
        group=CommandGroup.SORTED_SET,
        response_callback=ZMembersOrScoredMembers(),
    )
    async def zunion(
        self,
        keys: Iterable[KeyT],
        weights: Optional[Iterable[int]] = None,
        aggregate: Optional[
            Literal[PureToken.SUM, PureToken.MIN, PureToken.MAX]
        ] = None,
        withscores: Optional[bool] = None,
    ) -> Tuple[Union[AnyStr, ScoredMember], ...]:
        """

        Add multiple sorted sets

        :return: the result of union (optionally with their scores, in case the ``withscores``
         argument is given).
        """

        return await self._zaggregate(
            "ZUNION", keys, None, weights, aggregate, withscores=withscores
        )

    @redis_command("ZUNIONSTORE", group=CommandGroup.SORTED_SET)
    async def zunionstore(
        self,
        keys: Iterable[KeyT],
        destination: KeyT,
        weights: Optional[Iterable[int]] = None,
        aggregate: Optional[
            Literal[PureToken.SUM, PureToken.MIN, PureToken.MAX]
        ] = None,
    ) -> int:
        """
        Add multiple sorted sets and store the resulting sorted set in a new key

        :return: the number of elements in the resulting sorted set at ``destination``.
        """

        return await self._zaggregate(
            "ZUNIONSTORE", keys, destination, weights, aggregate
        )

    @deprecated(
        reason="Use :meth:`zadd` with the appropriate options instead", version="3.0.0"
    )
    async def zaddoption(self, key, option=None, *args, **kwargs):
        """
        Differs from zadd in that you can set either 'XX' or 'NX' option as
        described here: https://redis.io/commands/zadd. Only for Redis 3.0.2 or
        later.

        The following example would add four values to the 'my-key' key:
        redis.zaddoption('my-key', 'XX', 1.1, 'name1', 2.2, 'name2', name3=3.3, name4=4.4)
        redis.zaddoption('my-key', 'NX CH', name1=2.2)

        """

        if not option:
            raise RedisError("ZADDOPTION must take options")
        options = set(opt.upper() for opt in option.split())

        if options - VALID_ZADD_OPTIONS:
            raise RedisError("ZADD only takes XX, NX, CH, or INCR")

        if "NX" in options and "XX" in options:
            raise RedisError("ZADD only takes one of XX or NX")
        pieces = list(options)
        members: List[ValueT] = []

        if args:
            if len(args) % 2 != 0:
                raise RedisError(
                    "ZADD requires an equal number of " "values and scores"
                )
            members.extend(args)

        for pair in iteritems(kwargs):
            members.append(pair[1])
            members.append(pair[0])

        if "INCR" in options and len(members) != 2:
            raise RedisError("ZADD with INCR only takes one score-name pair")

        return await self.execute_command("ZADD", key, *pieces, *members)

    async def _zrange(
        self,
        command: ValueT,
        key: KeyT,
        start: Union[int, ValueT],
        stop: Union[int, ValueT],
        dest: Optional[ValueT] = None,
        rev: Optional[bool] = None,
        sortby: Optional[PureToken] = None,
        withscores: Optional[bool] = False,
        offset: Optional[int] = None,
        count: Optional[int] = None,
    ):
        if (offset is not None and count is None) or (
            count is not None and offset is None
        ):
            raise DataError("``offset`` and ``count`` must both be specified.")

        if sortby == PureToken.BYLEX and withscores:
            raise DataError(
                "``withscores`` not supported in combination " "with ``bylex``."
            )
        pieces: CommandArgList = [command]

        if dest:
            pieces.append(dest)
        pieces.extend([key, start, stop])

        if sortby:
            pieces.append(sortby.value)

        if rev is not None:
            pieces.append("REV")

        if offset is not None and count is not None:
            pieces.extend(["LIMIT", offset, count])

        if withscores:
            pieces.append("WITHSCORES")
        options = {"withscores": withscores}

        return await self.execute_command(*pieces, **options)

    async def _zaggregate(
        self,
        command,
        keys: Iterable[ValueT],
        destination: Optional[ValueT] = None,
        weights: Optional[Iterable[int]] = None,
        aggregate: Optional[PureToken] = None,
        withscores: Optional[bool] = None,
    ):
        pieces = [command]
        if destination:
            pieces.append(destination)
        pieces.append(len(list(keys)))
        pieces.extend(keys)
        options = {}
        if weights:
            pieces.append(b("WEIGHTS"))
            pieces.extend(weights)

        if aggregate:
            pieces.append(b("AGGREGATE"))
            pieces.append(aggregate.value)

        if withscores is not None:
            pieces.append(b("WITHSCORES"))
            options = {"withscores": True}
        return await self.execute_command(*pieces, **options)

    @redis_command("XACK", group=CommandGroup.STREAM)
    async def xack(
        self, key: KeyT, group: ValueT, identifiers: Iterable[ValueT]
    ) -> int:
        """
        Marks a pending message as correctly processed,
        effectively removing it from the pending entries list of the consumer group.

        :return: number of messages successfully acknowledged,
         that is, the IDs we were actually able to resolve in the PEL.
        """

        return await self.execute_command("XACK", key, group, *identifiers)

    @mutually_inclusive_parameters("trim_strategy", "threshold")
    @redis_command(
        "XADD",
        group=CommandGroup.STREAM,
        arguments={
            "nomkstream": {"version_introduced": "6.2.0"},
            "limit": {"version_introduced": "6.2.0"},
        },
    )
    async def xadd(
        self,
        key: KeyT,
        field_values: Dict[ValueT, ValueT],
        identifier: Optional[ValueT] = None,
        nomkstream: Optional[bool] = None,
        trim_strategy: Optional[Literal[PureToken.MAXLEN, PureToken.MINID]] = None,
        threshold: Optional[int] = None,
        trim_operator: Optional[
            Literal[PureToken.EQUAL, PureToken.APPROXIMATELY]
        ] = None,
        limit: Optional[int] = None,
    ) -> Optional[AnyStr]:
        """
        Appends a new entry to a stream

        :return: The identifier of the added entry. The identifier is the one auto-generated
         if ``*`` is passed as :paramref:`identifier`, otherwise the it justs returns
         the same identifier specified

         Returns ``None`` when used with :paramref:`nomkstream` and the key doesn't exist.

        """
        pieces: CommandArgList = []
        if nomkstream is not None:
            pieces.append(PureToken.NOMKSTREAM.value)

        if trim_strategy == PureToken.MAXLEN:
            pieces.append(trim_strategy.value)

            if trim_operator:
                pieces.append(trim_operator.value)

            if threshold is not None:
                pieces.append(threshold)

        if limit is not None:
            pieces.extend(["LIMIT", limit])

        pieces.append(identifier or PureToken.AUTO_ID.value)

        for kv in field_values.items():
            pieces.extend(list(kv))

        return await self.execute_command("XADD", key, *pieces)

    @redis_command("XLEN", readonly=True, group=CommandGroup.STREAM)
    async def xlen(self, key: KeyT) -> int:
        """ """

        return await self.execute_command("XLEN", key)

    @redis_command(
        "XRANGE",
        readonly=True,
        group=CommandGroup.STREAM,
        response_callback=StreamRangeCallback(),
    )
    async def xrange(
        self,
        key: KeyT,
        start: Optional[ValueT] = None,
        end: Optional[ValueT] = None,
        count: Optional[int] = None,
    ) -> Tuple[StreamEntry, ...]:
        """
        Return a range of elements in a stream, with IDs matching the specified IDs interval
        """

        pieces: CommandArgList = [defaultvalue(start, "-"), defaultvalue(end, "+")]

        if count is not None:
            pieces.append("COUNT")
            pieces.append(count)

        return await self.execute_command("XRANGE", key, *pieces)

    @redis_command(
        "XREVRANGE",
        readonly=True,
        group=CommandGroup.STREAM,
        response_callback=StreamRangeCallback(),
    )
    async def xrevrange(
        self,
        key: KeyT,
        end: Optional[ValueT] = None,
        start: Optional[ValueT] = None,
        count: Optional[int] = None,
    ) -> Tuple[StreamEntry, ...]:
        """
        Return a range of elements in a stream, with IDs matching the specified
        IDs interval, in reverse order (from greater to smaller IDs) compared to XRANGE
        """
        pieces: CommandArgList = [defaultvalue(end, "+"), defaultvalue(start, "-")]

        if count is not None:
            pieces.append("COUNT")
            pieces.append(count)

        return await self.execute_command("XREVRANGE", key, *pieces)

    @redis_command(
        "XREAD",
        readonly=True,
        group=CommandGroup.STREAM,
        response_callback=MultiStreamRangeCallback(),
    )
    async def xread(
        self,
        streams: Dict[ValueT, ValueT],
        count: Optional[int] = None,
        block: Optional[Union[int, datetime.timedelta]] = None,
    ) -> Optional[Dict[AnyStr, Tuple[StreamEntry, ...]]]:
        """
        Return never seen elements in multiple streams, with IDs greater than
        the ones reported by the caller for each stream. Can block.

        :return: Mapping of streams to stream entries.
         Field and values are guaranteed to be reported in the same order they were
         added by :meth:`xadd`.

         When :paramref:`block` is used, on timeout ``None`` is returned.
        """
        pieces: CommandArgList = []

        if block is not None:
            if not isinstance(block, int) or block < 0:
                raise RedisError("XREAD block must be a positive integer")
            pieces.append("BLOCK")
            pieces.append(str(block))

        if count is not None:
            if not isinstance(count, int) or count < 1:
                raise RedisError("XREAD count must be a positive integer")
            pieces.append("COUNT")
            pieces.append(str(count))
        pieces.append("STREAMS")
        ids = []

        for partial_stream in streams.items():
            pieces.append(partial_stream[0])
            ids.append(partial_stream[1])
        pieces.extend(ids)

        return await self.execute_command("XREAD", *pieces)

    @mutually_inclusive_parameters("group", "consumer")
    @redis_command(
        "XREADGROUP",
        group=CommandGroup.STREAM,
        response_callback=MultiStreamRangeCallback(),
    )
    async def xreadgroup(
        self,
        group: ValueT,
        consumer: ValueT,
        streams: Dict[ValueT, ValueT],
        count: Optional[int] = None,
        block: Optional[Union[int, datetime.timedelta]] = None,
        noack: Optional[bool] = None,
    ) -> Dict[AnyStr, Tuple[StreamEntry, ...]]:
        """ """
        pieces: CommandArgList = ["GROUP", group, consumer]

        if block is not None:
            if not isinstance(block, int) or block < 1:
                raise RedisError("XREAD block must be a positive integer")
            pieces.append("BLOCK")
            pieces.append(str(block))

        if count is not None:
            if not isinstance(count, int) or count < 1:
                raise RedisError("XREAD count must be a positive integer")
            pieces.append("COUNT")
            pieces.append(str(count))
        pieces.append("STREAMS")
        ids = []

        for partial_stream in streams.items():
            pieces.append(partial_stream[0])
            ids.append(partial_stream[1])
        pieces.extend(ids)

        return await self.execute_command("XREADGROUP", *pieces)

    @mutually_inclusive_parameters("start", "end", "count")
    @redis_command(
        "XPENDING",
        readonly=True,
        group=CommandGroup.STREAM,
        arguments={"idle": {"version_introduced": "6.2.0"}},
        response_callback=PendingCallback(),
    )
    async def xpending(
        self,
        key: KeyT,
        group: ValueT,
        start: Optional[ValueT] = None,
        end: Optional[ValueT] = None,
        count: Optional[int] = None,
        idle: Optional[int] = None,
        consumer: Optional[ValueT] = None,
    ) -> Union[Tuple[StreamPendingExt, ...], StreamPending]:
        """
        Return information and entries from a stream consumer group pending
        entries list, that are messages fetched but never acknowledged.
        """
        pieces: CommandArgList = [key, group]

        if idle is not None:
            pieces.extend(["IDLE", idle])
        if count is not None and end is not None and start is not None:
            pieces.extend([start, end, count])
        if consumer is not None:
            pieces.append(consumer)

        return await self.execute_command("XPENDING", *pieces, count=count)

    @mutually_inclusive_parameters("trim_strategy", "threshold")
    @redis_command(
        "XTRIM",
        group=CommandGroup.STREAM,
        arguments={"limit": {"version_introduced": "6.2.0"}},
    )
    async def xtrim(
        self,
        key: KeyT,
        trim_strategy: Literal[PureToken.MAXLEN, PureToken.MINID],
        threshold: int,
        trim_operator: Optional[
            Literal[PureToken.EQUAL, PureToken.APPROXIMATELY]
        ] = None,
        limit: Optional[int] = None,
    ) -> int:
        """ """
        pieces: CommandArgList = [trim_strategy.value]

        if trim_operator:
            pieces.append(trim_operator.value)

        pieces.append(threshold)

        if limit is not None:
            pieces.extend(["LIMIT", limit])

        return await self.execute_command("XTRIM", key, *pieces)

    @redis_command("XDEL", group=CommandGroup.STREAM)
    async def xdel(self, key: KeyT, identifiers: Iterable[ValueT]) -> int:
        """ """

        return await self.execute_command("XDEL", key, *identifiers)

    @redis_command(
        "XINFO CONSUMERS",
        readonly=True,
        group=CommandGroup.STREAM,
        response_callback=XInfoCallback(),
    )
    async def xinfo_consumers(
        self, key: KeyT, groupname: ValueT
    ) -> Tuple[Dict[AnyStr, AnyStr], ...]:
        """
        Get list of all consumers that belong to :paramref:`groupname` of the
        stream stored at :paramref:`key`
        """

        return await self.execute_command("XINFO CONSUMERS", key, groupname)

    @redis_command(
        "XINFO GROUPS",
        readonly=True,
        group=CommandGroup.STREAM,
        response_callback=XInfoCallback(),
    )
    async def xinfo_groups(self, key: KeyT) -> Tuple[Dict[AnyStr, AnyStr], ...]:
        """
        Get list of all consumers groups of the stream stored at :paramref:`key`
        """

        return await self.execute_command("XINFO GROUPS", key)

    @redis_command(
        "XINFO STREAM",
        readonly=True,
        group=CommandGroup.STREAM,
        response_callback=StreamInfoCallback(),
    )
    async def xinfo_stream(self, key: KeyT, count: Optional[int] = None) -> StreamInfo:
        """
        Get information about the stream stored at :paramref:`key`
        """
        pieces = []
        if count is not None:
            pieces.extend(["COUNT", count])

        return await self.execute_command("XINFO STREAM", key, *pieces)

    @redis_command(
        "XCLAIM", group=CommandGroup.STREAM, response_callback=ClaimCallback()
    )
    async def xclaim(
        self,
        key: KeyT,
        group: ValueT,
        consumer: ValueT,
        min_idle_time: Union[int, datetime.timedelta],
        identifiers: Iterable[ValueT],
        idle: Optional[int] = None,
        time: Optional[Union[int, datetime.datetime]] = None,
        retrycount: Optional[int] = None,
        force: Optional[bool] = None,
        justid: Optional[bool] = None,
    ) -> Union[Tuple[AnyStr, ...], Tuple[StreamEntry, ...]]:
        """
        Changes (or acquires) ownership of a message in a consumer group, as
        if the message was delivered to the specified consumer.

        :return:
        """
        pieces: CommandArgList = [
            key,
            group,
            consumer,
            normalized_milliseconds(min_idle_time),
        ]
        pieces.extend(identifiers)

        if idle is not None:
            pieces.extend(["IDLE", idle])
        if time is not None:
            pieces.extend(["TIME", normalized_time_milliseconds(time)])
        if retrycount is not None:
            pieces.extend(["RETRYCOUNT", retrycount])
        if force is not None:
            pieces.append(PureToken.FORCE.value)
        if justid is not None:
            pieces.append(PureToken.JUSTID.value)
        return await self.execute_command("XCLAIM", *pieces, justid=justid)

    @redis_command(
        "XGROUP CREATE",
        group=CommandGroup.STREAM,
        response_callback=SimpleStringCallback(),
    )
    async def xgroup_create(
        self,
        key: KeyT,
        groupname: ValueT,
        identifier: Optional[ValueT] = None,
        mkstream: Optional[bool] = None,
    ) -> bool:
        """
        Create a consumer group.
        """
        pieces: CommandArgList = [key, groupname, identifier or PureToken.NEW_ID.value]
        if mkstream is not None:
            pieces.append(PureToken.MKSTREAM.value)

        return await self.execute_command("XGROUP CREATE", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "XGROUP CREATECONSUMER",
        version_introduced="6.2.0",
        group=CommandGroup.STREAM,
    )
    async def xgroup_createconsumer(
        self, key: KeyT, *, groupname: ValueT, consumername: ValueT
    ) -> int:
        """
        Create a consumer in a consumer group.

        :return: the number of created consumers (0 or 1)
        """
        pieces = [key, groupname, consumername]
        return await self.execute_command("XGROUP CREATECONSUMER", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "XGROUP SETID",
        group=CommandGroup.STREAM,
        response_callback=SimpleStringCallback(),
    )
    async def xgroup_setid(
        self,
        key: KeyT,
        groupname: ValueT,
        identifier: Optional[ValueT] = None,
    ) -> bool:
        """
        Set a consumer group to an arbitrary last delivered ID value.
        """
        return await self.execute_command(
            "XGROUP SETID", key, groupname, identifier or PureToken.NEW_ID.value
        )

    @redis_command("XGROUP DESTROY", group=CommandGroup.STREAM)
    async def xgroup_destroy(self, key: KeyT, groupname: ValueT) -> int:
        """
        Destroy a consumer group.

        :return: The number of destroyed consumer groups
        """

        return await self.execute_command("XGROUP DESTROY", key, groupname)

    @versionadded(version="3.0.0")
    @redis_command("XGROUP DELCONSUMER", group=CommandGroup.STREAM)
    async def xgroup_delconsumer(
        self, key: KeyT, groupname: ValueT, consumername: ValueT
    ) -> int:
        """
        Delete a consumer from a consumer group.

        :return: The number of pending messages that the consumer had before it was deleted
        """
        return await self.execute_command(
            "XGROUP DELCONSUMER", key, groupname, consumername
        )

    @versionadded(version="3.0.0")
    @redis_command(
        "XAUTOCLAIM",
        version_introduced="6.2.0",
        group=CommandGroup.STREAM,
        response_callback=AutoClaimCallback(),
    )
    async def xautoclaim(
        self,
        key: KeyT,
        group: ValueT,
        consumer: ValueT,
        min_idle_time: Union[int, datetime.timedelta],
        start: ValueT,
        count: Optional[int] = None,
        justid: Optional[bool] = None,
    ) -> Union[
        Tuple[AnyStr, Tuple[AnyStr, ...]],
        Tuple[AnyStr, Tuple[StreamEntry, ...], Tuple[AnyStr, ...]],
    ]:

        """
        Changes (or acquires) ownership of messages in a consumer group, as if the messages were
        delivered to the specified consumer.

        :return: A dictionary with keys as stream identifiers and values containing
         all the successfully claimed messages in the same format as :meth:`xrange`

        """
        pieces: CommandArgList = [
            key,
            group,
            consumer,
            normalized_milliseconds(min_idle_time),
            start,
        ]

        if count is not None:
            pieces.extend(["COUNT", count])

        if justid is not None:
            pieces.append(PureToken.JUSTID.value)

        return await self.execute_command("XAUTOCLAIM", *pieces, justid=justid)

    @redis_command(
        "BITCOUNT",
        readonly=True,
        group=CommandGroup.BITMAP,
    )
    @mutually_inclusive_parameters("start", "end")
    async def bitcount(
        self,
        key: KeyT,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ) -> int:
        """
        Returns the count of set bits in the value of ``key``.  Optional
        ``start`` and ``end`` paramaters indicate which bytes to consider

        """
        params: CommandArgList = [key]

        if start is not None and end is not None:
            params.append(start)
            params.append(end)
        elif (start is not None and end is None) or (end is not None and start is None):
            raise RedisError("Both start and end must be specified")

        return await self.execute_command("BITCOUNT", *params)

    def bitfield(self, key: KeyT) -> BitFieldOperation:
        """

        Return a :class:`BitFieldOperation` instance to conveniently construct one or
        more bitfield operations on ``key``.
        """

        return BitFieldOperation(self, key)

    def bitfield_ro(self, key: KeyT) -> BitFieldOperation:
        """

        Return a :class:`BitFieldOperation` instance to conveniently construct bitfield
        operations on a read only replica against ``key``.

        Raises :class:`ReadOnlyError` if a write operation is attempted
        """

        return BitFieldOperation(self, key, readonly=True)

    @redis_command(
        "BITOP", group=CommandGroup.BITMAP, cluster=ClusterCommandConfig(pipeline=False)
    )
    async def bitop(
        self, keys: Iterable[KeyT], operation: ValueT, destkey: KeyT
    ) -> int:
        """
        Perform a bitwise operation using ``operation`` between ``keys`` and
        store the result in ``destkey``.
        """

        return await self.execute_command("BITOP", operation, destkey, *keys)

    @redis_command(
        "BITPOS",
        readonly=True,
        group=CommandGroup.BITMAP,
    )
    async def bitpos(
        self,
        key: KeyT,
        bit: int,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ) -> int:
        """

        Return the position of the first bit set to 1 or 0 in a string.
        ``start`` and ``end`` defines the search range. The range is interpreted
        as a range of bytes and not a range of bits, so start=0 and end=2
        means to look at the first three bytes.
        """

        if bit not in (0, 1):
            raise RedisError("bit must be 0 or 1")
        params: CommandArgList = [key, bit]

        if start is not None:
            params.append(start)

        if start is not None and end is not None:
            params.append(end)
        elif start is None and end is not None:
            raise RedisError("start argument is not set, when end is specified")

        return await self.execute_command("BITPOS", *params)

    @redis_command("GETBIT", readonly=True, group=CommandGroup.BITMAP)
    async def getbit(self, key: KeyT, offset: int) -> int:
        """
        Returns the bit value at offset in the string value stored at key

        :return: the bit value stored at ``offset``.
        """

        return await self.execute_command("GETBIT", key, offset)

    @redis_command("SETBIT", group=CommandGroup.BITMAP)
    async def setbit(self, key: KeyT, offset: int, value: int) -> int:
        """
        Flag the ``offset`` in ``key`` as ``value``. Returns a boolean
        indicating the previous value of ``offset``.

        :return: the original bit value stored at ``offset``.
        """
        value = value and 1 or 0

        return await self.execute_command("SETBIT", key, offset, value)

    @redis_command(
        "PUBLISH",
        group=CommandGroup.PUBSUB,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def publish(self, channel: ValueT, message: ValueT) -> int:
        """
        Publish ``message`` on ``channel``.
        Returns the number of subscribers the message was delivered to.
        """
        return await self.execute_command("PUBLISH", channel, message)

    @redis_command(
        "PUBSUB CHANNELS",
        group=CommandGroup.PUBSUB,
        response_callback=TupleCallback(),
    )
    async def pubsub_channels(
        self, *, pattern: Optional[ValueT] = None
    ) -> Tuple[AnyStr, ...]:
        """
        Return channels that have at least one subscriber
        """
        return await self.execute_command("PUBSUB CHANNELS", pattern or "*")

    @redis_command(
        "PUBSUB NUMPAT",
        group=CommandGroup.PUBSUB,
    )
    async def pubsub_numpat(self) -> int:
        """
        Get the count of unique patterns pattern subscriptions

        :return: the number of patterns all the clients are subscribed to.
        """
        return await self.execute_command("PUBSUB NUMPAT")

    @redis_command(
        "PUBSUB NUMSUB",
        group=CommandGroup.PUBSUB,
        response_callback=DictCallback(pairs_to_ordered_dict),
    )
    async def pubsub_numsub(self, *channels: ValueT) -> OrderedDict[AnyStr, int]:
        """
        Get the count of subscribers for channels

        :return: Mapping of channels to number of subscribers per channel
        """
        pieces: CommandArgList = []
        if channels:
            pieces.extend(channels)
        return await self.execute_command("PUBSUB NUMSUB", *pieces)

    @redis_command(
        "EVAL",
        group=CommandGroup.SCRIPTING,
    )
    async def eval(
        self,
        script: ValueT,
        keys: Optional[Iterable[KeyT]] = None,
        args: Optional[Iterable[ValueT]] = None,
    ) -> Any:
        """
        Execute the Lua ``script``, specifying the ``numkeys`` the script
        will touch and the key names and argument values in ``keys_and_args``.
        Returns the result of the script.

        In practice, use the object returned by ``register_script``. This
        function exists purely for Redis API completion.
        """
        num_keys = 0
        pieces: CommandArgList = []
        if keys:
            pieces.extend(list(keys))
            num_keys = len(pieces)
        if args:
            pieces.extend(args)

        return await self.execute_command("EVAL", script, num_keys, *pieces)

    @redis_command("EVALSHA", group=CommandGroup.SCRIPTING)
    async def evalsha(
        self,
        sha1: ValueT,
        keys: Optional[Iterable[KeyT]] = None,
        args: Optional[Iterable[ValueT]] = None,
    ) -> Any:
        """
        Use the ``sha`` to execute a Lua script already registered via EVAL
        or SCRIPT LOAD. Specify the ``numkeys`` the script will touch and the
        key names and argument values in ``keys_and_args``. Returns the result
        of the script.

        In practice, use the object returned by ``register_script``. This
        function exists purely for Redis API completion.
        """

        num_keys = 0
        pieces: CommandArgList = []
        if keys:
            pieces.extend(list(keys))
            num_keys = len(pieces)
        if args:
            pieces.extend(args)

        return await self.execute_command("EVALSHA", sha1, num_keys, *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "SCRIPT DEBUG",
        group=CommandGroup.SCRIPTING,
        response_callback=SimpleStringCallback(),
        cluster=ClusterCommandConfig(
            flag=NodeFlag.PRIMARIES,
            combine=lambda res: tuple(all(k) for k in zip(*res.values())),
        ),
    )
    async def script_debug(
        self,
        mode: Literal[PureToken.YES, PureToken.SYNC, PureToken.NO],
    ) -> bool:
        """
        Set the debug mode for executed scripts.
        """

        return await self.execute_command("SCRIPT DEBUG", mode.value)

    @redis_command(
        "SCRIPT EXISTS",
        group=CommandGroup.SCRIPTING,
        response_callback=BoolsCallback(),
        cluster=ClusterCommandConfig(
            flag=NodeFlag.PRIMARIES,
            combine=lambda res: tuple(all(k) for k in zip(*res.values())),
        ),
    )
    async def script_exists(self, sha1s: Iterable[ValueT]) -> Tuple[bool, ...]:
        """
        Check if a script exists in the script cache by specifying the SHAs of
        each script as ``sha1s``.

        :return: tuple of boolean values indicating if each script
         exists in the cache.
        """

        return await self.execute_command("SCRIPT EXISTS", *sha1s)

    @redis_command(
        "SCRIPT FLUSH",
        group=CommandGroup.SCRIPTING,
        arguments={"sync_type": {"version_introduced": "6.2.0"}},
        response_callback=BoolCallback(),
        cluster=ClusterCommandConfig(
            flag=NodeFlag.PRIMARIES, combine=lambda res: all(res)
        ),
    )
    async def script_flush(
        self,
        sync_type: Optional[Literal[PureToken.SYNC, PureToken.ASYNC]] = None,
    ) -> bool:
        """
        Flushes all scripts from the script cache
        """
        pieces: CommandArgList = []

        if sync_type:
            pieces = [sync_type.value]

        return await self.execute_command("SCRIPT FLUSH", *pieces)

    @redis_command(
        "SCRIPT KILL",
        group=CommandGroup.SCRIPTING,
        response_callback=SimpleStringCallback(),
    )
    async def script_kill(self) -> bool:
        """
        Kills the currently executing Lua script
        """

        return await self.execute_command("SCRIPT KILL")

    @redis_command(
        "SCRIPT LOAD",
        group=CommandGroup.SCRIPTING,
        cluster=ClusterCommandConfig(
            flag=NodeFlag.PRIMARIES,
            combine=lambda res: res and list(res.values()).pop(),
        ),
    )
    async def script_load(self, script: ValueT) -> AnyStr:
        """
        Loads a Lua ``script`` into the script cache.

        :return: The SHA1 digest of the script added into the script cache
        """

        return await self.execute_command("SCRIPT LOAD", script)

    def register_script(self, script: ValueT):
        """
        Registers a Lua ``script`` specifying the ``keys`` it will touch.
        Returns a Script object that is callable and hides the complexity of
        dealing with scripts, keys, and shas. This is the preferred way of
        working with Lua scripts.
        """
        from coredis.commands.builders.script import Script

        return Script(self, script)  # type: ignore

    @redis_command(
        "BGREWRITEAOF",
        group=CommandGroup.CONNECTION,
        response_callback=SimpleStringCallback(),
    )
    async def bgrewriteaof(self) -> bool:
        """Tell the Redis server to rewrite the AOF file from data in memory"""

        return await self.execute_command("BGREWRITEAOF")

    @redis_command(
        "BGSAVE",
        group=CommandGroup.CONNECTION,
        response_callback=SimpleStringCallback(),
    )
    async def bgsave(self, schedule: Optional[bool] = None) -> bool:
        """
        Tells the Redis server to save its data to disk.  Unlike save(),
        this method is asynchronous and returns immediately.
        """
        pieces = []
        if schedule is not None:
            pieces.append(PureToken.SCHEDULE)
        return await self.execute_command("BGSAVE", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "CLIENT CACHING",
        version_introduced="6.0.0",
        group=CommandGroup.CONNECTION,
        response_callback=SimpleStringCallback(),
    )
    async def client_caching(self, mode: Literal[PureToken.YES, PureToken.NO]) -> bool:
        """
        Instruct the server about tracking or not keys in the next request
        """
        pieces = [mode.value]
        return await self.execute_command("CLIENT CACHING", *pieces)

    @redis_command(
        "CLIENT KILL",
        group=CommandGroup.CONNECTION,
        arguments={"laddr": {"version_introduced": "6.2.0"}},
        response_callback=SimpleStringOrIntCallback(),
    )
    async def client_kill(
        self,
        ip_port: Optional[ValueT] = None,
        identifier: Optional[int] = None,
        type_: Optional[
            Literal[
                PureToken.NORMAL,
                PureToken.MASTER,
                PureToken.SLAVE,
                PureToken.REPLICA,
                PureToken.PUBSUB,
            ]
        ] = None,
        user: Optional[ValueT] = None,
        addr: Optional[ValueT] = None,
        laddr: Optional[ValueT] = None,
        skipme: Optional[bool] = None,
    ) -> Union[int, bool]:
        """
        Disconnects the client at ``ip_port``

        :return: True if the connection exists and has been closed
         or the number of clients killed.
        """

        pieces: CommandArgList = []

        if ip_port:
            pieces.append(ip_port)

        if identifier:
            pieces.extend(["ID", identifier])

        if type_:
            pieces.extend(["TYPE", type_.value])

        if user:
            pieces.extend(["USER", user])

        if addr:
            pieces.extend(["ADDR", addr])

        if laddr:
            pieces.extend(["LADDR", laddr])

        if skipme is not None:
            pieces.extend(["SKIPME", skipme and "yes" or "no"])

        return await self.execute_command("CLIENT KILL", *pieces)

    @redis_command(
        "CLIENT LIST",
        group=CommandGroup.CONNECTION,
        arguments={
            "identifiers": {"version_introduced": "6.2.0"},
        },
        response_callback=ClientListCallback(),
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def client_list(
        self,
        type_: Optional[
            Literal[
                PureToken.NORMAL, PureToken.MASTER, PureToken.REPLICA, PureToken.PUBSUB
            ]
        ] = None,
        identifiers: Optional[Iterable[int]] = None,
    ) -> Tuple[ClientInfo, ...]:
        """
        Get client connections

        :return: a tuple of dictionaries containing client fields
        """

        pieces: CommandArgList = []

        if type_:
            pieces.extend(["TYPE", type_.value])

        if identifiers is not None:
            pieces.append("ID")
            pieces.extend(identifiers)

        return await self.execute_command("CLIENT LIST", *pieces)

    @redis_command(
        "CLIENT GETNAME",
        group=CommandGroup.CONNECTION,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def client_getname(self) -> Optional[AnyStr]:
        """
        Returns the current connection name

        :return: The connection name, or ``None`` if no name is set.
        """

        return await self.execute_command("CLIENT GETNAME")

    @redis_command(
        "CLIENT SETNAME",
        group=CommandGroup.CONNECTION,
        response_callback=SimpleStringCallback(),
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def client_setname(self, connection_name: ValueT) -> bool:
        """
        Set the current connection name
        :return: If the connection name was successfully set.
        """

        return await self.execute_command("CLIENT SETNAME", connection_name)

    @redis_command(
        "CLIENT PAUSE",
        group=CommandGroup.CONNECTION,
        arguments={"mode": {"version_introduced": "6.2.0"}},
        response_callback=SimpleStringCallback(),
    )
    async def client_pause(
        self,
        timeout: int,
        mode: Optional[Literal[PureToken.WRITE, PureToken.ALL]] = None,
    ) -> bool:
        """
        Stop processing commands from clients for some time

        :return: The command returns ``True`` or raises an error if the timeout is invalid.
        """

        pieces: CommandArgList = [timeout]
        if mode is not None:
            pieces.append(mode.value)
        return await self.execute_command("CLIENT PAUSE", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "CLIENT UNPAUSE",
        version_introduced="6.2.0",
        group=CommandGroup.CONNECTION,
        response_callback=SimpleStringCallback(),
    )
    async def client_unpause(self) -> bool:
        """
        Resume processing of clients that were paused

        :return: The command returns ```True```
        """

        return await self.execute_command("CLIENT UNPAUSE")

    @versionadded(version="3.0.0")
    @redis_command("CLIENT UNBLOCK", group=CommandGroup.CONNECTION)
    async def client_unblock(
        self,
        client_id: int,
        timeout_error: Optional[Literal[PureToken.TIMEOUT, PureToken.ERROR]] = None,
    ) -> bool:
        """
        Unblock a client blocked in a blocking command from a different connection

        :return: Whether the client was unblocked
        """
        pieces: CommandArgList = [client_id]

        if timeout_error is not None:
            pieces.append(timeout_error.value)

        return await self.execute_command("CLIENT UNBLOCK", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "CLIENT GETREDIR", version_introduced="6.0.0", group=CommandGroup.CONNECTION
    )
    async def client_getredir(self) -> int:
        """
        Get tracking notifications redirection client ID if any

        :return: the ID of the client we are redirecting the notifications to.
         The command returns ``-1`` if client tracking is not enabled,
         or ``0`` if client tracking is enabled but we are not redirecting the
         notifications to any client.
        """

        return await self.execute_command("CLIENT GETREDIR")

    @versionadded(version="3.0.0")
    @redis_command("CLIENT ID", group=CommandGroup.CONNECTION)
    async def client_id(self) -> int:
        """
        Returns the client ID for the current connection

        :return: The id of the client.
        """

        return await self.execute_command("CLIENT ID")

    @versionadded(version="3.0.0")
    @redis_command(
        "CLIENT INFO",
        version_introduced="6.2.0",
        group=CommandGroup.CONNECTION,
        response_callback=ClientInfoCallback(),
    )
    async def client_info(self) -> ClientInfo:
        """
        Returns information about the current client connection.
        """

        return await self.execute_command("CLIENT INFO")

    @versionadded(version="3.0.0")
    @redis_command(
        "CLIENT REPLY",
        group=CommandGroup.CONNECTION,
        response_callback=SimpleStringCallback(),
    )
    async def client_reply(
        self, mode: Literal[PureToken.ON, PureToken.OFF, PureToken.SKIP]
    ) -> bool:
        """
        Instruct the server whether to reply to commands
        """

        return await self.execute_command("CLIENT REPLY", mode.value)

    @versionadded(version="3.0.0")
    @redis_command(
        "CLIENT TRACKING",
        version_introduced="6.0.0",
        group=CommandGroup.CONNECTION,
        response_callback=SimpleStringCallback(),
    )
    async def client_tracking(
        self,
        status: Literal[PureToken.ON, PureToken.OFF],
        *prefixes: ValueT,
        redirect: Optional[int] = None,
        bcast: Optional[bool] = None,
        optin: Optional[bool] = None,
        optout: Optional[bool] = None,
        noloop: Optional[bool] = None,
    ) -> bool:

        """
        Enable or disable server assisted client side caching support

        :return: If the connection was successfully put in tracking mode or if the
         tracking mode was successfully disabled.
        """

        pieces: CommandArgList = [status.value]

        if prefixes:
            pieces.extend(prefixes)

        if redirect is not None:
            pieces.extend(["REDIRECT", redirect])

        if bcast is not None:
            pieces.append(PureToken.BCAST.value)

        if optin is not None:
            pieces.append(PureToken.OPTIN.value)

        if optout is not None:
            pieces.append(PureToken.OPTOUT.value)

        if noloop is not None:
            pieces.append(PureToken.NOLOOP.value)

        return await self.execute_command("CLIENT TRACKING", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "CLIENT TRACKINGINFO",
        version_introduced="6.2.0",
        group=CommandGroup.CONNECTION,
        response_callback=DictCallback(pairs_to_dict),
    )
    async def client_trackinginfo(self) -> Dict[AnyStr, AnyStr]:
        """
        Return information about server assisted client side caching for the current connection

        :return: a mapping of tracking information sections and their respective values
        """

        return await self.execute_command("CLIENT TRACKINGINFO")

    @redis_command(
        "DBSIZE",
        readonly=True,
        group=CommandGroup.SERVER,
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def dbsize(self) -> int:
        """Returns the number of keys in the current database"""

        return await self.execute_command("DBSIZE")

    @redis_command(
        "DEBUG OBJECT", group=CommandGroup.SERVER, response_callback=DebugCallback()
    )
    async def debug_object(self, key: KeyT):
        """Returns version specific meta information about a given key"""

        return await self.execute_command("DEBUG OBJECT", key)

    @mutually_inclusive_parameters("host", "port")
    @versionadded(version="3.0.0")
    @redis_command(
        "FAILOVER",
        version_introduced="6.2.0",
        group=CommandGroup.SERVER,
        response_callback=SimpleStringCallback(),
    )
    async def failover(
        self,
        host: Optional[ValueT] = None,
        port: Optional[int] = None,
        force: Optional[bool] = None,
        abort: Optional[bool] = None,
        timeout: Optional[Union[int, datetime.timedelta]] = None,
    ) -> bool:
        """
        Start a coordinated failover between this server and one of its replicas.

        :return: `True` if the command was accepted and a coordinated failover
         is in progress.
        """
        pieces = []
        if host and port:
            pieces.extend(["TO", host, port])
            if force is not None:
                pieces.append(PureToken.FORCE.value)
        if abort:
            pieces.append(PureToken.ABORT.value)
        if timeout is not None:
            pieces.append(normalized_milliseconds(timeout))
        return await self.execute_command("FAILOVER", *pieces)

    @redis_command(
        "FLUSHALL",
        group=CommandGroup.SERVER,
        response_callback=SimpleStringCallback(),
        cluster=ClusterCommandConfig(
            flag=NodeFlag.PRIMARIES,
            combine=lambda res: res and list(res.values()).pop(),
            pipeline=False,
        ),
    )
    async def flushall(
        self, async_: Optional[Literal[PureToken.ASYNC, PureToken.SYNC]] = None
    ) -> bool:
        """Deletes all keys in all databases on the current host"""
        pieces: CommandArgList = []

        if async_:
            pieces.append(async_.value)

        return await self.execute_command("FLUSHALL", *pieces)

    @redis_command(
        "FLUSHDB",
        group=CommandGroup.SERVER,
        response_callback=SimpleStringCallback(),
        cluster=ClusterCommandConfig(
            flag=NodeFlag.PRIMARIES,
            combine=lambda res: res and list(res.values()).pop(),
            pipeline=False,
        ),
    )
    async def flushdb(
        self, async_: Optional[Literal[PureToken.ASYNC, PureToken.SYNC]] = None
    ) -> bool:
        """Deletes all keys in the current database"""
        pieces: CommandArgList = []

        if async_:
            pieces.append(async_.value)

        return await self.execute_command("FLUSHDB", *pieces)

    @redis_command(
        "INFO",
        group=CommandGroup.SERVER,
        response_callback=InfoCallback(),
    )
    async def info(self, *sections: ValueT) -> Dict[AnyStr, AnyStr]:
        """
        Get information and statistics about the server

        The ``section`` option can be used to select a specific section
        of information

        The section option is not supported by older versions of Redis Server,
        and will generate ResponseError
        """

        if sections is None:
            return await self.execute_command("INFO")
        else:
            return await self.execute_command("INFO", *sections)

    @redis_command(
        "LASTSAVE", group=CommandGroup.SERVER, response_callback=DateTimeCallback()
    )
    async def lastsave(self) -> datetime.datetime:
        """
        Get the time of the last successful save to disk
        """

        return await self.execute_command("LASTSAVE")

    @versionadded(version="3.0.0")
    @redis_command("LATENCY DOCTOR", group=CommandGroup.SERVER)
    async def latency_doctor(self) -> AnyStr:
        """
        Return a human readable latency analysis report.
        """

        return await self.execute_command("LATENCY DOCTOR")

    @versionadded(version="3.0.0")
    @redis_command("LATENCY GRAPH", group=CommandGroup.SERVER)
    async def latency_graph(self, event: ValueT) -> AnyStr:
        """
        Return a latency graph for the event.
        """
        pieces: CommandArgList = []
        # Handle event
        pieces.append(event)

        return await self.execute_command("LATENCY GRAPH", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "LATENCY HISTORY", group=CommandGroup.SERVER, response_callback=TupleCallback()
    )
    async def latency_history(self, event: ValueT) -> Tuple[AnyStr, ...]:
        """
        Return timestamp-latency samples for the event.

        :return: The command returns a tuple where each element is a tuple
         representing the timestamp and the latency of the event.

        """
        pieces: CommandArgList = [event]
        return await self.execute_command("LATENCY HISTORY", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "LATENCY LATEST",
        group=CommandGroup.SERVER,
        response_callback=DictCallback(transform_function=quadruples_to_dict),
    )
    async def latency_latest(self) -> Dict[AnyStr, Tuple[int, int, int]]:
        """
        Return the latest latency samples for all events.

        :return: Mapping of event name to (timestamp, latest, all-time) triplet
        """

        return await self.execute_command("LATENCY LATEST")

    @versionadded(version="3.0.0")
    @redis_command("LATENCY RESET", group=CommandGroup.SERVER)
    async def latency_reset(self, events: Optional[Iterable[ValueT]] = None) -> int:
        """
        Reset latency data for one or more events.

        :return: the number of event time series that were reset.
        """
        pieces: CommandArgList = list(events) if events else []
        return await self.execute_command("LATENCY RESET", *pieces)

    @versionadded(version="3.0.0")
    @redis_command("MEMORY DOCTOR", group=CommandGroup.SERVER)
    async def memory_doctor(self) -> AnyStr:
        """
        Outputs memory problems report
        :return:

        """

        return await self.execute_command("MEMORY DOCTOR")

    @versionadded(version="3.0.0")
    @redis_command("MEMORY MALLOC-STATS", group=CommandGroup.SERVER)
    async def memory_malloc_stats(self) -> AnyStr:
        """
        Show allocator internal stats
        :return: the memory allocator's internal statistics report
        """

        return await self.execute_command("MEMORY MALLOC-STATS")

    @versionadded(version="3.0.0")
    @redis_command(
        "MEMORY PURGE",
        group=CommandGroup.SERVER,
        response_callback=SimpleStringCallback(),
    )
    async def memory_purge(self) -> bool:
        """
        Ask the allocator to release memory
        :return:
        """

        return await self.execute_command("MEMORY PURGE")

    @versionadded(version="3.0.0")
    @redis_command(
        "MEMORY STATS",
        group=CommandGroup.SERVER,
        response_callback=DictCallback(transform_function=pairs_to_dict),
    )
    async def memory_stats(self) -> Dict[AnyStr, Union[AnyStr, int, float]]:
        """
        Show memory usage details
        :return: mapping of memory usage metrics and their values

        """

        return await self.execute_command("MEMORY STATS")

    @versionadded(version="3.0.0")
    @redis_command("MEMORY USAGE", readonly=True, group=CommandGroup.SERVER)
    async def memory_usage(
        self, key: KeyT, *, samples: Optional[int] = None
    ) -> Optional[int]:
        """
        Estimate the memory usage of a key

        :return: the memory usage in bytes, or ``None`` when the key does not exist.

        """
        pieces: CommandArgList = []
        pieces.append(key)

        if samples is not None:
            pieces.append(samples)

        return await self.execute_command("MEMORY USAGE", *pieces)

    @redis_command(
        "SAVE",
        group=CommandGroup.SERVER,
        response_callback=SimpleStringCallback(),
    )
    async def save(self) -> bool:
        """
        Tells the Redis server to save its data to disk,
        blocking until the save is complete
        """

        return await self.execute_command("SAVE")

    @redis_command(
        "SHUTDOWN",
        group=CommandGroup.SERVER,
        response_callback=SimpleStringCallback(),
    )
    async def shutdown(
        self, nosave_save: Optional[Literal[PureToken.NOSAVE, PureToken.SAVE]] = None
    ) -> bool:
        """Stops Redis server"""
        pieces: CommandArgList = []

        if nosave_save:
            pieces.append(nosave_save.value)
        try:
            await self.execute_command("SHUTDOWN", *pieces)
        except ConnectionError:
            # a ConnectionError here is expected

            return True
        raise RedisError("SHUTDOWN seems to have failed.")

    @redis_command("SLAVEOF", version_deprecated="5.0.0", group=CommandGroup.SERVER)
    async def slaveof(self, host: ValueT, port: ValueT) -> bool:
        """
        Sets the server to be a replicated slave of the instance identified
        by the ``host`` and ``port``. If called without arguments, the
        instance is promoted to a master instead.
        """

        if host is None and port is None:
            return await self.execute_command("SLAVEOF", b("NO"), b("ONE"))

        return await self.execute_command("SLAVEOF", host, port)

    @redis_command(
        "SLOWLOG GET", group=CommandGroup.SERVER, response_callback=SlowlogCallback()
    )
    async def slowlog_get(self, count: Optional[int] = None) -> Tuple[SlowLogInfo, ...]:
        """
        Gets the entries from the slowlog. If ``count`` is specified, get the
        most recent ``count`` items.
        """
        pieces: CommandArgList = []

        if count is not None:
            pieces.append(count)

        return await self.execute_command("SLOWLOG GET", *pieces)

    @redis_command("SLOWLOG LEN", group=CommandGroup.SERVER)
    async def slowlog_len(self) -> int:
        """Gets the number of items in the slowlog"""

        return await self.execute_command("SLOWLOG LEN")

    @redis_command(
        "SLOWLOG RESET",
        group=CommandGroup.SERVER,
        response_callback=BoolCallback(),
    )
    async def slowlog_reset(self) -> bool:
        """Removes all items in the slowlog"""

        return await self.execute_command("SLOWLOG RESET")

    @redis_command(
        "TIME",
        group=CommandGroup.SERVER,
        response_callback=TimeCallback(),
    )
    async def time(self) -> datetime.datetime:
        """
        Returns the server time as a 2-item tuple of ints:
        (seconds since epoch, microseconds into this second).
        """

        return await self.execute_command("TIME")

    @versionadded(version="3.0.0")
    @redis_command(
        "REPLICAOF", group=CommandGroup.SERVER, response_callback=SimpleStringCallback()
    )
    async def replicaof(self, *, host: ValueT, port: ValueT) -> bool:
        """
        Make the server a replica of another instance, or promote it as master.
        """
        pieces = [host, port]
        return await self.execute_command("REPLICAOF", *pieces)

    @redis_command("ROLE", group=CommandGroup.SERVER, response_callback=RoleCallback())
    async def role(self) -> RoleInfo:
        """
        Provides information on the role of a Redis instance in the context of replication,
        by returning if the instance is currently a master, slave, or sentinel.
        The command also returns additional information about the state of the replication
        (if the role is master or slave)
        or the list of monitored master names (if the role is sentinel).
        """

        return await self.execute_command("ROLE")

    @versionadded(version="3.0.0")
    @redis_command(
        "SWAPDB", group=CommandGroup.SERVER, response_callback=SimpleStringCallback()
    )
    async def swapdb(self, *, index1: int, index2: int) -> bool:
        """
        Swaps two Redis databases
        """
        pieces = [index1, index2]
        return await self.execute_command("SWAPDB", *pieces)

    @redis_command("LOLWUT", readonly=True, group=CommandGroup.SERVER)
    async def lolwut(self, version: Optional[int] = None) -> AnyStr:
        """
        Get the Redis version and a piece of generative computer art
        """
        pieces = []
        if version is not None:
            pieces.append(version)
        return await self.execute_command("LOLWUT VERSION", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "ACL CAT",
        version_introduced="6.0.0",
        group=CommandGroup.SERVER,
        response_callback=TupleCallback(),
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def acl_cat(
        self, categoryname: Optional[ValueT] = None
    ) -> Tuple[AnyStr, ...]:
        """
        List the ACL categories or the commands inside a category


        :return: a list of ACL categories or a list of commands inside a given category.
         The command may return an error if an invalid category name is given as argument.

        """

        pieces: CommandArgList = []

        if categoryname:
            pieces.append(categoryname)

        return await self.execute_command("ACL CAT", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "ACL DELUSER",
        version_introduced="6.0.0",
        group=CommandGroup.SERVER,
    )
    async def acl_deluser(self, usernames: Iterable[ValueT]) -> int:
        """
        Remove the specified ACL users and the associated rules


        :return: The number of users that were deleted.
         This number will not always match the number of arguments since
         certain users may not exist.
        """

        return await self.execute_command("ACL DELUSER", *usernames)

    @versionadded(version="3.0.0")
    @redis_command(
        "ACL GENPASS",
        version_introduced="6.0.0",
        group=CommandGroup.SERVER,
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def acl_genpass(self, bits: Optional[int] = None) -> AnyStr:
        """
        Generate a pseudorandom secure password to use for ACL users


        :return: by default 64 bytes string representing 256 bits of pseudorandom data.
         Otherwise if an argument if needed, the output string length is the number of
         specified bits (rounded to the next multiple of 4) divided by 4.
        """
        pieces: CommandArgList = []

        if bits is not None:
            pieces.append(bits)

        return await self.execute_command("ACL GENPASS", *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "ACL GETUSER",
        version_introduced="6.0.0",
        group=CommandGroup.SERVER,
        response_callback=DictCallback(transform_function=pairs_to_dict),
    )
    async def acl_getuser(self, username: ValueT) -> Dict[AnyStr, List[AnyStr]]:
        """
        Get the rules for a specific ACL user

        :return:
        """

        return await self.execute_command("ACL GETUSER", username)

    @versionadded(version="3.0.0")
    @redis_command(
        "ACL LIST",
        version_introduced="6.0.0",
        group=CommandGroup.SERVER,
        response_callback=TupleCallback(),
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def acl_list(self) -> Tuple[AnyStr, ...]:
        """
        List the current ACL rules in ACL config file format

        :return:
        """

        return await self.execute_command("ACL LIST")

    @versionadded(version="3.0.0")
    @redis_command(
        "ACL LOAD",
        version_introduced="6.0.0",
        group=CommandGroup.SERVER,
        response_callback=BoolCallback(),
    )
    async def acl_load(self) -> bool:
        """
        Reload the ACLs from the configured ACL file

        :return: True if successful. The command may fail with an error for several reasons:

         - if the file is not readable
         - if there is an error inside the file, and in such case the error will be reported to
           the user in the error.
         - Finally the command will fail if the server is not configured to use an external
           ACL file.

        """

        return await self.execute_command("ACL LOAD")

    @versionadded(version="3.0.0")
    @mutually_exclusive_parameters("count", "reset")
    @redis_command(
        "ACL LOG",
        version_introduced="6.0.0",
        group=CommandGroup.SERVER,
        response_callback=ACLLogCallback(),
    )
    async def acl_log(
        self, count: Optional[int] = None, reset: Optional[bool] = None
    ) -> Union[Tuple[Dict[AnyStr, AnyStr], ...], bool]:
        """
        List latest events denied because of ACLs in place

        :return: When called to show security events a list of ACL security events.
         When called with ``RESET`` True if the security log was cleared.

        """

        pieces: CommandArgList = []
        if count is not None:
            pieces.append(count)

        if reset is not None:
            pieces.append("RESET")
        return await self.execute_command("ACL LOG", *pieces, reset=reset)

    @versionadded(version="3.0.0")
    @redis_command(
        "ACL SAVE",
        version_introduced="6.0.0",
        group=CommandGroup.SERVER,
        response_callback=BoolCallback(),
    )
    async def acl_save(self) -> bool:
        """
        Save the current ACL rules in the configured ACL file

        :return: True if successful. The command may fail with an error for several reasons:
         - if the file cannot be written, or
         - if the server is not configured to use an external ACL file.

        """

        return await self.execute_command("ACL SAVE")

    @versionadded(version="3.0.0")
    @redis_command(
        "ACL SETUSER",
        version_introduced="6.0.0",
        group=CommandGroup.SERVER,
        response_callback=SimpleStringCallback(),
    )
    async def acl_setuser(
        self,
        username: ValueT,
        *rules: ValueT,
    ) -> bool:
        """
        Modify or create the rules for a specific ACL user


        :return: True if successful. If the rules contain errors, the error is returned.
        """
        pieces: CommandArgList = []
        if rules:
            pieces.extend(rules)
        return await self.execute_command("ACL SETUSER", username, *pieces)

    @versionadded(version="3.0.0")
    @redis_command(
        "ACL USERS",
        version_introduced="6.0.0",
        group=CommandGroup.SERVER,
        response_callback=TupleCallback(),
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def acl_users(self) -> Tuple[AnyStr, ...]:
        """
        List the username of all the configured ACL rules

        :return:
        """

        return await self.execute_command("ACL USERS")

    @versionadded(version="3.0.0")
    @redis_command(
        "ACL WHOAMI",
        version_introduced="6.0.0",
        group=CommandGroup.SERVER,
        cluster=ClusterCommandConfig(flag=NodeFlag.RANDOM),
    )
    async def acl_whoami(self) -> AnyStr:
        """
        Return the name of the user associated to the current connection


        :return: the username of the current connection.
        """

        return await self.execute_command("ACL WHOAMI")

    @versionadded(version="3.0.0")
    @redis_command(
        "COMMAND",
        group=CommandGroup.SERVER,
        response_callback=CommandCallback(),
    )
    async def command(self) -> Dict[AnyStr, Command]:
        """
        Get Redis command details

        :return: Mapping of command details.  Commands are returned
         in random order.
        """

        return await self.execute_command("COMMAND")

    @versionadded(version="3.0.0")
    @redis_command(
        "COMMAND COUNT",
        group=CommandGroup.SERVER,
    )
    async def command_count(self) -> int:
        """
        Get total number of Redis commands

        :return: number of commands returned by ``COMMAND``
        """

        return await self.execute_command("COMMAND COUNT")

    @versionadded(version="3.0.0")
    @redis_command(
        "COMMAND GETKEYS",
        group=CommandGroup.SERVER,
    )
    async def command_getkeys(
        self, command: ValueT, arguments: Iterable[ValueT]
    ) -> Tuple[AnyStr, ...]:
        """
        Extract keys given a full Redis command

        :return: keys from your command.
        """

        return await self.execute_command("COMMAND GETKEYS", command, *arguments)

    @versionadded(version="3.0.0")
    @redis_command(
        "COMMAND INFO",
        group=CommandGroup.SERVER,
        response_callback=CommandCallback(),
    )
    async def command_info(self, *command_names: ValueT) -> Dict[AnyStr, Command]:
        """
        Get specific Redis command details, or all when no argument is given.

        :return: mapping of command details.

        """
        pieces = command_names if command_names else []
        return await self.execute_command("COMMAND INFO", *pieces)

    @redis_command(
        "CONFIG GET",
        group=CommandGroup.SERVER,
        response_callback=DictCallback(pairs_to_dict),
    )
    async def config_get(self, parameters: Iterable[ValueT]) -> Dict[AnyStr, AnyStr]:
        """
        Get the values of configuration parameters
        """

        return await self.execute_command("CONFIG GET", *parameters)

    @redis_command(
        "CONFIG SET",
        group=CommandGroup.SERVER,
        response_callback=SimpleStringCallback(),
        cluster=ClusterCommandConfig(pipeline=False),
    )
    async def config_set(self, parameter_values: Dict[ValueT, ValueT]) -> bool:
        """Sets configuration parameters to the given values"""
        return await self.execute_command(
            "CONFIG SET", *itertools.chain(*parameter_values.items())
        )

    @redis_command(
        "CONFIG RESETSTAT",
        group=CommandGroup.SERVER,
        response_callback=SimpleStringCallback(),
    )
    async def config_resetstat(self) -> bool:
        """Resets runtime statistics"""

        return await self.execute_command("CONFIG RESETSTAT")

    @redis_command("CONFIG REWRITE", group=CommandGroup.SERVER)
    async def config_rewrite(self) -> bool:
        """
        Rewrites config file with the minimal change to reflect running config
        """

        return await self.execute_command("CONFIG REWRITE")
