from typing import Any, AnyStr, Dict

from coredis.commands import SimpleCallback


class NumSubCallback(SimpleCallback):
    def transform(self, response: Any, **options: Any) -> Dict[AnyStr, int]:
        return dict(zip(response[0::2], response[1::2]))
