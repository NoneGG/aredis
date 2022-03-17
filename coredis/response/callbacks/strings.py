from typing import Any, AnyStr, Union

from coredis.commands import ParametrizedCallback
from coredis.response.callbacks import SimpleStringCallback


class StringSetCallback(ParametrizedCallback):
    def transform(self, response: Any, **options: Any) -> Union[AnyStr, bool]:
        if options.get("get"):
            return response
        else:
            return SimpleStringCallback()(response)
