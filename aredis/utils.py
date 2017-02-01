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


class dummy(object):
    """
    Instances of this class can be used as an attribute container.
    """
    pass


# ++++++++++ functions to parse response ++++++++++++++
def string_keys_to_dict(key_string, callback):
    return dict.fromkeys(key_string.split(), callback)


def dict_merge(*dicts):
    merged = {}
    for d in dicts:
        merged.update(d)
    return merged


def bool_ok(response):
    return response == b'OK'


def list_or_args(keys, args):
    # returns a single list combining keys and args
    try:
        iter(keys)
        # a string or bytes instance can be iterated, but indicates
        # keys wasn't passed as a list
        if isinstance(keys, (str, bytes)):
            keys = [keys]
    except TypeError:
        keys = [keys]
    if args:
        keys.extend(args)
    return keys


def int_or_none(response):
    if response is None:
        return None
    return int(response)


def pairs_to_dict(response):
    "Create a dict given a list of key/value pairs"
    it = iter(response)
    return dict(zip(it, it))
