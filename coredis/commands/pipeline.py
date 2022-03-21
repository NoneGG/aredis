import functools
import inspect
import sys
from abc import ABCMeta
from concurrent.futures import CancelledError
from dataclasses import dataclass, field
from itertools import chain
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    TypeVar,
)

from coredis.client import AbstractRedis, AbstractRedisCluster, ResponseParser
from coredis.exceptions import (
    AskError,
    ClusterTransactionError,
    ConnectionError,
    ExecAbortError,
    MovedError,
    RedisClusterException,
    RedisError,
    ResponseError,
    TimeoutError,
    TryAgainError,
    WatchError,
)
from coredis.pool import ClusterConnectionPool
from coredis.typing import KeyT, ParamSpec, ValueT
from coredis.utils import NodeFlag, clusterdown_wrapper, dict_merge

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")

ERRORS_ALLOW_RETRY = (
    ConnectionError,
    TimeoutError,
    MovedError,
    AskError,
    TryAgainError,
)


def block_pipeline_command(
    func: Callable[P, Awaitable[R]]
) -> Callable[P, Awaitable[R]]:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        raise RedisClusterException(
            (
                f"ERROR: Calling pipelined function {func.__name__}"
                " is blocked when running redis in cluster mode."
            )
        )

    wrapper.__doc__ = f"""{wrapper.__doc__}

:meta private:
    """

    return wrapper


def wrap_pipeline_method(
    kls: "PipelineMeta", func: Callable[P, Awaitable]
) -> Callable[P, Awaitable]:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs):
        return await func(*args, **kwargs)

    wrapper.__annotations__ = wrapper.__annotations__.copy()
    wrapper.__annotations__["return"] = kls
    wrapper.__doc__ = f"""Pipeline variant that does not execute immediately
and instead returns the instance of :class:`{kls.__name__}` itself.

To fetch the return values call :meth:`{kls.__name__}.execute` to fetch responses for all commands
executed in the pipeline.

{wrapper.__doc__}
    """
    return wrapper


@dataclass
class PipelineCommand:
    args: Tuple[Any, ...]
    options: Dict[Any, Any] = field(default_factory=dict)


@dataclass
class ClusterPipelineCommand(PipelineCommand):
    position: int = 0
    result: Optional[Any] = None
    node: Optional[Any] = None
    asking: bool = False


class NodeCommands:
    def __init__(self, parse_response, connection, in_transaction=False):
        self.parse_response = parse_response
        self.connection = connection
        self.commands = []
        self.in_transaction = in_transaction

    def extend(self, c):
        self.commands.extend(c)

    def append(self, c):
        self.commands.append(c)

    async def write(self):
        """NOTE: Code was borrowed from Redis so it can be fixed"""
        connection = self.connection
        commands = self.commands

        # We are going to clobber the commands with the write, so go ahead
        # and ensure that nothing is sitting there from a previous run.

        for c in commands:
            c.result = None

        # build up all commands into a single request to increase network perf
        # send all the commands and catch connection and timeout errors.
        try:
            await connection.send_packed_command(
                connection.pack_commands([c.args for c in commands])
            )
        except (ConnectionError, TimeoutError) as e:
            for c in commands:
                c.result = e

    async def read(self):
        connection = self.connection

        for c in self.commands:

            # if there is a result on this command, it means we ran into an exception
            # like a connection error. Trying to parse a response on a connection that
            # is no longer open will result in a connection error raised by redis-py.
            # but redis-py doesn't check in parse_response that the sock object is
            # still set and if you try to read from a closed connection, it will
            # result in an AttributeError because it will do a readline() call on None.
            # This can have all kinds of nasty side-effects.
            # Treating this case as a connection error is fine because it will dump
            # the connection object back into the pool and on the next write, it will
            # explicitly open the connection and all will be well.

            if c.result is None:
                try:
                    if self.in_transaction:
                        cmd = "_"
                    else:
                        cmd = c.args[0]
                    c.result = await self.parse_response(connection, cmd, **c.options)

                except ExecAbortError:
                    raise
                except (ConnectionError, TimeoutError) as e:
                    for c in self.commands:
                        c.result = e
                except RedisError:
                    c.result = sys.exc_info()[1]


