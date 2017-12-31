cdef bytes SYM_STAR = b'*'
cdef bytes SYM_DOLLAR = b'$'
cdef bytes SYM_CRLF = b'\r\n'
cdef bytes SYM_LF = b'\n'
cdef bytes SYM_EMPTY = b''


cpdef bytes b(x):
    if not isinstance(x, bytes):
        return (<unicode>x).encode('latin-1')
    else:
        return x


cpdef str nativestr(x):
    if isinstance(x, str):
        return x
    else:
        return x.decode('utf-8', 'replace')

cpdef bytes encode(str encoding, value):
    """cython: Return a bytestring representation of the value"""
    if isinstance(value, bytes):
        return value
    elif isinstance(value, (int, float)):
        value = b(str(value))
    elif not isinstance(value, str):
        value = str(value)
    if isinstance(value, str):
        value = value.encode(encoding)
    return value

cpdef list pack_command(str encoding, tuple args):
    """cython: Pack a series of arguments into the Redis protocol"""
    cdef list output = []
    # the client might have included 1 or more literal arguments in
    # the command name, e.g., 'CONFIG GET'. The Redis server expects these
    # arguments to be sent separately, so split the first argument
    # manually. All of these arguements get wrapped in the Token class
    # to prevent them from being encoded.
    cdef str command = args[0]
    if ' ' in command:
        args = tuple([b(s) for s in command.split()]) + args[1:]
    else:
        args = (b(command),) + args[1:]

    cdef bytes buff = SYM_EMPTY.join((SYM_STAR, b(str(len(args))), SYM_CRLF))
    for arg in args:
        # to avoid large string mallocs, chunk the command into the
        # output list if we're sending large values
        arg = encode(encoding, arg)
        if len(buff) > 6000 or len(arg) > 6000:
            buff = SYM_EMPTY.join((buff, SYM_DOLLAR, b(str(len(arg))), SYM_CRLF))
            output.append(buff)
            output.append(b(arg))
            buff = SYM_CRLF
        else:
            buff = SYM_EMPTY.join((buff, SYM_DOLLAR, b(str(len(arg))),
                                   SYM_CRLF, b(arg), SYM_CRLF))
    output.append(buff)
    return output


cpdef list pack_commands(str encoding, list commands):
    """cython: Pack multiple commands into the Redis protocol"""
    cdef list output = []
    cdef list pieces = []
    cdef int buffer_length = 0

    for cmd in commands:
        for chunk in pack_command(encoding, cmd):
            pieces.append(chunk)
            buffer_length += len(chunk)

        if buffer_length > 6000:
            output.append(SYM_EMPTY.join(pieces))
            buffer_length = 0
            pieces = []

    if pieces:
        output.append(SYM_EMPTY.join(pieces))
    return output
