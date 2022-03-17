from typing import Dict, NamedTuple, Optional, Tuple, TypedDict, Union

from typing_extensions import OrderedDict, TypeAlias


class ClientInfo(TypedDict):
    """
    Response from `CLIENT INFO <https://redis.io/commands/client-info>`__
    """

    #: a unique 64-bit client ID
    id: int
    #: address/port of the client
    addr: str
    #: address/port of local address client connected to (bind address)
    laddr: str
    #: file descriptor corresponding to the socket
    fd: int
    #: the name set by the client with CLIENT SETNAME
    name: str
    #: total duration of the connection in seconds
    age: int
    #: idle time of the connection in seconds
    idle: int
    #: client flags
    flags: str
    #: current database ID
    db: int
    #: number of channel subscriptions
    sub: int
    #: number of pattern matching subscriptions
    psub: int
    #: number of commands in a MULTI/EXEC context
    multi: int
    #: query buffer length (0 means no query pending)
    qbuf: int
    #: free space of the query buffer (0 means the buffer is full)
    qbuf_free: int
    #: incomplete arguments for the next command (already extracted from query buffer)
    argv_mem: int
    #: memory is used up by buffered multi commands. Added in Redis 7.0
    multi_mem: int
    #: output buffer length
    obl: int
    #: output list length (replies are queued in this list when the buffer is full)
    oll: int
    #: output buffer memory usage
    omem: int
    #: total memory consumed by this client in its various buffers
    tot_mem: int
    #: file descriptor events
    events: str
    #: last command played
    cmd: str
    #: the authenticated username of the client
    user: str
    #: client id of current client tracking redirection
    redir: int
    #: client RESP protocol version. Added in Redis 7.0
    resp: str


class ScoredMember(NamedTuple):
    """
    Member of a sorted set
    """

    #: The sorted set member name
    member: Union[str, bytes]
    #: Score of the member
    score: float


class GeoCoordinates(NamedTuple):
    """
    A latitude/longitude pair identifying a location
    """

    #: Latitude
    latitude: float
    #: Longitude
    longitude: float


ScoredMembers: TypeAlias = Tuple[ScoredMember, ...]


class GeoSearchResult(NamedTuple):
    """
    Structure of a geo query
    """

    #: Place name
    name: Union[str, bytes]
    #: Distance
    distance: Optional[float]
    #: GeoHash
    geohash: Optional[int]
    #: Lat/Lon
    coordinates: Optional[GeoCoordinates]


class Command(TypedDict):
    """
    Definition of a redis command
    See: `<https://redis.io/topics/key-specs>`__
    """

    #: This is the command's name in lowercase
    name: str
    #: Arity is the number of arguments a command expects.
    arity: int
    #: See `<https://redis.io/commands/command#flags>`__
    flags: Tuple[str, ...]
    #: This value identifies the position of the command's first key name argumen
    first_key: str
    #: This value identifies the position of the command's last key name argument
    last_key: str
    #: This value is the step, or increment, between the first key and last key values
    #  where the keys are.
    step: int
    #: This is an array of simple strings that are the ACL categories to which the command belongs
    acl_categories: Optional[Tuple[str, ...]]
    #: Helpful information about the command
    tips: Optional[str]
    #: This is an array consisting of the command's key specifications
    key_specifications: Optional[Tuple[str, ...]]
    #: This is an array containing all of the command's subcommands, if any
    sub_commands: Optional[Tuple[str, ...]]


class RoleInfo(TypedDict):
    """
    Redis instance role information
    """

    role: str
    offset: int
    status: str
    slaves: Tuple[Dict[str, Union[str, int]], ...]
    master: Tuple[str, ...]


class StreamEntry(NamedTuple):
    """
    Structure representing an entry in a redis stream
    """

    identifier: Union[bytes, str]
    field_values: OrderedDict[Union[bytes, str], Union[bytes, str]]


class StreamInfo(TypedDict):
    """
    Details of a stream
    """

    length: int
    radix_tree_keys: int
    radix_tree_nodes: int
    groups: int
    last_generated_id: int
    first_entry: Optional[StreamEntry]
    last_entry: Optional[StreamEntry]


class StreamPending(NamedTuple):
    """
    Summary response from
    `XPENDING <https://redis.io/commands/xpending#summary-form-of-xpending>`__
    """

    pending: int
    minimum_identifier: Union[bytes, str]
    maximum_identifier: Union[bytes, str]
    consumers: OrderedDict[Union[bytes, str, int], Union[bytes, str, int]]


class StreamPendingExt(NamedTuple):
    """
    Extended form response from
    `XPENDING <https://redis.io/commands/xpending#extended-form-of-xpending>`__
    """

    identifier: Union[bytes, str]
    consumer: Union[bytes, str]
    idle: int
    delivered: int


class SlowLogInfo(TypedDict):
    """
    Response from `SLOWLOG GET <https://redis.io/commands/slowlog-get>`__
    """

    id: int
    start_time: int
    duration: int
    command: Tuple[Union[bytes, str], ...]
