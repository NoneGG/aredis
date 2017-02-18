from aredis.pubsub import PubSub


def parse_pubsub_numsub(response, **options):
    return list(zip(response[0::2], response[1::2]))


class PubSubCommanMixin:

    RESPONSE_CALLBACKS = {
        'PUBSUB NUMSUB': parse_pubsub_numsub,
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
        return await self.execute_command('PUBLISH', channel, message)

    async def pubsub_channels(self, pattern='*'):
        """
        Return a list of channels that have at least one subscriber
        """
        return await self.execute_command('PUBSUB CHANNELS', pattern)

    async def pubsub_numpat(self):
        """
        Returns the number of subscriptions to patterns
        """
        return await self.execute_command('PUBSUB NUMPAT')

    async def pubsub_numsub(self, *args):
        """
        Return a list of (channel, number of subscribers) tuples
        for each channel given in ``*args``
        """
        return await self.execute_command('PUBSUB NUMSUB', *args)
