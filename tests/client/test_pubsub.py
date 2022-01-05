from __future__ import with_statement

import asyncio
import pickle
import time

import pytest

import coredis
from coredis.exceptions import ConnectionError
from coredis.utils import b


async def wait_for_message(pubsub, timeout=0.5, ignore_subscribe_messages=False):
    now = time.time()
    timeout = now + timeout
    while now < timeout:
        message = await pubsub.get_message(
            ignore_subscribe_messages=ignore_subscribe_messages, timeout=0.01
        )
        if message is not None:
            return message
        await asyncio.sleep(0.01)
        now = time.time()
    return None


def make_message(type, channel, data, pattern=None):
    return {
        "type": type,
        "pattern": pattern and pattern.encode("utf-8") or None,
        "channel": channel.encode("utf-8"),
        "data": data.encode("utf-8") if isinstance(data, str) else data,
    }


def make_subscribe_test_data(pubsub, type):
    if type == "channel":
        return {
            "p": pubsub,
            "sub_type": "subscribe",
            "unsub_type": "unsubscribe",
            "sub_func": pubsub.subscribe,
            "unsub_func": pubsub.unsubscribe,
            "keys": ["foo", "bar", "uni" + chr(56) + "code",],
        }
    elif type == "pattern":
        return {
            "p": pubsub,
            "sub_type": "psubscribe",
            "unsub_type": "punsubscribe",
            "sub_func": pubsub.psubscribe,
            "unsub_func": pubsub.punsubscribe,
            "keys": ["f*", "b*", "uni" + chr(56) + "*"],
        }
    assert False, "invalid subscribe type: %s" % type


