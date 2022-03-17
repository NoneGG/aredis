from typing import Any, AnyStr, Dict, Tuple, Union

from coredis.commands import ParametrizedCallback, SimpleCallback
from coredis.utils import pairs_to_dict


class HScanCallback(SimpleCallback):
    def transform(self, response: Any) -> Tuple[int, Dict[AnyStr, AnyStr]]:
        cursor, r = response

        return int(cursor), r and pairs_to_dict(r) or {}


class HRandFieldCallback(ParametrizedCallback):
    def transform(
        self, response: Any, **options: Any
    ) -> Union[str, Tuple[AnyStr, ...], Dict[AnyStr, AnyStr]]:
        if options.get("count"):
            if options.get("withvalues"):
                return pairs_to_dict(response)
            else:
                return tuple(response)
        else:
            return response


class HGetAllCallback(SimpleCallback):
    def transform(self, response: Any) -> Dict[AnyStr, AnyStr]:
        return pairs_to_dict(response) if response else {}
