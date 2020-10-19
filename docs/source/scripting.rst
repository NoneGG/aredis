LUA Scripting
=============

aredis supports the EVAL, EVALSHA, and SCRIPT commands. However, there are
a number of edge cases that make these commands tedious to use in real world
scenarios. Therefore, aredis exposes a Script object that makes scripting
much easier to use.

To create a Script instance, use the `register_script` function on a client
instance passing the LUA code as the first argument. `register_script` returns
a Script instance that you can use throughout your code.

The following trivial LUA script accepts two parameters: the name of a key and
a multiplier value. The script fetches the value stored in the key, multiplies
it with the multiplier value and returns the result.

.. code-block:: pycon

    r = redis.StrictRedis()
    lua = """
    local value = redis.call('GET', KEYS[1])
    value = tonumber(value)
    return value * ARGV[1]"""
    multiply = r.register_script(lua)

`multiply` is now a Script instance that is invoked by calling it like a
function. Script instances accept the following optional arguments:

* **keys**: A list of key names that the script will access. This becomes the
  KEYS list in LUA.
* **args**: A list of argument values. This becomes the ARGV list in LUA.
* **client**: A aredis Client or Pipeline instance that will invoke the
  script. If client isn't specified, the client that intiially
  created the Script instance (the one that `register_script` was
  invoked from) will be used.

Notice that the `Srcipt.__call__` is no longer useful(`async/await` can't be used in magic method),
please use `Script.register` instead

Continuing the example from above:

.. code-block:: python

    await r.set('foo', 2)
    await multiply.execute(keys=['foo'], args=[5])
    # 10

The value of key 'foo' is set to 2. When multiply is invoked, the 'foo' key is
passed to the script along with the multiplier value of 5. LUA executes the
script and returns the result, 10.

Script instances can be executed using a different client instance, even one
that points to a completely different Redis server.

.. code-block:: python

    r2 = redis.StrictRedis('redis2.example.com')
    await r2.set('foo', 3)
    multiply.execute(keys=['foo'], args=[5], client=r2)
    # 15

The Script object ensures that the LUA script is loaded into Redis's script
cache. In the event of a NOSCRIPT error, it will load the script and retry
executing it.

Script objects can also be used in pipelines. The pipeline instance should be
passed as the client argument when calling the script. Care is taken to ensure
that the script is registered in Redis's script cache just prior to pipeline
execution.

.. code-block:: python

    pipe = await r.pipeline()
    await pipe.set('foo', 5)
    await multiply(keys=['foo'], args=[5], client=pipe)
    await pipe.execute()
    # [True, 25]