class BasePipeline:
    """
    Pipelines provide a way to transmit multiple commands to the Redis server
    in one transmission.  This is convenient for batch processing, such as
    saving all the values in a list to Redis.

    All commands executed within a pipeline are wrapped with MULTI and EXEC
    calls. This guarantees all commands executed in the pipeline will be
    executed atomically.

    Any command raising an exception does *not* halt the execution of
    subsequent commands in the pipeline. Instead, the exception is caught
    and its instance is placed into the response list returned by execute().
    Code iterating over the response list should be able to deal with an
    instance of an exception as a potential value. In general, these will be
    ResponseError exceptions, such as those raised when issuing a command
    on a key of a different datatype.
    """

    command_stack: List[PipelineCommand]
    UNWATCH_COMMANDS = {"DISCARD", "EXEC", "UNWATCH"}

    def __init__(self, connection_pool, response_callbacks, transaction):
        self.connection_pool = connection_pool
        self.connection = None
        self.response_callbacks = response_callbacks
        self._transaction = transaction
        self.watching = False
        self.command_stack = []

    async def __aenter__(self) -> "BasePipeline":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.reset()

    def __len__(self):
        return len(self.command_stack)

    async def reset(self):
        self.command_stack.clear()
        self.scripts = set()
        # make sure to reset the connection state in the event that we were
        # watching something

        if self.watching and self.connection:
            try:
                # call this manually since our unwatch or
                # immediate_execute_command methods can call reset()
                await self.connection.send_command("UNWATCH")
                await self.connection.read_response()
            except ConnectionError:
                # disconnect will also remove any previous WATCHes
                self.connection.disconnect()
        # clean up the other instance attributes
        self.watching = False
        self.explicit_transaction = False
        # we can safely return the connection to the pool here since we're
        # sure we're no longer WATCHing anything

        if self.connection:
            self.connection_pool.release(self.connection)
            self.connection = None

    def multi(self):
        """
        Starts a transactional block of the pipeline after WATCH commands
        are issued. End the transactional block with `execute`.
        """

        if self.explicit_transaction:
            raise RedisError("Cannot issue nested calls to MULTI")

        if self.command_stack:
            raise RedisError(
                "Commands without an initial WATCH have already " "been issued"
            )
        self.explicit_transaction = True

    async def execute_command(self, *args, **kwargs) -> Any:
        if (self.watching or args[0] == "WATCH") and not self.explicit_transaction:
            return await self.immediate_execute_command(*args, **kwargs)

        return self.pipeline_execute_command(*args, **kwargs)

    async def immediate_execute_command(self, *args, **kwargs):
        """
        Executes a command immediately, but don't auto-retry on a
        ConnectionError if we're already WATCHing a variable. Used when
        issuing WATCH or subsequent commands retrieving their values but before
        MULTI is called.
        """
        command_name = args[0]
        conn = self.connection
        # if this is the first call, we need a connection

        if not conn:
            conn = await self.connection_pool.get_connection()
            self.connection = conn
        try:
            await conn.send_command(*args)

            return await self.parse_response(conn, command_name, **kwargs)
        except (ConnectionError, TimeoutError) as e:
            conn.disconnect()

            if not conn.retry_on_timeout and isinstance(e, TimeoutError):
                raise
            # if we're not already watching, we can safely retry the command
            try:
                if not self.watching:
                    await conn.send_command(*args)

                    return await self.parse_response(conn, command_name, **kwargs)
            except ConnectionError:
                # the retry failed so cleanup.
                conn.disconnect()
                await self.reset()
                raise

    def pipeline_execute_command(self, *args, **options):
        """
        Stages a command to be executed next execute() invocation

        Returns the current Pipeline object back so commands can be
        chained together, such as:

        pipe = pipe.set('foo', 'bar').incr('baz').decr('bang')

        At some other point, you can then run: pipe.execute(),
        which will execute all commands queued in the pipe.
        """
        self.command_stack.append(PipelineCommand(args=args, options=options))

        return self

    async def _execute_transaction(self, connection, commands, raise_on_error):

        cmds = chain(
            [PipelineCommand(args=("MULTI",))],
            commands,
            [PipelineCommand(args=("EXEC",))],
        )
        all_cmds = connection.pack_commands([cmd.args for cmd in cmds])
        await connection.send_packed_command(all_cmds)
        errors: List[Tuple[int, Optional[BaseException]]] = []

        # parse off the response for MULTI
        # NOTE: we need to handle ResponseErrors here and continue
        # so that we read all the additional command messages from
        # the socket
        try:
            await self.parse_response(connection, "_")
        except ResponseError:
            errors.append((0, sys.exc_info()[1]))

        # and all the other commands

        for i, cmd in enumerate(commands):
            try:
                await self.parse_response(connection, "_")
            except ResponseError:
                ex = sys.exc_info()[1]
                self.annotate_exception(ex, i + 1, cmd.args)
                errors.append((i, ex))

        # parse the EXEC.
        try:
            response = await self.parse_response(connection, "_")
        except ExecAbortError:
            if self.explicit_transaction:
                await self.immediate_execute_command("DISCARD")

            if errors and errors[0][1]:
                raise errors[0][1]
            raise

        if response is None:
            raise WatchError("Watched variable changed.")

        # put any parse errors into the response

        for i, e in errors:
            response.insert(i, e)

        if len(response) != len(commands):
            if self.connection:
                self.connection.disconnect()
            raise ResponseError(
                "Wrong number of response items from " "pipeline execution"
            )

        # find any errors in the response and raise if necessary

        if raise_on_error:
            self.raise_first_error(commands, response)

        # We have to run response callbacks manually
        data = []

        for r, cmd in zip(response, commands):
            if not isinstance(r, Exception):
                command_name = cmd.args[0]

                if command_name in self.response_callbacks:
                    callback = self.response_callbacks[command_name]
                    r = callback(r, **cmd.options)
                    # typing.Awaitable is not available in Python3.5
                    # so use inspect.isawaitable instead
                    # according to issue https://github.com/alisaifee/coredis/issues/77

                    if inspect.isawaitable(response):
                        r = await r

            data.append(r)

        return tuple(data)

    async def _execute_pipeline(self, connection, commands, raise_on_error):
        # build up all commands into a single request to increase network perf
        all_cmds = connection.pack_commands([cmd.args for cmd in commands])
        await connection.send_packed_command(all_cmds)

        response = []

        for cmd in commands:
            try:
                response.append(
                    await self.parse_response(connection, cmd.args[0], **cmd.options)
                )
            except ResponseError:
                response.append(sys.exc_info()[1])

        if raise_on_error:
            self.raise_first_error(commands, response)

        return tuple(response)

    def raise_first_error(self, commands, response):
        for i, r in enumerate(response):
            if isinstance(r, ResponseError):
                self.annotate_exception(r, i + 1, commands[i].args)
                raise r

    def annotate_exception(self, exception, number, command):
        cmd = str(" ").join(map(str, command))
        msg = str("Command # %d (%s) of pipeline caused error: %s") % (
            number,
            cmd,
            str(exception.args[0]),
        )
        exception.args = (msg,) + exception.args[1:]

    async def _parse(self, connection, command_name, **options):
        "Parses a response from the Redis server"
        response = await connection.read_response()
        if command_name in self.response_callbacks:
            callback = self.response_callbacks[command_name]

            return callback(response, **options)

        return response

    async def parse_response(self, connection, command_name, **options):
        result = await self._parse(connection, command_name, **options)

        if command_name in self.UNWATCH_COMMANDS:
            self.watching = False
        elif command_name == "WATCH":
            self.watching = True

        return result

    async def load_scripts(self):
        # make sure all scripts that are about to be run on this pipeline exist
        scripts = list(self.scripts)
        immediate = self.immediate_execute_command
        shas = [s.sha for s in scripts]
        # we can't use the normal script_* methods because they would just
        # get buffered in the pipeline.
        exists = await immediate("SCRIPT EXISTS", *shas)

        if not all(exists):
            for s, exist in zip(scripts, exists):
                if not exist:
                    s.sha = await immediate("SCRIPT LOAD", s.script)

    async def execute(self, raise_on_error=True) -> Any:
        """Executes all the commands in the current pipeline"""
        stack = self.command_stack

        if not stack:
            return []

        if self.scripts:
            await self.load_scripts()

        if self._transaction or self.explicit_transaction:
            exec = self._execute_transaction
        else:
            exec = self._execute_pipeline

        conn = self.connection

        if not conn:
            conn = await self.connection_pool.get_connection()
            # assign to self.connection so reset() releases the connection
            # back to the pool after we're done
            self.connection = conn

        try:
            return await exec(conn, stack, raise_on_error)
        except (ConnectionError, TimeoutError, CancelledError) as e:
            conn.disconnect()

            if not conn.retry_on_timeout and isinstance(e, TimeoutError):
                raise
            # if we were watching a variable, the watch is no longer valid
            # since this connection has died. raise a WatchError, which
            # indicates the user should retry his transaction. If this is more
            # than a temporary failure, the WATCH that the user next issues
            # will fail, propegating the real ConnectionError

            if self.watching:
                raise WatchError(
                    "A ConnectionError occured on while watching " "one or more keys"
                )
            # otherwise, it's safe to retry since the transaction isn't
            # predicated on any state

            return await exec(conn, stack, raise_on_error)
        finally:
            await self.reset()

    async def watch(self, *keys: ValueT) -> bool:
        """Watches the values at keys ``keys``"""

        if self.explicit_transaction:
            raise RedisError("Cannot issue a WATCH after a MULTI")

        return await self.execute_command("WATCH", *keys)

    async def unwatch(self) -> bool:
        """Unwatches all previously specified keys"""

        return self.watching and await self.execute_command("UNWATCH") or True


