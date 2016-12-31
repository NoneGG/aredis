import asyncio


def b(x):
    return x.encode('latin-1') if not isinstance(x, bytes) else x


def iteritems(x):
    return iter(x.items())


def iterkeys(x):
    return iter(x.keys())


def itervalues(x):
    return iter(x.values())


async def exec_with_timeout(coroutine, timeout):
    if timeout:
        return await asyncio.wait_for(coroutine, timeout)
    else:
        return await coroutine

class dummy(object):
    """
    Instances of this class can be used as an attribute container.
    """
    pass
