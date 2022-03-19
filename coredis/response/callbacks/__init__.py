"""
coredis.response.callbacks
--------------------------
"""
import datetime
from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from coredis.typing import ParamSpec
from coredis.utils import nativestr

R = TypeVar("R")
P = ParamSpec("P")


class SimpleCallback(ABC):
    def __call__(self, response: Any) -> Any:
        return self.transform(response)

    @abstractmethod
    def transform(self, response: Any) -> Any:
        pass


class ParametrizedCallback(ABC):
    def __call__(self, response: Any, **kwargs: Any) -> Any:
        return self.transform(response, **kwargs)

    @abstractmethod
    def transform(self, response: Any, **kwargs: Any) -> Any:
        pass


class SimpleStringCallback(SimpleCallback):
    def __init__(self, raise_on_error: Optional[Type[Exception]] = None):
        self.raise_on_error = raise_on_error

    def transform(self, response: Any) -> Any:
        success = response and nativestr(response) == "OK"
        if not success and self.raise_on_error:
            raise self.raise_on_error(response)
        return success


class PrimitiveCallback(SimpleCallback, Generic[R]):
    @abstractmethod
    def transform(self, response: Any) -> Any:
        pass


class FloatCallback(PrimitiveCallback[float]):
    def transform(self, response: Any) -> float:
        return float(response)


class BoolCallback(PrimitiveCallback[bool]):
    def transform(self, response: Any) -> bool:
        return bool(response)


class SimpleStringOrIntCallback(SimpleCallback):
    def transform(self, response: Any) -> Union[bool, int]:
        if isinstance(response, int):
            return response
        else:
            return SimpleStringCallback()(response)


class TupleCallback(PrimitiveCallback[Tuple]):
    def transform(self, response: Any) -> Tuple:
        return tuple(response)


class ListCallback(PrimitiveCallback[List]):
    def transform(self, response: Any) -> List:
        return list(response)


class DateTimeCallback(ParametrizedCallback):
    def transform(self, response: Any, **kwargs: Any) -> datetime.datetime:
        ts = response
        if kwargs.get("unit") == "milliseconds":
            ts = ts / 1000.0
        return datetime.datetime.fromtimestamp(ts)


class DictCallback(PrimitiveCallback[Dict]):
    def __init__(self, transform_function=Optional[Callable[[List], Dict]]):
        self.transform_function = transform_function

    def transform(self, response: Any) -> Dict:
        return (
            dict(response)
            if not self.transform_function
            else self.transform_function(response)
        )


class SetCallback(PrimitiveCallback[Set]):
    def transform(self, response: Any) -> Set:
        return set(response) if response else set()


class BoolsCallback(SimpleCallback):
    def transform(self, response: Any) -> Tuple[bool, ...]:
        return tuple(bool(r) for r in response)


class OptionalPrimitiveCallback(SimpleCallback, Generic[R]):
    def transform(self, response: Any) -> Optional[R]:
        return response


class OptionalFloatCallback(OptionalPrimitiveCallback[float]):
    def transform(self, response: Any) -> Optional[float]:
        return response and float(response)


class OptionalIntCallback(OptionalPrimitiveCallback[int]):
    def transform(self, response: Any) -> Optional[int]:
        return response and int(response)


class OptionalSetCallback(OptionalPrimitiveCallback[Set]):
    def transform(self, response: Any) -> Optional[Set]:
        return response and set(response)


class OptionalTupleCallback(OptionalPrimitiveCallback[Tuple]):
    def transform(self, response: Any) -> Optional[Tuple]:
        return response and tuple(response)
