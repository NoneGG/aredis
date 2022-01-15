class RedisError(Exception):
    pass


class ConnectionError(RedisError):
    pass


class TimeoutError(RedisError):
    pass


class BusyLoadingError(ConnectionError):
    pass


class InvalidResponse(RedisError):
    pass


class ResponseError(RedisError):
    pass


class DataError(RedisError):
    pass


class PubSubError(RedisError):
    pass


class WatchError(RedisError):
    pass


class NoScriptError(ResponseError):
    pass


class ExecAbortError(ResponseError):
    pass


class ReadOnlyError(ResponseError):
    pass


class LockError(RedisError, ValueError):
    """Errors acquiring or releasing a lock"""

    # NOTE: For backwards compatability, this class derives from ValueError.
    # This was originally chosen to behave like threading.Lock.


class CacheError(RedisError):
    """Base exception for :mod:`coredis.cache`"""


class SerializeError(CacheError):
    pass


class CompressError(CacheError):
    pass


class RedisClusterException(Exception):
    """Base exception for the RedisCluster client"""


class ClusterError(RedisError):
    """
    Cluster errors occurred multiple times, resulting in an exhaustion of the
    command execution ``TTL``
    """


class ClusterCrossSlotError(ResponseError):
    """Raised when keys in request don't hash to the same slot"""

    message = "Keys in request don't hash to the same slot"


class ClusterDownError(ClusterError, ResponseError):
    """
    Error indicated ``CLUSTERDOWN`` error received from cluster.

    By default Redis Cluster nodes stop accepting queries if they detect there
    is at least a hash slot uncovered (no available node is serving it).
    This way if the cluster is partially down (for example a range of hash
    slots are no longer covered) the entire cluster eventually becomes
    unavailable. It automatically returns available as soon as all the slots
    are covered again.
    """

    def __init__(self, resp):
        self.args = (resp,)
        self.message = resp


class ClusterTransactionError(ClusterError):
    def __init__(self, msg):
        self.msg = msg


class AskError(ResponseError):
    """
    Error indicated ``ASK`` error received from cluster.

    When a slot is set as ``MIGRATING``, the node will accept all queries that
    pertain to this hash slot, but only if the key in question exists,
    otherwise the query is forwarded using a -ASK redirection to the node that
    is target of the migration.

    src node: ``MIGRATING`` to dst node
        get > ``ASK`` error
        ask dst node > ``ASKING`` command
    dst node: ``IMPORTING`` from src node
        asking command only affects next command
        any op will be allowed after asking command
    """

    def __init__(self, resp):
        self.args = (resp,)
        self.message = resp
        slot_id, new_node = resp.split(" ")
        host, port = new_node.rsplit(":", 1)
        self.slot_id = int(slot_id)
        self.node_addr = self.host, self.port = host, int(port)


class TryAgainError(ResponseError):
    """
    Error indicated ``TRYAGAIN`` error received from cluster.
    Operations on keys that don't exist or are - during resharding - split
    between the source and destination nodes, will generate a -``TRYAGAIN`` error.
    """


class MovedError(AskError):
    """
    Error indicated ``MOVED`` error received from cluster.
    A request sent to a node that doesn't serve this key will be replayed with
    a ``MOVED`` error that points to the correct node.
    """
