from typing import Any, AnyStr, Union

from coredis.commands import ParametrizedCallback
from coredis.response.callbacks import SimpleStringCallback
from coredis.response.types import LCSMatch, LCSResult


class StringSetCallback(ParametrizedCallback):
    def transform(self, response: Any, **options: Any) -> Union[AnyStr, bool]:
        if options.get("get"):
            return response
        else:
            return SimpleStringCallback()(response)


class LCSCallback(ParametrizedCallback):
    def transform(self, response: Any, **options: Any) -> Union[AnyStr, int, LCSResult]:
        if options.get("idx") is not None:
            return LCSResult(
                tuple(
                    LCSMatch(
                        (int(k[0][0]), int(k[0][1])),
                        (int(k[1][0]), int(k[1][1])),
                        k[2] if len(k) > 2 else None,
                    )
                    for k in response[1]
                ),
                response[-1],
            )

        return response