class TestPubSubSubscribeUnsubscribe:
    async def _test_subscribe_unsubscribe(
        self, p, sub_type, unsub_type, sub_func, unsub_func, keys
    ):
        for key in keys:
            assert await sub_func(key) is None

        # should be a message for each channel/pattern we just subscribed to
        for i, key in enumerate(keys):
            assert await wait_for_message(p) == make_message(sub_type, key, i + 1)

        for key in keys:
            assert await unsub_func(key) is None

        # should be a message for each channel/pattern we just unsubscribed
        # from
        for i, key in enumerate(keys):
            i = len(keys) - 1 - i
            assert await wait_for_message(p) == make_message(unsub_type, key, i)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_channel_subscribe_unsubscribe(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), "channel")
        await self._test_subscribe_unsubscribe(**kwargs)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pattern_subscribe_unsubscribe(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), "pattern")
        await self._test_subscribe_unsubscribe(**kwargs)

    async def _test_resubscribe_on_reconnection(
        self, p, sub_type, unsub_type, sub_func, unsub_func, keys
    ):

        for key in keys:
            assert await sub_func(key) is None

        # should be a message for each channel/pattern we just subscribed to
        for i, key in enumerate(keys):
            assert await wait_for_message(p) == make_message(sub_type, key, i + 1)

        # manually disconnect
        p.connection.disconnect()

        # calling get_message again reconnects and resubscribes
        # note, we may not re-subscribe to channels in exactly the same order
        # so we have to do some extra checks to make sure we got them all
        messages = []
        for i in range(len(keys)):
            messages.append(await wait_for_message(p))

        unique_channels = set()
        assert len(messages) == len(keys)
        for i, message in enumerate(messages):
            assert message["type"] == sub_type
            assert message["data"] == i + 1
            channel = message["channel"].decode("utf-8")
            unique_channels.add(channel)

        assert len(unique_channels) == len(keys)
        for channel in unique_channels:
            assert channel in keys
        await unsub_func()

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_resubscribe_to_channels_on_reconnection(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), "channel")
        await self._test_resubscribe_on_reconnection(**kwargs)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_resubscribe_to_patterns_on_reconnection(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), "pattern")
        await self._test_resubscribe_on_reconnection(**kwargs)

    async def _test_subscribed_property(
        self, p, sub_type, unsub_type, sub_func, unsub_func, keys
    ):

        assert p.subscribed is False
        await sub_func(keys[0])
        # we're now subscribed even though we haven't processed the
        # reply from the server just yet
        assert p.subscribed is True
        assert await wait_for_message(p) == make_message(sub_type, keys[0], 1)
        # we're still subscribed
        assert p.subscribed is True

        # unsubscribe from all channels
        await unsub_func()
        # we're still technically subscribed until we process the
        # response messages from the server
        assert p.subscribed is True
        assert await wait_for_message(p) == make_message(unsub_type, keys[0], 0)
        # now we're no longer subscribed as no more messages can be delivered
        # to any channels we were listening to
        assert p.subscribed is False

        # subscribing again flips the flag back
        await sub_func(keys[0])
        assert p.subscribed is True
        assert await wait_for_message(p) == make_message(sub_type, keys[0], 1)

        # unsubscribe again
        await unsub_func()
        assert p.subscribed is True
        # subscribe to another channel before reading the unsubscribe response
        await sub_func(keys[1])
        assert p.subscribed is True
        # read the unsubscribe for key1
        assert await wait_for_message(p) == make_message(unsub_type, keys[0], 0)
        # we're still subscribed to key2, so subscribed should still be True
        assert p.subscribed is True
        # read the key2 subscribe message
        assert await wait_for_message(p) == make_message(sub_type, keys[1], 1)
        await unsub_func()
        # haven't read the message yet, so we're still subscribed
        assert p.subscribed is True
        assert await wait_for_message(p) == make_message(unsub_type, keys[1], 0)
        # now we're finally unsubscribed
        assert p.subscribed is False
        await p.unsubscribe()

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_subscribe_property_with_channels(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), "channel")
        await self._test_subscribed_property(**kwargs)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_subscribe_property_with_patterns(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), "pattern")
        await self._test_subscribed_property(**kwargs)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_ignore_all_subscribe_messages(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)

        checks = (
            (p.subscribe, "foo"),
            (p.unsubscribe, "foo"),
            (p.psubscribe, "f*"),
            (p.punsubscribe, "f*"),
        )

        assert p.subscribed is False
        for func, channel in checks:
            assert await func(channel) is None
            assert p.subscribed is True
            assert await wait_for_message(p) is None
        assert p.subscribed is False

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_ignore_individual_subscribe_messages(self, r):
        p = r.pubsub()

        checks = (
            (p.subscribe, "foo"),
            (p.unsubscribe, "foo"),
            (p.psubscribe, "f*"),
            (p.punsubscribe, "f*"),
        )

        assert p.subscribed is False
        for func, channel in checks:
            assert await func(channel) is None
            assert p.subscribed is True
            message = await wait_for_message(p, ignore_subscribe_messages=True)
            assert message is None
        assert p.subscribed is False


