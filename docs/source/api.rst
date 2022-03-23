API Documentation
=================
.. currentmodule:: coredis

Clients
^^^^^^^
Redis
-----
.. autoclass:: Redis
   :class-doc-from: both

Cluster
-------
.. autoclass:: RedisCluster
   :class-doc-from: both


Sentinel
--------
.. currentmodule:: coredis.sentinel
.. autoclass:: Sentinel
   :class-doc-from: both

Connection Classes
^^^^^^^^^^^^^^^^^^
.. currentmodule:: coredis
.. autoclass:: Connection
   :class-doc-from: both
.. autoclass:: UnixDomainSocketConnection
   :class-doc-from: both
.. autoclass:: ClusterConnection
   :class-doc-from: both

Connection Pools
^^^^^^^^^^^^^^^^
.. autoclass:: ConnectionPool
   :class-doc-from: both
.. autoclass:: BlockingConnectionPool
   :class-doc-from: both

Cluster
-------
.. autoclass:: ClusterConnectionPool
   :class-doc-from: both

.. currentmodule:: coredis.sentinel
.. autoclass:: SentinelConnectionPool
   :class-doc-from: both

Command Builders
^^^^^^^^^^^^^^^^

BitField Operations
-------------------

.. autoclass:: coredis.commands.bitfield.BitFieldOperation
   :no-inherited-members:
   :class-doc-from: both

PubSub
------
.. autoclass:: coredis.commands.pubsub.PubSub
   :no-inherited-members:
   :class-doc-from: both

Scripting
---------
.. autoclass:: coredis.commands.script.Script
   :no-inherited-members:
   :class-doc-from: both

Functions
---------
.. autoclass:: coredis.commands.function.Library
   :class-doc-from: both

.. autoclass:: coredis.commands.function.Function
   :class-doc-from: both

Transactions
------------

.. autoclass:: coredis.commands.pipeline.Pipeline
   :no-inherited-members:
   :class-doc-from: both

.. autoclass:: coredis.commands.pipeline.ClusterPipeline
   :no-inherited-members:
   :class-doc-from: both

Monitor
-------
.. autoclass:: coredis.commands.monitor.Monitor


Response Types
^^^^^^^^^^^^^^
.. automodule:: coredis.response.types
   :no-inherited-members:
   :show-inheritance:


Utility Classes
^^^^^^^^^^^^^^^

.. currentmodule:: coredis

.. autoclass:: NodeFlag
   :no-inherited-members:
   :show-inheritance:
.. autoclass:: PureToken
   :no-inherited-members:
   :show-inheritance:
.. autoclass:: coredis.commands.pubsub.PubSubWorkerThread
   :no-inherited-members:
   :show-inheritance:
.. autoclass:: coredis.commands.monitor.MonitorThread
   :no-inherited-members:
   :show-inheritance:

Exceptions
^^^^^^^^^^

.. currentmodule:: coredis

Authentication & Authorization
------------------------------

.. autoexception:: AuthenticationFailureError
   :no-inherited-members:
.. autoexception:: AuthenticationRequiredError
   :no-inherited-members:
.. autoexception:: AuthorizationError
   :no-inherited-members:

Cluster
-------
.. autoexception:: AskError
   :no-inherited-members:
.. autoexception:: ClusterCrossSlotError
   :no-inherited-members:
.. autoexception:: ClusterDownError
   :no-inherited-members:
.. autoexception:: ClusterError
   :no-inherited-members:
.. autoexception:: ClusterTransactionError
   :no-inherited-members:
.. autoexception:: MovedError
   :no-inherited-members:
.. autoexception:: RedisClusterException
   :no-inherited-members:

General Exceptions
-------------------
.. autoexception:: BusyLoadingError
   :no-inherited-members:
.. autoexception:: CommandSyntaxError
   :no-inherited-members:
.. autoexception:: ConnectionError
   :no-inherited-members:
.. autoexception:: DataError
   :no-inherited-members:
.. autoexception:: ExecAbortError
   :no-inherited-members:
.. autoexception:: InvalidResponse
   :no-inherited-members:
.. autoexception:: LockError
   :no-inherited-members:
.. autoexception:: NoKeyError
   :no-inherited-members:
.. autoexception:: NoScriptError
   :no-inherited-members:
.. autoexception:: PubSubError
   :no-inherited-members:
.. autoexception:: ReadOnlyError
   :no-inherited-members:
.. autoexception:: RedisError
   :no-inherited-members:
.. autoexception:: ResponseError
   :no-inherited-members:
.. autoexception:: TimeoutError
   :no-inherited-members:
.. autoexception:: TryAgainError
   :no-inherited-members:
.. autoexception:: WatchError
   :no-inherited-members:
