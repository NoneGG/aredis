import asyncio
import sys
from functools import wraps


def b(x):
    return x.encode('latin-1') if not isinstance(x, bytes) else x


def iteritems(x):
    return iter(x.items())


def iterkeys(x):
    return iter(x.keys())


def itervalues(x):
    return iter(x.values())


def ban_python_version_lt(min_version):
    min_version = tuple(map(int, min_version.split('.')))

    def decorator(func):
        @wraps(func)
        def _inner(*args, **kwargs):
            if sys.version_info[:2] < min_version:
                raise EnvironmentError(
                    '{} not supported in Python version less than {}'
                        .format(func.__name__, min_version)
                )
            else:
                return func(*args, **kwargs)
        return _inner
    return decorator


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
