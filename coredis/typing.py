import os
import warnings
from abc import ABC, abstractmethod
from numbers import Number
from typing import (
    Any,
    AnyStr,
    Callable,
    Generic,
    Iterable,
    List,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

from typing_extensions import (
    Annotated,
    OrderedDict,
    ParamSpec,
    TypeAlias,
    runtime_checkable,
)

CommandArgList: TypeAlias = List[Union[str, bytes, float, Number]]

RUNTIME_TYPECHECKS = False
try:
    if os.environ.get("COREDIS_RUNTIME_CHECKS"):
        import beartype

        warnings.filterwarnings("ignore", module="beartype")
        RUNTIME_TYPECHECKS = True
except ImportError:  # noqa
    warnings.warn("Runtime checks were requested but could not import beartype")

P = ParamSpec("P")
R = TypeVar("R")

KeyT: TypeAlias = Union[str, bytes]
ValueT: TypeAlias = Union[str, bytes, int, float]


def add_runtime_checks(func: Callable[P, R]) -> Callable[P, R]:
    if RUNTIME_TYPECHECKS:
        return beartype.beartype(func)

    return func


@runtime_checkable
class SupportsWatch(Protocol):
    async def __aenter__(self) -> "SupportsWatch":
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ...

    async def watch(self, *keys: ValueT) -> bool:
        ...

    async def execute(self, raise_on_error=True) -> Any:
        ...


@runtime_checkable
class SupportsScript(Protocol):
    async def evalsha(
        self,
        sha1: ValueT,
        keys: Optional[Iterable[ValueT]] = None,
        args: Optional[Iterable[ValueT]] = None,
    ) -> Any:
        ...

    async def script_load(self, script: ValueT) -> AnyStr:
        ...


@runtime_checkable
class SupportsPipeline(Protocol):
    async def pipeline(
        self,
        transaction: Optional[bool] = True,
        watches: Optional[Iterable[ValueT]] = None,
    ) -> SupportsWatch:
        ...


class AbstractExecutor(ABC, Generic[AnyStr]):
    @abstractmethod
    async def execute_command(self, command: Any, *args: Any, **options: Any) -> Any:
        pass


__all__ = [
    "AbstractExecutor",
    "Annotated",
    "CommandArgList",
    "KeyT",
    "OrderedDict",
    "ParamSpec",
    "SupportsWatch",
    "SupportsScript",
    "SupportsPipeline",
    "TypeAlias",
    "ValueT",
]
