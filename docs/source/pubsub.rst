Publish / Subscribe
===================

aredis includes a `PubSub` object that subscribes to channels and listens
for new messages. Creating a `PubSub` object is easy.

.. code-block:: python

    >>> r = redis.StrictRedis(...)
    >>> p = r.pubsub()

Once a `PubSub` instance is created, channels and patterns can be subscribed
to.

.. code-block:: python

    >>> await p.subscribe('my-first-channel', 'my-second-channel', ...)
    >>> await p.psubscribe('my-*', ...)

The `PubSub` instance is now subscribed to those channels/patterns. The
subscription confirmations can be seen by reading messages from the `PubSub`
instance.

.. code-block:: python

    >>> await p.get_message()
    {'pattern': None, 'type': 'subscribe', 'channel': 'my-second-channel', 'data': 1L}
    >>> await p.get_message()
    {'pattern': None, 'type': 'subscribe', 'channel': 'my-first-channel', 'data': 2L}
    >>> await p.get_message()
    {'pattern': None, 'type': 'psubscribe', 'channel': 'my-*', 'data': 3L}

Every message read from a `PubSub` instance will be a dictionary with the
following keys.

* **type**: One of the following: 'subscribe', 'unsubscribe', 'psubscribe',
  'punsubscribe', 'message', 'pmessage'
* **channel**: The channel [un]subscribed to or the channel a message was
  published to
* **pattern**: The pattern that matched a published message's channel. Will be
  `None` in all cases except for 'pmessage' types.
* **data**: The message data. With [un]subscribe messages, this value will be
  the number of channels and patterns the connection is currently subscribed
  to. With [p]message messages, this value will be the actual published
  message.

Let's send a message now.

.. code-block:: python

    # the publish method returns the number matching channel and pattern
    # subscriptions. 'my-first-channel' matches both the 'my-first-channel'
    # subscription and the 'my-*' pattern subscription, so this message will
    # be delivered to 2 channels/patterns
    >>> await r.publish('my-first-channel', 'some data')
    2
    >>> await p.get_message()
    {'channel': 'my-first-channel', 'data': 'some data', 'pattern': None, 'type': 'message'}
    >>> await p.get_message()
    {'channel': 'my-first-channel', 'data': 'some data', 'pattern': 'my-*', 'type': 'pmessage'}

Unsubscribing works just like subscribing. If no arguments are passed to
[p]unsubscribe, all channels or patterns will be unsubscribed from.

.. code-block:: python

    >>> await p.unsubscribe()
    >>> await p.punsubscribe('my-*')
    >>> await p.get_message()
    {'channel': 'my-second-channel', 'data': 2L, 'pattern': None, 'type': 'unsubscribe'}
    >>> await p.get_message()
    {'channel': 'my-first-channel', 'data': 1L, 'pattern': None, 'type': 'unsubscribe'}
    >>> await p.get_message()
    {'channel': 'my-*', 'data': 0L, 'pattern': None, 'type': 'punsubscribe'}

aredis also allows you to register callback functions to handle published
messages. Message handlers take a single argument, the message, which is a
dictionary just like the examples above. To subscribe to a channel or pattern
with a message handler, pass the channel or pattern name as a keyword argument
with its value being the callback function.

When a message is read on a channel or pattern with a message handler, the
message dictionary is created and passed to the message handler. In this case,
a `None` value is returned from get_message() since the message was already
handled.

.. code-block:: python

    >>> def my_handler(message):
    ...     print('MY HANDLER: ', message['data'])
    >>> await p.subscribe(**{'my-channel': my_handler})
    # read the subscribe confirmation message
    >>> await p.get_message()
    {'pattern': None, 'type': 'subscribe', 'channel': 'my-channel', 'data': 1L}
    >>> await r.publish('my-channel', 'awesome data')
    1
    # for the message handler to work, we need tell the instance to read data.
    # this can be done in several ways (read more below). we'll just use
    # the familiar get_message() function for now
    >>> await message = p.get_message()
    MY HANDLER:  awesome data
    # note here that the my_handler callback printed the string above.
    # `message` is None because the message was handled by our handler.
    >>> print(message)
    None

If your application is not interested in the (sometimes noisy)
subscribe/unsubscribe confirmation messages, you can ignore them by passing
`ignore_subscribe_messages=True` to `r.pubsub()`. This will cause all
subscribe/unsubscribe messages to be read, but they won't bubble up to your
application.

.. code-block:: python

    >>> p = r.pubsub(ignore_subscribe_messages=True)
    >>> await p.subscribe('my-channel')
    >>> await p.get_message()  # hides the subscribe message and returns None
    >>> await r.publish('my-channel')
    1
    >>> await p.get_message()
    {'channel': 'my-channel', 'data': 'my data', 'pattern': None, 'type': 'message'}

There are three different strategies for reading messages.

The examples above have been using `pubsub.get_message()`.
If there's data available to be read, `get_message()` will
read it, format the message and return it or pass it to a message handler. If
there's no data to be read, `get_message()` will return None after the configured `timeout`
(`timeout` should set to value larger than 0 or it will be ignore).
This makes it trivial to integrate into an existing event loop inside your application.

.. code-block:: python

    >>> while True:
    >>>     message = await p.get_message()
    >>>     if message:
    >>>         # do something with the message
    >>>     await asyncio.sleep(0.001)  # be nice to the system :)

Older versions of aredis only read messages with `pubsub.listen()`. listen()
is a generator that blocks until a message is available. If your application
doesn't need to do anything else but receive and act on messages received from
redis, listen() is an easy way to get up an running.

.. code-block:: python

    >>> for message in await p.listen():
    ...     # do something with the message

The third option runs an event loop in a separate thread.
`pubsub.run_in_thread()` creates a new thread and use the event loop in main thread.
The thread object is returned to the caller of `run_in_thread()`. The caller can
use the `thread.stop()` method to shut down the event loop and thread. Behind
the scenes, this is simply a wrapper around `get_message()` that runs in a
separate thread, and use `asyncio.run_coroutine_threadsafe()` to run coroutines.

Note: Since we're running in a separate thread, there's no way to handle
messages that aren't automatically handled with registered message handlers.
Therefore, aredis prevents you from calling `run_in_thread()` if you're
subscribed to patterns or channels that don't have message handlers attached.

.. code-block:: python

    >>> await p.subscribe(**{'my-channel': my_handler})
    >>> thread = p.run_in_thread(sleep_time=0.001)
    # the event loop is now running in the background processing messages
    # when it's time to shut it down...
    >>> thread.stop()

PubSub objects remember what channels and patterns they are subscribed to. In
the event of a disconnection such as a network error or timeout, the
PubSub object will re-subscribe to all prior channels and patterns when
reconnecting. Messages that were published while the client was disconnected
cannot be delivered. When you're finished with a PubSub object, call its
`.close()` method to shutdown the connection.

.. code-block:: python

    >>> p = r.pubsub()
    >>> ...
    >>> p.close()

The PUBSUB set of subcommands CHANNELS, NUMSUB and NUMPAT are also
supported:

.. code-block:: pycon

    >>> await r.pubsub_channels()
    ['foo', 'bar']
    >>> await r.pubsub_numsub('foo', 'bar')
    [('foo', 9001), ('bar', 42)]
    >>> await r.pubsub_numsub('baz')
    [('baz', 0)]
    >>> await r.pubsub_numpat()
    1204