class PipelineMeta(ABCMeta):
    RESPONSE_CALLBACKS: Dict[str, Callable]
    RESULT_CALLBACKS: Dict[str, Callable]
    NODES_FLAGS: Dict[str, NodeFlag]

    def __new__(cls, name, bases, dct):
        kls = super(PipelineMeta, cls).__new__(cls, name, bases, dct)

        for name, method in PipelineMeta.get_methods(kls).items():
            if getattr(method, "__coredis_command", None):
                setattr(kls, name, wrap_pipeline_method(kls, method))

        return kls

    @staticmethod
    def get_methods(kls) -> Dict[str, Callable]:
        return dict(k for k in inspect.getmembers(kls) if inspect.isfunction(k[1]))


class ClusterPipelineMeta(PipelineMeta):
    def __new__(cls, name, bases, dct):
        kls = super(ClusterPipelineMeta, cls).__new__(cls, name, bases, dct)
        for name, method in ClusterPipelineMeta.get_methods(kls).items():
            if cmd := getattr(method, "__coredis_command", None):
                if not cmd.cluster.pipeline:
                    setattr(kls, name, block_pipeline_command(method))
                else:
                    if cmd.cluster.flag:
                        kls.NODES_FLAGS[cmd.command] = cmd.cluster.flag
                    if cmd.response_callback:
                        kls.RESPONSE_CALLBACKS[cmd.command] = cmd.response_callback
                    if cmd.cluster.multi_node:
                        kls.RESULT_CALLBACKS[cmd.command] = cmd.cluster.combine or (
                            lambda r, **_: r
                        )
                    else:
                        kls.RESULT_CALLBACKS[cmd.command] = lambda response, **_: list(
                            response.values()
                        ).pop()
        return kls


