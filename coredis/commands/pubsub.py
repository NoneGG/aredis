from coredis.pubsub import PubSub, ClusterPubSub
from coredis.utils import dict_merge, merge_result, list_keys_to_dict, NodeFlag


def parse_pubsub_numsub(response, **options):
    return list(zip(response[0::2], response[1::2]))


class PubSubCommandMixin:

    RESPONSE_CALLBACKS = {
        "PUBSUB NUMSUB": parse_pubsub_numsub,
    }

    def pubsub(self, **kwargs):
        """
        Return a Publish/Subscribe object. With this object, you can
        subscribe to channels and listen for messages that get published to
        them.
        """
        return PubSub(self.connection_pool, **kwargs)

    async def publish(self, channel, message):
        """
        Publish ``message`` on ``channel``.
        Returns the number of subscribers the message was delivered to.
        """
        return await self.execute_command("PUBLISH", channel, message)

    async def pubsub_channels(self, pattern="*"):
        """
        Return a list of channels that have at least one subscriber
        """
        return await self.execute_command("PUBSUB CHANNELS", pattern)

    async def pubsub_numpat(self):
        """
        Returns the number of subscriptions to patterns
        """
        return await self.execute_command("PUBSUB NUMPAT")

    async def pubsub_numsub(self, *args):
        """
        Return a list of (channel, number of subscribers) tuples
        for each channel given in ``*args``
        """
        return await self.execute_command("PUBSUB NUMSUB", *args)


def parse_cluster_pubsub_channels(res, **options):
    """
    Result callback, handles different return types
    switchable by the `aggregate` flag.
    """
    aggregate = options.get("aggregate", True)
    if not aggregate:
        return res
    return merge_result(res)


def parse_cluster_pubsub_numpat(res, **options):
    """
    Result callback, handles different return types
    switchable by the `aggregate` flag.
    """
    aggregate = options.get("aggregate", True)
    if not aggregate:
        return res

    numpat = 0
    for node, node_numpat in res.items():
        numpat += node_numpat
    return numpat


def parse_cluster_pubsub_numsub(res, **options):
    """
    Result callback, handles different return types
    switchable by the `aggregate` flag.
    """
    aggregate = options.get("aggregate", True)
    if not aggregate:
        return res

    numsub_d = dict()
    for _, numsub_tups in res.items():
        for channel, numsubbed in numsub_tups:
            try:
                numsub_d[channel] += numsubbed
            except KeyError:
                numsub_d[channel] = numsubbed

    ret_numsub = []
    for channel, numsub in numsub_d.items():
        ret_numsub.append((channel, numsub))
    return ret_numsub


class CLusterPubSubCommandMixin(PubSubCommandMixin):

    NODES_FLAGS = dict_merge(
        list_keys_to_dict(
            ["PUBSUB CHANNELS", "PUBSUB NUMSUB", "PUBSUB NUMPAT"], NodeFlag.ALL_NODES
        )
    )

    RESULT_CALLBACKS = dict_merge(
        list_keys_to_dict(["PUBSUB CHANNELS",], parse_cluster_pubsub_channels),
        list_keys_to_dict(["PUBSUB NUMSUB",], parse_cluster_pubsub_numsub),
        list_keys_to_dict(["PUBSUB NUMPAT",], parse_cluster_pubsub_numpat),
    )

    def pubsub(self, **kwargs):
        return ClusterPubSub(self.connection_pool, **kwargs)
