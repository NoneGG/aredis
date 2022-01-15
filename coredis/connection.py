import asyncio
import inspect
import os
import socket
import ssl
import sys
import time
import warnings
from io import BytesIO

from coredis.exceptions import (
    AskError,
    BusyLoadingError,
    ClusterCrossSlotError,
    ClusterDownError,
    ConnectionError,
    ExecAbortError,
    InvalidResponse,
    MovedError,
    NoScriptError,
    ReadOnlyError,
    RedisError,
    ResponseError,
    TimeoutError,
    TryAgainError,
)
from coredis.utils import LOOP_DEPRECATED, b, nativestr

try:
    import hiredis

    HIREDIS_AVAILABLE = True
except ImportError:
    HIREDIS_AVAILABLE = False

SYM_STAR = b("*")
SYM_DOLLAR = b("$")
SYM_CRLF = b("\r\n")
SYM_LF = b("\n")
SYM_EMPTY = b("")


async def exec_with_timeout(coroutine, timeout, *, loop=None):
    try:
        if LOOP_DEPRECATED:
            return await asyncio.wait_for(coroutine, timeout)
        else:
            return await asyncio.wait_for(coroutine, timeout, loop=loop)
    except asyncio.TimeoutError as exc:
        raise TimeoutError(exc)


class SocketBuffer:
    def __init__(self, stream_reader, read_size):
        self._stream = stream_reader
        self.read_size = read_size
        self._buffer = BytesIO()
        # number of bytes written to the buffer from the socket
        self.bytes_written = 0
        # number of bytes read from the buffer
        self.bytes_read = 0

    @property
    def length(self):
        return self.bytes_written - self.bytes_read

    async def _read_from_socket(self, length=None):
        buf = self._buffer
        buf.seek(self.bytes_written)
        marker = 0

        try:
            while True:
                data = await self._stream.read(self.read_size)
                # an empty string indicates the server shutdown the socket
                if isinstance(data, bytes) and len(data) == 0:
                    raise ConnectionError("Socket closed on remote end")
                buf.write(data)
                data_length = len(data)
                self.bytes_written += data_length
                marker += data_length

                if length is not None and length > marker:
                    continue
                break
        except socket.error:
            e = sys.exc_info()[1]
            raise ConnectionError("Error while reading from socket: %s" % (e.args,))

    async def read(self, length):
        length = length + 2  # make sure to read the \r\n terminator
        # make sure we've read enough data from the socket
        if length > self.length:
            await self._read_from_socket(length - self.length)

        self._buffer.seek(self.bytes_read)
        data = self._buffer.read(length)
        self.bytes_read += len(data)

        # purge the buffer when we've consumed it all so it doesn't
        # grow forever
        if self.bytes_read == self.bytes_written:
            self.purge()

        return data[:-2]

    async def readline(self):
        buf = self._buffer
        buf.seek(self.bytes_read)
        data = buf.readline()
        while not data.endswith(SYM_CRLF):
            # there's more data in the socket that we need
            await self._read_from_socket()
            buf.seek(self.bytes_read)
            data = buf.readline()

        self.bytes_read += len(data)

        # purge the buffer when we've consumed it all so it doesn't
        # grow forever
        if self.bytes_read == self.bytes_written:
            self.purge()

        return data[:-2]

    def purge(self):
        self._buffer.seek(0)
        self._buffer.truncate()
        self.bytes_written = 0
        self.bytes_read = 0

    def close(self):
        try:
            self.purge()
            self._buffer.close()
        except Exception:
            # redis-py issue #633 suggests the purge/close somehow raised a
            # BadFileDescriptor error. Perhaps the client ran out of
            # memory or something else? It's probably OK to ignore
            # any error being raised from purge/close since we're
            # removing the reference to the instance below.
            pass
        self._buffer = None
        self._sock = None