class Pipeline(BasePipeline, AbstractRedis, metaclass=PipelineMeta):
    """Pipeline for the Redis class"""


class ClusterPipeline(
    AbstractRedisCluster, ResponseParser, metaclass=ClusterPipelineMeta
):

    connection_pool: ClusterConnectionPool
    command_stack: List[ClusterPipelineCommand]

    RESPONSE_CALLBACKS: Dict[str, Callable] = {}
    RESULT_CALLBACKS: Dict[str, Callable] = {}
    NODES_FLAGS: Dict[str, NodeFlag] = {}

    def __init__(
        self,
        connection_pool: ClusterConnectionPool,
        result_callbacks=None,
        response_callbacks=None,
        startup_nodes=None,
        transaction: Optional[bool] = False,
        watches=None,
    ):
        self.command_stack = []
        self.refresh_table_asap = False
        self.connection_pool: ClusterConnectionPool = connection_pool
        self.result_callbacks = (
            result_callbacks or self.__class__.RESULT_CALLBACKS.copy()
        )
        self.startup_nodes = startup_nodes if startup_nodes else []
        self.nodes_flags = self.__class__.NODES_FLAGS.copy()
        self.response_callbacks = dict_merge(
            response_callbacks or self.__class__.RESPONSE_CALLBACKS.copy()
        )
        self._transaction = transaction
        self.watches = watches or None
        self.watching = False
        self.explicit_transaction = False

    async def watch(self, *keys: ValueT) -> bool:
        raise NotImplementedError

    def __repr__(self):
        return "{0}".format(type(self).__name__)

    def __del__(self):
        self.reset()

    def __len__(self):
        return len(self.command_stack)

    async def __aenter__(self) -> "ClusterPipeline":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.reset()

    def _determine_slot(self, *args):
        """Figure out what slot based on command and args"""

        if len(args) <= 1:
            raise RedisClusterException(
                "No way to dispatch this command to Redis Cluster. Missing key."
            )
        command = args[0]

        if command in ["EVAL", "EVALSHA"]:
            numkeys = args[2]
            keys = args[3 : 3 + numkeys]
            slots = {self.connection_pool.nodes.keyslot(key) for key in keys}

            if len(slots) != 1:
                raise RedisClusterException(
                    "{0} - all keys must map to the same key slot".format(command)
                )

            return slots.pop()

        key = args[1]

        return self.connection_pool.nodes.keyslot(key)

    async def execute_command(self, *args, **kwargs):
        return self.pipeline_execute_command(*args, **kwargs)

    def pipeline_execute_command(self, *args, **options):
        self.command_stack.append(
            ClusterPipelineCommand(
                args=args, options=options, position=len(self.command_stack)
            )
        )

        return self

    def raise_first_error(self, stack):
        for c in stack:
            r = c.result

            if isinstance(r, Exception):
                self.annotate_exception(r, c.position + 1, c.args)
                raise r

    def annotate_exception(self, exception, number, command):
        cmd = " ".join(str(x) for x in command)
        msg = "Command # {0} ({1}) of pipeline caused error: {2}".format(
            number, cmd, exception.args[0]
        )
        exception.args = (msg,) + exception.args[1:]

    async def execute(self, raise_on_error=True) -> Any:
        await self.connection_pool.initialize()
        stack = self.command_stack

        if not stack:
            return []

        if self._transaction:
            execute = self.send_cluster_transaction
        else:
            execute = self.send_cluster_commands
        try:
            return await execute(stack, raise_on_error)
        finally:
            self.reset()

    def reset(self):
        """Empties pipeline"""
        self.command_stack = []

        self.scripts = set()
        self.watches = []
        # clean up the other instance attributes
        self.watching = False
        self.explicit_transaction = False

    @clusterdown_wrapper
    async def send_cluster_transaction(self, stack, raise_on_error=True):
        # the first time sending the commands we send all of the commands that were queued up.
        # if we have to run through it again, we only retry the commands that failed.
        attempt = sorted(stack, key=lambda x: x.position)
        node: Dict = {}

        # as we move through each command that still needs to be processed,
        # we figure out the slot number that command maps to, then from the slot determine the node.

        for c in attempt:
            # refer to our internal node -> slot table that tells us where a given
            # command should route to.
            slot = self._determine_slot(*c.args)
            hashed_node = self.connection_pool.get_node_by_slot(slot)

            # now that we know the name of the node ( it's just a string in the form of host:port )
            # we can build a list of commands for each node.

            if node.get("name") != hashed_node["name"]:
                # raise error if commands in a transaction can not hash to same node

                if len(node) > 0:
                    raise ClusterTransactionError(
                        "Keys in request don't hash to the same node"
                    )
            node = hashed_node
        conn = self.connection_pool.get_connection_by_node(node)

        if self.watches:
            await self._watch(node, conn, self.watches)
        node_commands = NodeCommands(self.parse_response, conn, in_transaction=True)
        node_commands.append(ClusterPipelineCommand(("MULTI",)))
        node_commands.extend(attempt)
        node_commands.append(ClusterPipelineCommand(("EXEC",)))
        self.explicit_transaction = True
        await node_commands.write()
        # todo: make this place clear
        try:
            await node_commands.read()
        except ExecAbortError:
            if self.explicit_transaction:
                await conn.send_command("DISCARD")
                await conn.read_response()

        # If at least one watched key is modified before the EXEC command,
        # the whole transaction aborts,
        # and EXEC returns a Null reply to notify that the transaction failed.

        if node_commands.commands[-1].result is None:
            raise WatchError
        self.connection_pool.release(conn)

        if self.watching:
            await self._unwatch(conn)

        if raise_on_error:
            self.raise_first_error(stack)

    @clusterdown_wrapper
    async def send_cluster_commands(
        self, stack, raise_on_error=True, allow_redirections=True
    ):
        """
        Sends a bunch of cluster commands to the redis cluster.

        `allow_redirections` If the pipeline should follow `ASK` & `MOVED` responses
        automatically. If set to false it will raise RedisClusterException.
        """
        # the first time sending the commands we send all of the commands that were queued up.
        # if we have to run through it again, we only retry the commands that failed.
        attempt = sorted(stack, key=lambda x: x.position)

        # build a list of node objects based on node names we need to
        nodes = {}

        # as we move through each command that still needs to be processed,
        # we figure out the slot number that command maps to, then from the slot determine the node.

        for c in attempt:
            # refer to our internal node -> slot table that tells us where a given
            # command should route to.
            slot = self._determine_slot(*c.args)
            node = self.connection_pool.get_node_by_slot(slot)

            # little hack to make sure the node name is populated. probably could clean this up.
            self.connection_pool.nodes.set_node_name(node)

            # now that we know the name of the node ( it's just a string in the form of host:port )
            # we can build a list of commands for each node.
            node_name = node["name"]

            if node_name not in nodes:
                nodes[node_name] = NodeCommands(
                    self.parse_response,
                    self.connection_pool.get_connection_by_node(node),
                )

            nodes[node_name].append(c)

        # send the commands in sequence.
        # we  write to all the open sockets for each node first, before reading anything
        # this allows us to flush all the requests out across the network essentially in parallel
        # so that we can read them all in parallel as they come back.
        # we dont' multiplex on the sockets as they come available, but that shouldn't make
        # too much difference.
        node_commands = nodes.values()

        for n in node_commands:
            await n.write()

        for n in node_commands:
            await n.read()

        # release all of the redis connections we allocated earlier back into the connection pool.
        # we used to do this step as part of a try/finally block, but it is really dangerous to
        # release connections back into the pool if for some reason the socket has data still left
        # in it from a previous operation. The write and read operations already have try/catch
        # around them for all known types of errors including connection and socket level errors.
        # So if we hit an exception, something really bad happened and putting any of
        # these connections back into the pool is a very bad idea.
        # the socket might have unread buffer still sitting in it, and then the
        # next time we read from it we pass the buffered result back from a previous
        # command and every single request after to that connection will always get
        # a mismatched result. (not just theoretical, I saw this happen on production x.x).

        for n in nodes.values():
            self.connection_pool.release(n.connection)

        # if the response isn't an exception it is a valid response from the node
        # we're all done with that command, YAY!
        # if we have more commands to attempt, we've run into problems.
        # collect all the commands we are allowed to retry.
        # (MOVED, ASK, or connection errors or timeout errors)
        attempt = sorted(
            [c for c in attempt if isinstance(c.result, ERRORS_ALLOW_RETRY)],
            key=lambda x: x.position,
        )

        if attempt and allow_redirections:
            # RETRY MAGIC HAPPENS HERE!
            # send these remaing comamnds one at a time using `execute_command`
            # in the main client. This keeps our retry logic in one place mostly,
            # and allows us to be more confident in correctness of behavior.
            # at this point any speed gains from pipelining have been lost
            # anyway, so we might as well make the best attempt to get the correct
            # behavior.
            #
            # The client command will handle retries for each individual command
            # sequentially as we pass each one into `execute_command`. Any exceptions
            # that bubble out should only appear once all retries have been exhausted.
            #
            # If a lot of commands have failed, we'll be setting the
            # flag to rebuild the slots table from scratch. So MOVED errors should
            # correct themselves fairly quickly.
            await self.connection_pool.nodes.increment_reinitialize_counter(
                len(attempt)
            )

            for c in attempt:
                try:
                    # send each command individually like we do in the main client.
                    c.result = await super(ClusterPipeline, self).execute_command(
                        *c.args, **c.options
                    )
                except RedisError as e:
                    c.result = e

        # turn the response back into a simple flat array that corresponds
        # to the sequence of commands issued in the stack in pipeline.execute()
        response = tuple(c.result for c in sorted(stack, key=lambda x: x.position))

        if raise_on_error:
            self.raise_first_error(stack)

        return response

    def _fail_on_redirect(self, allow_redirections):
        if not allow_redirections:
            raise RedisClusterException(
                "ASK & MOVED redirection not allowed in this pipeline"
            )

    def _multi(self):
        raise RedisClusterException("method multi() is not implemented")

    def immediate_execute_command(self, *args, **options):
        raise RedisClusterException(
            "method immediate_execute_command() is not implemented"
        )

    def load_scripts(self):
        raise RedisClusterException("method load_scripts() is not implemented")

    async def _watch(self, node, conn, names):
        "Watches the values at keys ``names``"

        for name in names:
            slot = self._determine_slot("WATCH", name)
            dist_node = self.connection_pool.get_node_by_slot(slot)

            if node.get("name") != dist_node["name"]:
                # raise error if commands in a transaction can not hash to same node

                if len(node) > 0:
                    raise ClusterTransactionError(
                        "Keys in request don't hash to the same node"
                    )

        if self.explicit_transaction:
            raise RedisError("Cannot issue a WATCH after a MULTI")
        await conn.send_command("WATCH", *names)

        return await conn.read_response()

    async def _unwatch(self, conn):
        """Unwatches all previously specified keys"""
        await conn.send_command("UNWATCH")
        res = await conn.read_response()

        return self.watching and res or True

    def script_load_for_pipeline(self, *args, **kwargs):
        raise RedisClusterException(
            "method script_load_for_pipeline() is not implemented"
        )

    def delete(self, keys: Iterable[KeyT]):
        """Deletes a key specified by ``names``"""

        _keys = list(keys)
        if len(_keys) != 1:
            raise RedisClusterException(
                "deleting multiple keys is not implemented in pipeline command"
            )

        return self.execute_command("DEL", _keys[0])
