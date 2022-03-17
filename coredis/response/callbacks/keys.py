from typing import Any, AnyStr, Tuple, Union

from coredis.response.callbacks import ParametrizedCallback, SimpleCallback
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