class BaseParser:
    """Plain Python parsing class"""

    EXCEPTION_CLASSES = {
        "ERR": {"max number of clients reached": ConnectionError},
        "EXECABORT": ExecAbortError,
        "LOADING": BusyLoadingError,
        "NOSCRIPT": NoScriptError,
        "READONLY": ReadOnlyError,
        "ASK": AskError,
        "TRYAGAIN": TryAgainError,
        "MOVED": MovedError,
        "CLUSTERDOWN": ClusterDownError,
        "CROSSSLOT": ClusterCrossSlotError,
    }

    def parse_error(self, response):
        """Parse an error response"""
        error_code = response.split(" ")[0]
        if error_code in self.EXCEPTION_CLASSES:
            response = response[len(error_code) + 1 :]
            exception_class = self.EXCEPTION_CLASSES[error_code]
            if isinstance(exception_class, dict):
                exception_class = exception_class.get(response, ResponseError)
            return exception_class(response)
        return ResponseError(response)


class PythonParser(BaseParser):
    def __init__(self, read_size):
        self._stream = None
        self._buffer = None
        self._read_size = read_size
        self.encoding = None

    def __del__(self):
        try:
            self.on_disconnect()
        except Exception:
            pass

    def on_connect(self, connection):
        """Called when the stream connects"""
        self._stream = connection._reader
        self._buffer = SocketBuffer(self._stream, self._read_size)
        if connection.decode_responses:
            self.encoding = connection.encoding

    def on_disconnect(self):
        """Called when the stream disconnects"""
        if self._stream is not None:
            self._stream = None
        if self._buffer is not None:
            self._buffer.close()
            self._buffer = None
        self.encoding = None

    def can_read(self):
        return self._buffer and bool(self._buffer.length)

    async def read_response(self):
        if not self._buffer:
            raise ConnectionError("Socket closed on remote end")
        response = await self._buffer.readline()
        if not response:
            raise ConnectionError("Socket closed on remote end")

        byte, response = chr(response[0]), response[1:]

        if byte not in ("-", "+", ":", "$", "*"):
            raise InvalidResponse("Protocol Error: %s, %s" % (str(byte), str(response)))

        # server returned an error
        if byte == "-":
            response = response.decode()
            error = self.parse_error(response)
            # if the error is a ConnectionError, raise immediately so the user
            # is notified
            if isinstance(error, ConnectionError):
                raise error
            # otherwise, we're dealing with a ResponseError that might belong
            # inside a pipeline response. the connection's read_response()
            # and/or the pipeline's execute() will raise this error if
            # necessary, so just return the exception instance here.
            return error
        # single value
        elif byte == "+":
            pass
        # int value
        elif byte == ":":
            response = int(response)
        # bulk response
        elif byte == "$":
            length = int(response)
            if length == -1:
                return None
            response = await self._buffer.read(length)
        # multi-bulk response
        elif byte == "*":
            length = int(response)
            if length == -1:
                return None
            response = []
            for i in range(length):
                response.append(await self.read_response())
        if isinstance(response, bytes) and self.encoding:
            response = response.decode(self.encoding)
        return response


class HiredisParser(BaseParser):
    """Parser class for connections using Hiredis"""

    def __init__(self, read_size):
        if not HIREDIS_AVAILABLE:
            raise RedisError("Hiredis is not installed")
        self._stream = None
        self._reader = None
        self._read_size = read_size

    def __del__(self):
        try:
            self.on_disconnect()
        except Exception:
            pass

    def can_read(self):
        if not self._reader:
            raise ConnectionError("Socket closed on remote end")

        if self._next_response is False:
            self._next_response = self._reader.gets()
        return self._next_response is not False

    def on_connect(self, connection):
        self._stream = connection._reader
        kwargs = {
            "protocolError": InvalidResponse,
            "replyError": ResponseError,
        }
        if connection.decode_responses:
            kwargs["encoding"] = connection.encoding
        self._reader = hiredis.Reader(**kwargs)
        self._next_response = False

    def on_disconnect(self):
        if self._stream is not None:
            self._stream = None
        self._reader = None
        self._next_response = False

    async def read_response(self):
        if not self._stream:
            raise ConnectionError("Socket closed on remote end")

        # _next_response might be cached from a can_read() call
        if self._next_response is not False:
            response = self._next_response
            self._next_response = False
            return response

        response = self._reader.gets()
        while response is False:
            try:
                buffer = await self._stream.read(self._read_size)
            # CancelledError will be caught by client so that command won't be retried again
            # For more detailed discussion please see https://github.com/alisaifee/coredis/issues/56
            except asyncio.CancelledError:
                raise
            except Exception:
                e = sys.exc_info()[1]
                raise ConnectionError(
                    "Error {} while reading from stream: {}".format(type(e), e.args)
                )
            if not buffer:
                raise ConnectionError("Socket closed on remote end")
            self._reader.feed(buffer)
            response = self._reader.gets()
        if isinstance(response, ResponseError):
            response = self.parse_error(response.args[0])
        return response


if HIREDIS_AVAILABLE:
    DefaultParser = HiredisParser
else:
    DefaultParser = PythonParser


class RedisSSLContext:
    def __init__(self, keyfile=None, certfile=None, cert_reqs=None, ca_certs=None):
        self.keyfile = keyfile
        self.certfile = certfile
        if cert_reqs is None:
            self.cert_reqs = ssl.CERT_NONE
        elif isinstance(cert_reqs, str):
            CERT_REQS = {
                "none": ssl.CERT_NONE,
                "optional": ssl.CERT_OPTIONAL,
                "required": ssl.CERT_REQUIRED,
            }
            if cert_reqs not in CERT_REQS:
                raise RedisError(
                    "Invalid SSL Certificate Requirements Flag: %s" % cert_reqs
                )
            self.cert_reqs = CERT_REQS[cert_reqs]
        self.ca_certs = ca_certs
        self.context = None

    def get(self):
        if not self.keyfile:
            self.context = ssl.create_default_context(cafile=self.ca_certs)
        else:
            self.context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            self.context.verify_mode = self.cert_reqs
            self.context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
            self.context.load_verify_locations(self.ca_certs)
        return self.context


class BaseConnection:
    description = "BaseConnection"

    def __init__(
        self,
        retry_on_timeout=False,
        stream_timeout=None,
        parser_class=DefaultParser,
        reader_read_size=65535,
        encoding="utf-8",
        decode_responses=False,
        *,
        loop=None
    ):
        self._parser = parser_class(reader_read_size)
        self._stream_timeout = stream_timeout
        self._reader = None
        self._writer = None
        self.password = ""
        self.db = ""
        self.pid = os.getpid()
        self.retry_on_timeout = retry_on_timeout
        self._description_args = dict()
        self._connect_callbacks = list()
        self.encoding = encoding
        self.decode_responses = decode_responses
        self.loop = loop
        # flag to show if a connection is waiting for response
        self.awaiting_response = False
        self.last_active_at = time.time()

    def __repr__(self):
        return self.description.format(**self._description_args)

    def __del__(self):
        try:
            self.disconnect()
        except Exception:
            pass

    @property
    def is_connected(self):
        return bool(self._reader and self._writer)

    def register_connect_callback(self, callback):
        self._connect_callbacks.append(callback)

    def clear_connect_callbacks(self):
        self._connect_callbacks = list()

    async def can_read(self):
        """Checks for data that can be read"""
        if not self.is_connected:
            await self.connect()
        return self._parser.can_read()

    async def connect(self):
        try:
            await self._connect()
        except asyncio.CancelledError:
            raise
        except Exception:
            raise ConnectionError()
        # run any user callbacks. right now the only internal callback
        # is for pubsub channel/pattern resubscription
        for callback in self._connect_callbacks:
            task = callback(self)
            # typing.Awaitable is not available in Python3.5
            # so use inspect.isawaitable instead
            # according to issue https://github.com/alisaifee/coredis/issues/77
            if inspect.isawaitable(task):
                await task

    async def _connect(self):
        raise NotImplementedError

    async def on_connect(self):
        self._parser.on_connect(self)

        # if a password is specified, authenticate
        if self.password:
            await self.send_command("AUTH", self.password)
            if nativestr(await self.read_response()) != "OK":
                raise ConnectionError("Invalid Password")

        # if a database is specified, switch to it
        if self.db:
            await self.send_command("SELECT", self.db)
            if nativestr(await self.read_response()) != "OK":
                raise ConnectionError("Invalid Database")
        self.last_active_at = time.time()

    async def read_response(self):
        try:
            response = await exec_with_timeout(
                self._parser.read_response(), self._stream_timeout, loop=self.loop
            )
            self.last_active_at = time.time()
        except TimeoutError:
            self.disconnect()
            raise
        if isinstance(response, RedisError):
            raise response
        self.awaiting_response = False
        return response

    async def send_packed_command(self, command):
        """Sends an already packed command to the Redis server"""
        if not self._writer:
            await self.connect()
        try:
            if isinstance(command, str):
                command = [command]
            self._writer.writelines(command)
        except TimeoutError:
            self.disconnect()
            raise TimeoutError("Timeout writing to socket")
        except Exception:
            e = sys.exc_info()[1]
            self.disconnect()
            if len(e.args) == 1:
                errno, errmsg = "UNKNOWN", e.args[0]
            else:
                errno = e.args[0]
                errmsg = e.args[1]
            raise ConnectionError(
                "Error %s while writing to socket. %s." % (errno, errmsg)
            )
        except Exception:
            self.disconnect()
            raise

    async def send_command(self, *args):
        if not self.is_connected:
            await self.connect()
        await self.send_packed_command(self.pack_command(*args))
        self.awaiting_response = True
        self.last_active_at = time.time()

    def encode(self, value):
        """Returns a bytestring representation of the value"""
        if isinstance(value, bytes):
            return value
        elif isinstance(value, int):
            value = b(str(value))
        elif isinstance(value, float):
            value = b(repr(value))
        elif not isinstance(value, str):
            value = str(value)
        if isinstance(value, str):
            value = value.encode(self.encoding)
        return value

    def disconnect(self):
        """Disconnects from the Redis server"""
        self._parser.on_disconnect()
        try:
            self._writer.close()
        except Exception:
            pass
        self._reader = None
        self._writer = None

    def pack_command(self, *args):
        "Pack a series of arguments into the Redis protocol"
        output = []
        # the client might have included 1 or more literal arguments in
        # the command name, e.g., 'CONFIG GET'. The Redis server expects these
        # arguments to be sent separately, so split the first argument
        # manually. All of these arguements get wrapped in the Token class
        # to prevent them from being encoded.
        command = args[0]
        if " " in command:
            args = tuple([b(s) for s in command.split()]) + args[1:]
        else:
            args = (b(command),) + args[1:]

        buff = SYM_EMPTY.join((SYM_STAR, b(str(len(args))), SYM_CRLF))
        for arg in map(self.encode, args):
            # to avoid large string mallocs, chunk the command into the
            # output list if we're sending large values
            if len(buff) > 6000 or len(arg) > 6000:
                buff = SYM_EMPTY.join((buff, SYM_DOLLAR, b(str(len(arg))), SYM_CRLF))
                output.append(buff)
                output.append(b(arg))
                buff = SYM_CRLF
            else:
                buff = SYM_EMPTY.join(
                    (buff, SYM_DOLLAR, b(str(len(arg))), SYM_CRLF, b(arg), SYM_CRLF)
                )
        output.append(buff)
        return output

    def pack_commands(self, commands):
        "Pack multiple commands into the Redis protocol"
        output = []
        pieces = []
        buffer_length = 0

        for cmd in commands:
            for chunk in self.pack_command(*cmd):
                pieces.append(chunk)
                buffer_length += len(chunk)

            if buffer_length > 6000:
                output.append(SYM_EMPTY.join(pieces))
                buffer_length = 0
                pieces = []

        if pieces:
            output.append(SYM_EMPTY.join(pieces))
        return output


class Connection(BaseConnection):
    description = "Connection<host={host},port={port},db={db}>"

    def __init__(
        self,
        host="127.0.0.1",
        port=6379,
        password=None,
        db=0,
        retry_on_timeout=False,
        stream_timeout=None,
        connect_timeout=None,
        ssl_context=None,
        parser_class=DefaultParser,
        reader_read_size=65535,
        encoding="utf-8",
        decode_responses=False,
        socket_keepalive=None,
        socket_keepalive_options=None,
        *,
        loop=None
    ):
        super(Connection, self).__init__(
            retry_on_timeout,
            stream_timeout,
            parser_class,
            reader_read_size,
            encoding,
            decode_responses,
            loop=loop,
        )
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.ssl_context = ssl_context
        self._connect_timeout = connect_timeout
        self._description_args = {"host": self.host, "port": self.port, "db": self.db}
        self.socket_keepalive = socket_keepalive
        self.socket_keepalive_options = socket_keepalive_options or {}

    async def _connect(self):
        if LOOP_DEPRECATED:
            connection = asyncio.open_connection(
                host=self.host, port=self.port, ssl=self.ssl_context
            )
        else:
            connection = asyncio.open_connection(
                host=self.host, port=self.port, ssl=self.ssl_context, loop=self.loop
            )
        reader, writer = await exec_with_timeout(
            connection, self._connect_timeout, loop=self.loop
        )
        self._reader = reader
        self._writer = writer
        sock = writer.transport.get_extra_info("socket")
        if sock is not None:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            try:
                # TCP_KEEPALIVE
                if self.socket_keepalive:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    for k, v in self.socket_keepalive_options.items():
                        sock.setsockopt(socket.SOL_TCP, k, v)
            except (socket.error, TypeError):
                # `socket_keepalive_options` might contain invalid options
                # causing an error. Do not leave the connection open.
                writer.close()
                raise
        await self.on_connect()


class UnixDomainSocketConnection(BaseConnection):
    description = "UnixDomainSocketConnection<path={path},db={db}>"

    def __init__(
        self,
        path="",
        password=None,
        db=0,
        retry_on_timeout=False,
        stream_timeout=None,
        connect_timeout=None,
        ssl_context=None,
        parser_class=DefaultParser,
        reader_read_size=65535,
        encoding="utf-8",
        decode_responses=False,
        *,
        loop=None
    ):
        super(UnixDomainSocketConnection, self).__init__(
            retry_on_timeout,
            stream_timeout,
            parser_class,
            reader_read_size,
            encoding,
            decode_responses,
            loop=loop,
        )
        self.path = path
        self.db = db
        self.password = password
        self.ssl_context = ssl_context
        self._connect_timeout = connect_timeout
        self._description_args = {"path": self.path, "db": self.db}

    async def _connect(self):
        if LOOP_DEPRECATED:
            connection = asyncio.open_unix_connection(
                path=self.path, ssl=self.ssl_context
            )
        else:
            connection = asyncio.open_unix_connection(
                path=self.path, ssl=self.ssl_context, loop=self.loop
            )
        reader, writer = await exec_with_timeout(
            connection, self._connect_timeout, loop=self.loop
        )
        self._reader = reader
        self._writer = writer
        await self.on_connect()


class ClusterConnection(Connection):
    "Manages TCP communication to and from a Redis server"
    description = "ClusterConnection<host={host},port={port}>"

    def __init__(self, *args, **kwargs):
        self.readonly = kwargs.pop("readonly", False)
        super(ClusterConnection, self).__init__(*args, **kwargs)

    async def on_connect(self):
        """
        Initialize the connection, authenticate and select a database and send READONLY if it is
        set during object initialization.
        """
        if self.db:
            warnings.warn("SELECT DB is not allowed in cluster mode")
            self.db = ""
        await super(ClusterConnection, self).on_connect()
        if self.readonly:
            await self.send_command("READONLY")
            if nativestr(await self.read_response()) != "OK":
                raise ConnectionError("READONLY command failed")
