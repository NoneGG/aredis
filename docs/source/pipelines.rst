         Pipelines
^^^^^^^^^

Pipelines are a subclass of the base Redis class that provide support for
buffering multiple commands to the server in a single request. They can be used
to dramatically increase the performance of groups of commands by reducing the
number of back-and-forth TCP packets between the client and server.

Pipelines are quite simple to use:

.. code-block:: python

    >>> async def example(client):
    >>>     async with await client.pipeline(transaction=True) as pipe:
    >>>     # will return self to send another command
    >>>     pipe = await (await pipe.flushdb()).set('foo', 'bar')
    >>>     # can also directly send command
    >>>     await pipe.set('bar', 'foo')
    >>>     # commands will be buffered
    >>>     await pipe.keys('*')
    >>>     res = await pipe.execute()
    >>>     # results should be in order corresponding to your command
    >>>     assert res == [True, True, True, [b'bar', b'foo']]

For ease of use, all commands being buffered into the pipeline return the
pipeline object itself. Which enable you to use it like the example provided.

In addition, pipelines can also ensure the buffered commands are executed
atomically as a group. This happens by default. If you want to disable the
atomic nature of a pipeline but still want to buffer commands, you can turn
off transactions.

.. code-block:: python

    >>> pipe = r.pipeline(transaction=False)

A common issue occurs when requiring atomic transactions but needing to
retrieve values in Redis prior for use within the transaction. For instance,
let's assume that the INCR command didn't exist and we need to build an atomic
version of INCR in Python.

The completely naive implementation could GET the value, increment it in
Python, and SET the new value back. However, this is not atomic because
multiple clients could be doing this at the same time, each getting the same
value from GET.

Enter the WATCH command. WATCH provides the ability to monitor one or more keys
prior to starting a transaction. If any of those keys change prior the
execution of that transaction, the entire transaction will be canceled and a
WatchError will be raised. To implement our own client-side INCR command, we
could do something like this:

.. code-block:: python

    >>> async def example():
    >>>     async with await r.pipeline() as pipe:
    ...         while 1:
    ...             try:
    ...                 # put a WATCH on the key that holds our sequence value
    ...                 await pipe.watch('OUR-SEQUENCE-KEY')
    ...                 # after WATCHing, the pipeline is put into immediate execution
    ...                 # mode until we tell it to start buffering commands again.
    ...                 # this allows us to get the current value of our sequence
    ...                 current_value = await pipe.get('OUR-SEQUENCE-KEY')
    ...                 next_value = int(current_value) + 1
    ...                 # now we can put the pipeline back into buffered mode with MULTI
    ...                 pipe.multi()
    ...                 pipe.set('OUR-SEQUENCE-KEY', next_value)
    ...                 # and finally, execute the pipeline (the set command)
    ...                 await pipe.execute()
    ...                 # if a WatchError wasn't raised during execution, everything
    ...                 # we just did happened atomically.
    ...                 break
    ...             except WatchError:
    ...                 # another client must have changed 'OUR-SEQUENCE-KEY' between
    ...                 # the time we started WATCHing it and the pipeline's execution.
    ...                 # our best bet is to just retry.
    ...                 continue

Note that, because the Pipeline must bind to a single connection for the
duration of a WATCH, care must be taken to ensure that the connection is
returned to the connection pool by calling the reset() method. If the
Pipeline is used as a context manager (as in the example above) reset()
will be called automatically. Of course you can do this the manual way by
explicitly calling reset():

.. code-block:: python

    >>> async def example():
    >>>     async with await r.pipeline() as pipe:
    >>>         while 1:
    ...             try:
    ...                 await pipe.watch('OUR-SEQUENCE-KEY')
    ...                 ...
    ...                 await pipe.execute()
    ...                 break
    ...             except WatchError:
    ...                 continue
    ...             finally:
    ...                 await pipe.reset()

A convenience method named "transaction" exists for handling all the
boilerplate of handling and retrying watch errors. It takes a callable that
should expect a single parameter, a pipeline object, and any number of keys to
be WATCHed. Our client-side INCR command above can be written like this,
which is much easier to read:

.. code-block:: python

    >>> async def client_side_incr(pipe):
    ...     current_value = await pipe.get('OUR-SEQUENCE-KEY')
    ...     next_value = int(current_value) + 1
    ...     pipe.multi()
    ...     await pipe.set('OUR-SEQUENCE-KEY', next_value)
    >>>
    >>> await r.transaction(client_side_incr, 'OUR-SEQUENCE-KEY')
    [True]