class TestPubSubMessages:
    def setup_method(self, method):
        self.message = None

    def message_handler(self, message):
        self.message = message

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_published_message_to_channel(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe("foo")
        # if other tests failed, subscriber may not be cleared
        assert await r.publish("foo", "test message") >= 1

        message = await wait_for_message(p)
        assert isinstance(message, dict)
        assert message == make_message("message", "foo", "test message")
        await p.unsubscribe()

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_published_message_to_pattern(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe("foo")
        await p.psubscribe("f*")
        # 1 to pattern, 1 to channel
        assert await r.publish("foo", "test message") >= 2

        message1 = await wait_for_message(p)
        message2 = await wait_for_message(p)
        assert isinstance(message1, dict)
        assert isinstance(message2, dict)

        expected = [
            make_message("message", "foo", "test message"),
            make_message("pmessage", "foo", "test message", pattern="f*"),
        ]

        assert message1 in expected
        assert message2 in expected
        assert message1 != message2
        await p.unsubscribe("foo")

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_published_pickled_obj_to_channel(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe("foo")
        msg = pickle.dumps(Exception())
        # if other tests failed, subscriber may not be cleared
        assert await r.publish("foo", msg) >= 1

        message = await wait_for_message(p)
        assert isinstance(message, dict)
        assert message == make_message("message", "foo", msg)
        await p.unsubscribe()

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_published_pickled_obj_to_pattern(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe("foo")
        await p.psubscribe("f*")
        # 1 to pattern, 1 to channel
        msg = pickle.dumps(Exception())
        assert await r.publish("foo", msg) >= 2

        message1 = await wait_for_message(p)
        message2 = await wait_for_message(p)
        assert isinstance(message1, dict)
        assert isinstance(message2, dict)

        expected = [
            make_message("message", "foo", msg),
            make_message("pmessage", "foo", msg, pattern="f*"),
        ]

        assert message1 in expected
        assert message2 in expected
        assert message1 != message2
        await p.unsubscribe("foo")

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_channel_message_handler(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe(foo=self.message_handler)
        assert await r.publish("foo", "test message")
        assert await wait_for_message(p) is None
        assert self.message == make_message("message", "foo", "test message")
        await p.unsubscribe("foo")

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pattern_message_handler(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.psubscribe(**{"f*": self.message_handler})
        assert await r.publish("foo", "test message")
        assert await wait_for_message(p) is None
        assert self.message == make_message(
            "pmessage", "foo", "test message", pattern="f*"
        )
        await p.unsubscribe("foo")

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_unicode_channel_message_handler(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        channel = "uni" + chr(56) + "code"
        channels = {channel: self.message_handler}
        await p.subscribe(**channels)
        assert await r.publish(channel, "test message") == 1
        assert await wait_for_message(p) is None
        assert self.message == make_message("message", channel, "test message")
        await p.unsubscribe(channel)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_unicode_pattern_message_handler(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        pattern = "uni" + chr(56) + "*"
        channel = "uni" + chr(56) + "code"
        await p.psubscribe(**{pattern: self.message_handler})
        assert await r.publish(channel, "test message") == 1
        assert await wait_for_message(p) is None
        assert self.message == make_message(
            "pmessage", channel, "test message", pattern=pattern
        )
        await p.unsubscribe(channel)
        await p.punsubscribe(pattern)

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_get_message_without_subscribe(self, r):
        p = r.pubsub()
        with pytest.raises(RuntimeError) as info:
            await p.get_message()
        expect = (
            "connection not set: " "did you forget to call subscribe() or psubscribe()?"
        )
        assert expect in info.exconly()
        await p.unsubscribe()


# class TestPubSubAutoDecoding:
#     "These tests only validate that we get unicode values back"
#
#     channel = 'uni' + chr(56) + 'code'
#     pattern = 'uni' + chr(56) + '*'
#     data = 'abc' + chr(58) + '123'
#
#     def make_message(self, type, channel, data, pattern=None):
#         return {
#             'type': type,
#             'channel': channel,
#             'pattern': pattern,
#             'data': data
#         }
#
#     def setup_method(self, method):
#         self.message = None
#
#     def message_handler(self, message):
#         self.message = message
#
#     @pytest.fixture()
#     def r(self, request):
#         return _redis_client(request=request, decode_responses=True)
#
#     def test_channel_subscribe_unsubscribe(self, r):
#         p = r.pubsub()
#         p.subscribe(self.channel)
#         assert wait_for_message(p) == self.make_message('subscribe',
#                                                         self.channel, 1)
#
#         p.unsubscribe(self.channel)
#         assert wait_for_message(p) == self.make_message('unsubscribe',
#                                                         self.channel, 0)
#
#     def test_pattern_subscribe_unsubscribe(self, r):
#         p = r.pubsub()
#         p.psubscribe(self.pattern)
#         assert wait_for_message(p) == self.make_message('psubscribe',
#                                                         self.pattern, 1)
#
#         p.punsubscribe(self.pattern)
#         assert wait_for_message(p) == self.make_message('punsubscribe',
#                                                         self.pattern, 0)
#
#     def test_channel_publish(self, r):
#         p = r.pubsub(ignore_subscribe_messages=True)
#         p.subscribe(self.channel)
#         r.publish(self.channel, self.data)
#         assert wait_for_message(p) == self.make_message('message',
#                                                         self.channel,
#                                                         self.data)
#
#     def test_pattern_publish(self, r):
#         p = r.pubsub(ignore_subscribe_messages=True)
#         p.psubscribe(self.pattern)
#         r.publish(self.channel, self.data)
#         assert wait_for_message(p) == self.make_message('pmessage',
#                                                         self.channel,
#                                                         self.data,
#                                                         pattern=self.pattern)
#
#     def test_channel_message_handler(self, r):
#         p = r.pubsub(ignore_subscribe_messages=True)
#         p.subscribe(**{self.channel: self.message_handler})
#         r.publish(self.channel, self.data)
#         assert wait_for_message(p) is None
#         assert self.message == self.make_message('message', self.channel,
#                                                  self.data)
#
#         # test that we reconnected to the correct channel
#         p.connection.disconnect()
#         assert wait_for_message(p) is None  # should reconnect
#         new_data = self.data + 'new data'
#         r.publish(self.channel, new_data)
#         assert wait_for_message(p) is None
#         assert self.message == self.make_message('message', self.channel,
#                                                  new_data)
#
#     def test_pattern_message_handler(self, r):
#         p = r.pubsub(ignore_subscribe_messages=True)
#         p.psubscribe(**{self.pattern: self.message_handler})
#         r.publish(self.channel, self.data)
#         assert wait_for_message(p) is None
#         assert self.message == self.make_message('pmessage', self.channel,
#                                                  self.data,
#                                                  pattern=self.pattern)
#
#         # test that we reconnected to the correct pattern
#         p.connection.disconnect()
#         assert wait_for_message(p) is None  # should reconnect
#         new_data = self.data + 'new data'
#         r.publish(self.channel, new_data)
#         assert wait_for_message(p) is None
#         assert self.message == self.make_message('pmessage', self.channel,
#                                                  new_data,
#                                                  pattern=self.pattern)
#
#
class TestPubSubRedisDown:
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_channel_subscribe(self, r):
        r = coredis.StrictRedis(host="localhost", port=6390)
        p = r.pubsub()
        with pytest.raises(ConnectionError):
            await p.subscribe("foo")


class TestPubSubPubSubSubcommands:
    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pubsub_channels(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.subscribe("foo", "bar", "baz", "quux")
        channels = sorted(await r.pubsub_channels())
        assert channels == [b("bar"), b("baz"), b("foo"), b("quux")]
        await p.unsubscribe()

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pubsub_numsub(self, r):
        p1 = r.pubsub(ignore_subscribe_messages=True)
        await p1.subscribe("foo", "bar", "baz")
        p2 = r.pubsub(ignore_subscribe_messages=True)
        await p2.subscribe("bar", "baz")
        p3 = r.pubsub(ignore_subscribe_messages=True)
        await p3.subscribe("baz")

        channels = [(b("foo"), 1), (b("bar"), 2), (b("baz"), 3)]
        assert channels == await r.pubsub_numsub("foo", "bar", "baz")
        await p1.unsubscribe()
        await p2.unsubscribe()
        await p3.unsubscribe()

    @pytest.mark.asyncio(forbid_global_loop=True)
    async def test_pubsub_numpat(self, r):
        pubsub_count = await r.pubsub_numpat()
        p = r.pubsub(ignore_subscribe_messages=True)
        await p.psubscribe("*oo", "*ar", "b*z")
        assert await r.pubsub_numpat() == 3 + pubsub_count
