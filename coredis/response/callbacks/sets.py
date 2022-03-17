from typing import Any, AnyStr, Set, Tuple, Union

from coredis.commands import ParametrizedCallback, SimpleCallback


class SScanCallback(SimpleCallback):
    def transform(self, response: Any) -> Tuple[int, Set[AnyStr]]:
        cursor, r = response

        return int(cursor), set(r)


class ItemOrSetCallback(ParametrizedCallback):
    def transform(self, response: Any, **options: Any) -> Union[str, Set[AnyStr]]:
        if options.get("count"):
            return response and set(response)
        else:
            return response
