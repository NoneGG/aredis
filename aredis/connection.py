import asyncio
import sys
import socket
from io import BytesIO
from aredis.exceptions import (ExecAbortError, BusyLoadingError,
                               NoScriptError,
                               ReadOnlyError,
                               ResponseError,
                               InvalidResponse)


def b(x):
    return x.encode('latin-1') if not isinstance(x, bytes) else x


SYM_STAR = b('*')
SYM_DOLLAR = b('$')
SYM_CRLF = b('\r\n')
SYM_EMPTY = b('')


class BaseParser(object):
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
    "Plain Python parsing class"
    MAX_READ_LENGTH = 65535

    def __init__(self):
        self._reader = None

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
                    buf = BytesIO()
                    try:
                        while bytes_left > 0:
                            read_len = min(bytes_left, self.MAX_READ_LENGTH)
                            buf.write(await self._reader.read())
                            bytes_left -= read_len
                        buf.seek(0)
                        return buf.read(length)
                    finally:
                        buf.close()
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

DefaultParser = PythonParser


class Connection:

    def __init__(self, host='localhost', port=6379, db=0, password=None,
                 socket_timeout=None, parser_class=DefaultParser):
        self.socket_timeout = socket_timeout
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._reader = None
        self._writer = None
        self._parser = parser_class()

    async def connect(self):
        reader, writer = await asyncio.open_connection(host=self.host, port=self.port)
        self._reader = reader
        self._writer = writer
        await self.on_connect()

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
            response = await self._parser.read_response()
        except:
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
            if not self._reader:
                self._reader.close()
            if not self._writer:
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
