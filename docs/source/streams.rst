Streams
=======

Stream is a new feature provided by redis.

Since not all commands related are released officially(some commands are only referred in
`stream introduction <https://redis.io/topics/streams-intro>`_
), **you should make sure you know about
it before using the api, and the API may be changed in the future.**

For now, according to `command manual <https://redis.io/commands#stream>`_
, only `XADD`, `XRANGE`, `XREVRANGE`, `XLEN`,
`XREAD`, `XREADGROUP`, `XPENDING` commands are released. But commands you can find in
`stream introduction <https://redis.io/topics/streams-intro>`_
are all supported in aredis,
you can try the new feature with it.


You can append entries to stream like code below:

.. code-block:: python

    >>> entry = dict(event=1, user='usr1')
    >>> async def append_msg_to_stream(client, entry):
    >>>     stream_id = await client.xadd('example_stream', entry, max_len=10)
    >>>     return stream_id

**notice**
- max length of the stream length will not be limited max_len is set to None
- max_len should be int greater than 0, if set to 0 or negative, the stream length will not be limited
- The `XADD` command will auto-generate a unique id for you if the id argument specified is the '*' character.

You can use use read entries from a stream using `XRANGE` & `XREVRANGE`

.. code-block:: python

    >>> async def fetch_entries(client, stream, count=10, reverse=False):
    >>>     # if you do know the range of stream_id, you can specify it when using xrange
    >>>     if reverse:
    >>>         entries = await client.xrevrange(stream, start='10-0', end='1-0', count=count)
    >>>     else:
    >>>         entries = await client.xrange(stream, start='1-0', end='10-0', count=count)
    >>>     return entries

Actually, stream feature is inspired by `kafka <http://kafka.apache.org/>`_, a stream can be consumed by `consumer`
from a `group`, like code below:

.. code-block:: python

    >>> async def consuming_process(client):
    >>>     # create a stream firstly
    >>>     for idx in range(20):
    >>>         # give progressive stream id when create entry
    >>>         await client.xadd('test_stream', {'k1': 'v1', 'k2': 1}, stream_id=idx)
    >>>     # now create a consumer group
    >>>     # stream_id can be specified when creating a group,
    >>>     # if given '0', group will consume the stream from the beginning
    >>>     # if give '$', group will only consume newly appended entries
    >>>     await r.xgroup_create('test_stream', 'test_group', '0')
    >>>     # now consume the entries by 'consumer1' from group 'test_group'
    >>>     entries = await r.xreadgroup('test_group', 'consumer1', count=5, test_stream='1')
