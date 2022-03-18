from datetime import datetime
from typing import Any, AnyStr, Tuple, Union

from coredis.exceptions import DataError, NoKeyError, RedisError
from coredis.response.callbacks import (
    DateTimeCallback,
    ParametrizedCallback,
    SimpleCallback,
)
from coredis.utils import int_or_none


class SortCallback(ParametrizedCallback):
    def transform(
        self, response: Any, **options: Any
    ) -> Union[Tuple[AnyStr, ...], int]:
        if options.get("store"):
            return response

        return tuple(response)


def parse_object(response, infotype):
    """Parse the results of an OBJECT command"""

    if infotype in ("idletime", "refcount"):
        return int_or_none(response)

    return response


class ScanCallback(SimpleCallback):
    def transform(self, response: Any) -> Tuple[int, Tuple[AnyStr, ...]]:
        cursor, r = response
        return int(cursor), tuple(r)


class ExpiryCallback(DateTimeCallback):
    def transform(self, response: Any, **kwargs: Any) -> datetime:
        if response > 0:
            return super(ExpiryCallback, self).transform(response, **kwargs)
        else:
            if response == -2:
                raise NoKeyError()
            elif response == -1:
                raise DataError()
            else:
                raise RedisError()
