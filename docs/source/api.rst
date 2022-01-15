API Documentation
=================
.. currentmodule:: coredis

Clients
^^^^^^^
.. autoclass::
   StrictRedis

.. autoclass::
   StrictRedisCluster

.. currentmodule:: coredis.sentinel

.. autoclass::
   Sentinel

Connection Classes
^^^^^^^^^^^^^^^^^^
.. currentmodule:: coredis
.. autoclass:: Connection
.. autoclass:: UnixDomainSocketConnection
.. autoclass:: ClusterConnection
.. autoclass:: ConnectionPool
.. autoclass:: ClusterConnectionPool

.. currentmodule:: coredis.sentinel
.. autoclass:: SentinelConnectionPool

Utility Classes
^^^^^^^^^^^^^^^

.. currentmodule:: coredis

.. autoclass::
   BitFieldOperation

Exceptions
^^^^^^^^^^

.. currentmodule:: coredis

.. autoexception:: AskError
   :no-inherited-members:
.. autoexception:: BusyLoadingError
   :no-inherited-members:
.. autoexception:: CacheError
   :no-inherited-members:
.. autoexception:: ClusterCrossSlotError
   :no-inherited-members:
.. autoexception:: ClusterDownError
   :no-inherited-members:
.. autoexception:: ClusterError
   :no-inherited-members:
.. autoexception:: ClusterTransactionError
   :no-inherited-members:
.. autoexception:: CompressError
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
.. autoexception:: MovedError
   :no-inherited-members:
.. autoexception:: NoScriptError
   :no-inherited-members:
.. autoexception:: PubSubError
   :no-inherited-members:
.. autoexception:: ReadOnlyError
   :no-inherited-members:
.. autoexception:: RedisClusterException
   :no-inherited-members:
.. autoexception:: RedisError
   :no-inherited-members:
.. autoexception:: ResponseError
   :no-inherited-members:
.. autoexception:: SerializeError
   :no-inherited-members:
.. autoexception:: TimeoutError
   :no-inherited-members:
.. autoexception:: TryAgainError
   :no-inherited-members:
.. autoexception:: WatchError
   :no-inherited-members:
