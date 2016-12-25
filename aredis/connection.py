import asyncio
import os
import sys
import ssl
import socket
from io import BytesIO
from aredis.utils import (b, exec_with_timeout)
from aredis.exceptions import (RedisError,
                               ExecAbortError,
                               BusyLoadingError,
                               NoScriptError,
                               ReadOnlyError,
                               ResponseError,
                               InvalidResponse)

try:
    import hiredis
    HIREDIS_AVAILABLE = True
except ImportError:
    HIREDIS_AVAILABLE = False


SYM_STAR = b('*')
SYM_DOLLAR = b('$')
SYM_CRLF = b('\r\n')
SYM_LF = b('\n')
SYM_EMPTY = b('')


class BaseParser(object):
    "Plain Python parsing class"
    MAX_READ_LENGTH = 65535

    EXCEPTION_CLASSES = {
        'ERR': {
            'max number of clients reached': ConnectionError
        },
        'EXECABORT': ExecAbortError,
        'LOADING': BusyLoadingError,
        'NOSCRIPT': NoScriptError,
        'READONLY': ReadOnlyError,
    }

    def parse_error(self, response):
        "Parse an error response"
        error_code = response.split(' ')[0]
        if error_code in self.EXCEPTION_CLASSES:
            response = response[len(error_code) + 1:]
            exception_class = self.EXCEPTION_CLASSES[error_code]
            if isinstance(exception_class, dict):
                exception_class = exception_class.get(response, ResponseError)
            return exception_class(response)
        return ResponseError(response)


class PythonParser(BaseParser):

    def __init__(self):
        self._reader = None
        self._buffer = None

    def __del__(self):
        try:
            self.on_disconnect()
        except Exception:
            pass

    def on_connect(self, reader):
        "Called when the socket connects"
        self._reader = reader

    def on_disconnect(self):
        "Called when the socket disconnects"
        if self._reader is not None:
            self._reader.feed_eof()
            self._reader = None

    def can_read(self):
        try:
            return self._reader and bool(self._buffer.length)
        except Exception:
            return False

    async def read(self, length=None):
        """
        Read a line from the socket if no length is specified,
        otherwise read ``length`` bytes. Always strip away the newlines.
        """
        try:
            if length is not None:
                bytes_left = length + 2  # read the line ending
                if length > self.MAX_READ_LENGTH:
                    # apparently reading more than 1MB or so from a windows
                    # socket can cause MemoryErrors. See:
                    # https://github.com/andymccurdy/redis-py/issues/205
                    # read smaller chunks at a time to work around this
                    self._buffer = BytesIO()
                    try:
                        while bytes_left > 0:
                            read_len = min(bytes_left, self.MAX_READ_LENGTH)
                            self._buffer.write(await self._reader.read(read_len))
                            bytes_left -= read_len
                        self._buffer.seek(0)
                        return self._buffer.read(length)
                    finally:
                        self._buffer.close()
                return (await self._reader.readline())[:-2]

            # no length, read a full line
            return (await self._reader.readline())[:-2]
        except Exception:
            e = sys.exc_info()[1]
            raise ConnectionError("Error while reading from socket: %s" %
                                  (e.args,))

    async def read_response(self):
        response = await self.read()
        if not response:
            raise ConnectionError("Socket closed on remote end")

        byte, response = chr(response[0]), response[1:]

        if byte not in ('-', '+', ':', '$', '*'):
            raise InvalidResponse("Protocol Error: %s, %s" %
                                  (str(byte), str(response)))

        # server returned an error
        if byte == '-':
            response = str(response)
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
        elif byte == '+':
            pass
        # int value
        elif byte == ':':
            response = int(response)
        # bulk response
        elif byte == '$':
            length = int(response)
            if length == -1:
                return None
            response = await self.read(length)
        # multi-bulk response
        elif byte == '*':
            length = int(response)
            if length == -1:
                return None
            response = list()
            for _ in range(length):
                response.append(await self.read_response())
        return response


class HiredisParser(BaseParser):
    "Parser class for connections using Hiredis"
    def __init__(self):
        if not HIREDIS_AVAILABLE:
            raise RedisError("Hiredis is not installed")
        self._stream = None
        self._reader = None

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

    def on_connect(self, stream_reader):
        self._stream = stream_reader
        kwargs = {
            'protocolError': InvalidResponse,
            'replyError': ResponseError,
        }
        self._reader = hiredis.Reader(**kwargs)

    def on_disconnect(self):
        self._stream = None
        self._reader = None

    async def read_response(self):
        if not self._reader:
            raise ConnectionError("Socket closed on remote end")
        response = self._reader.gets()
        while response is False:
            try:
                buffer = await self._stream.read(self.MAX_READ_LENGTH)
            except (socket.error, socket.timeout):
                e = sys.exc_info()[1]
                raise ConnectionError("Error while reading from socket: %s" %
                                      (e.args,))
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

    def __init__(self, keyfile=None, certfile=None,
                 cert_reqs=None, ca_certs=None):
        self.keyfile = keyfile
        self.certfile = certfile
        if cert_reqs is None:
            cert_reqs = ssl.CERT_NONE
        elif isinstance(cert_reqs, str):
            CERT_REQS = {
                'none': ssl.CERT_NONE,
                'optional': ssl.CERT_OPTIONAL,
                'required': ssl.CERT_REQUIRED
            }
            if cert_reqs not in CERT_REQS:
                raise RedisError(
                    "Invalid SSL Certificate Requirements Flag: %s" %
                    cert_reqs)
        self.cert_reqs = cert_reqs
        self.ca_certs = ca_certs

    def get(self):
        if not self.keyfile:
            self.context = ssl.create_default_context(cafile=self.ca_certs)
        else:
            self.context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            self.context.verify_mode = self.cert_reqs
            self.context.load_cert_chain(certfile=self.certfile,
                                         keyfile=self.keyfile)
            self.context.load_verify_locations(self.ca_certs)
        return self.context


class BaseConnection:
    description = 'BaseConnection'

    def __init__(self, retry_on_timeout=0,
                 stream_timeout=0, parser_class=DefaultParser):
        self._parser = parser_class()
        self._stream_timeout = stream_timeout
        self._reader = None
        self._writer = None
        self.password = ''
        self.db = ''
        self.pid = os.getpid()
        self.retry_on_timeout = retry_on_timeout
        self._description_args = dict()
        self._connect_callbacks = list()

    def __repr__(self):
        return self.description.format(**self._description_args)

    def __del__(self):
        try:
            self.disconnect()
        except Exception:
            pass

    def register_connect_callback(self, callback):
        self._connect_callbacks.append(callback)

    def clear_connect_callbacks(self):
        self._connect_callbacks = list()

    def can_read(self):
        "See if there's data that can be read."
        if not self._reader:
            self.connect()
        return self._parser.can_read()

    async def connect(self):
        await self._connect()
        # run any user callbacks. right now the only internal callback
        # is for pubsub channel/pattern resubscription
        for callback in self._connect_callbacks:
            callback(self)

    async def _connect(self):
        raise NotImplementedError

    async def on_connect(self):
        self._parser.on_connect(self._reader)

        # if a password is specified, authenticate
        if self.password:
            await self.send_command('AUTH', self.password)
            if await self.read_response() != 'OK':
                raise ConnectionError('Invalid Password')

        # if a database is specified, switch to it
        if self.db:
            await self.send_command('SELECT', self.db)
            if await self.read_response() != 'OK':
                raise ConnectionError('Invalid Database')

    async def read_response(self):
        try:
            response = await exec_with_timeout(self._parser.read_response(), self._stream_timeout)
        except Exception:
            self.disconnect()
            raise
        if isinstance(response, ResponseError):
            raise response
        return response

    async def send_packed_command(self, command):
        "Send an already packed command to the Redis server"
        if not self._writer:
            self.connect()
        try:
            if isinstance(command, str):
                command = [command]
            self._writer.writelines(command)
        except socket.timeout:
            self.disconnect()
            raise TimeoutError("Timeout writing to socket")
        except socket.error:
            e = sys.exc_info()[1]
            self.disconnect()
            if len(e.args) == 1:
                errno, errmsg = 'UNKNOWN', e.args[0]
            else:
                errno = e.args[0]
                errmsg = e.args[1]
            raise ConnectionError("Error %s while writing to socket. %s." %
                                  (errno, errmsg))
        except:
            self.disconnect()
            raise

    async def send_command(self, *args):
        if not (self._reader and self._writer):
            await self.connect()
        await self.send_packed_command(self.pack_command(*args))

    def encode(self, value):
        "Return a bytestring representation of the value"
        if isinstance(value, bytes):
            return value
        elif isinstance(value, int):
            value = b(str(value))
        elif isinstance(value, float):
            value = b(repr(value))
        elif not isinstance(value, str):
            value = str(value)
        return value

    def disconnect(self):
        "Disconnects from the Redis server"
        self._parser.on_disconnect()
        try:
            if self._reader:
                self._reader.close()
            if self._writer:
                self._writer.transport.close()
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
        if ' ' in command:
            args = tuple([b(s) for s in command.split()]) + args[1:]
        else:
            args = (b(command),) + args[1:]

        buff = SYM_EMPTY.join(
            (SYM_STAR, b(str(len(args))), SYM_CRLF))
        for arg in map(self.encode, args):
            # to avoid large string mallocs, chunk the command into the
            # output list if we're sending large values
            if len(buff) > 6000 or len(arg) > 6000:
                buff = SYM_EMPTY.join(
                    (buff, SYM_DOLLAR, b(str(len(arg))), SYM_CRLF))
                output.append(buff)
                output.append(b(arg))
                buff = SYM_CRLF
            else:
                buff = SYM_EMPTY.join((buff, SYM_DOLLAR, b(str(len(arg))),
                                       SYM_CRLF, b(arg), SYM_CRLF))
        output.append(buff)
        return output


class Connection(BaseConnection):
    description = 'Connection<host={host},port={port},db={db}>'

    def __init__(self, host='127.0.0.1', port=6379, password=None,
                 db=0, retry_on_timeout=0, stream_timeout=0, connect_timeout=0,
                 ssl_context=None, parser_class=DefaultParser):
        super(Connection, self).__init__(retry_on_timeout, stream_timeout, parser_class)
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.ssl_context = ssl_context
        self._connect_timeout = connect_timeout
        self._description_args = {
            'host': self.host,
            'port': self.port,
            'db': self.db
        }

    async def _connect(self):
        reader, writer = await exec_with_timeout(
            asyncio.open_connection(host=self.host,
                                    port=self.port,
                                    ssl=self.ssl_context),
            self._connect_timeout
        )
        self._reader = reader
        self._writer = writer
        sock = writer.transport.get_extra_info('socket')
        if sock is not None:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        await self.on_connect()


class UnixDomainSocketConnection(BaseConnection):
    description = "UnixDomainSocketConnection<path={path},db={db}>"

    def __init__(self, path='', password=None,
                 db=0, retry_on_timeout=0, stream_timeout=0, connect_timeout=0,
                 ssl_context=None, parser_class=DefaultParser):
        super(UnixDomainSocketConnection, self).__init__(retry_on_timeout, stream_timeout, parser_class)
        self.path = path
        self.db = db
        self.password = password
        self.ssl_context = ssl_context
        self._connect_timeout = connect_timeout
        self._description_args = {
            'path': self.path,
            'db': self.db
        }

    async def _connect(self):
        reader, writer = await exec_with_timeout(
            asyncio.open_unix_connection(path=self.path,
                                         ssl=self.ssl_context),
            self._connect_timeout
        )
        self._reader = reader
        self._writer = writer
        sock = writer.transport.get_extra_info('socket')
        if sock is not None:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        await self.on_connect()