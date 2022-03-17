API Documentation
=================
.. currentmodule:: coredis

Clients
^^^^^^^
Redis
-----
.. autoclass::
   Redis

Cluster
-------
.. autoclass::
   RedisCluster


Sentinel
--------
.. currentmodule:: coredis.sentinel
.. autoclass::
   Sentinel

Connection Classes
^^^^^^^^^^^^^^^^^^
.. currentmodule:: coredis
.. autoclass:: Connection
.. autoclass:: UnixDomainSocketConnection
.. autoclass:: ClusterConnection

Connection Pools
^^^^^^^^^^^^^^^^
.. autoclass:: ConnectionPool
.. autoclass:: BlockingConnectionPool

Cluster
-------
.. autoclass:: ClusterConnectionPool

.. currentmodule:: coredis.sentinel
.. autoclass:: SentinelConnectionPool

Command Builders
^^^^^^^^^^^^^^^^

BitField Operations
-------------------

.. autoclass:: coredis.commands.builders.bitfield.BitFieldOperation
   :no-inherited-members:

PubSub
------
.. autoclass:: coredis.commands.builders.pubsub.PubSub
   :no-inherited-members:

Scripting
---------
.. autoclass:: coredis.commands.builders.script.Script
   :no-inherited-members:

Transactions
------------

.. autoclass:: coredis.commands.builders.pipeline.Pipeline
   :no-inherited-members:

.. autoclass:: coredis.commands.builders.pipeline.ClusterPipeline
   :no-inherited-members:


Response Types
^^^^^^^^^^^^^^
.. automodule:: coredis.response.types
   :no-inherited-members:
   :undoc-members:

Utility Classes
^^^^^^^^^^^^^^^

.. currentmodule:: coredis

.. autoclass::
   NodeFlag
.. autoclass::
   PureToken

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
