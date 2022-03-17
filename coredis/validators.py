import functools
import inspect
from typing import (
    Any,
    Callable,
    Coroutine,
    Iterable,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

from coredis.typing import ParamSpec

from .exceptions import CommandSyntaxError

R = TypeVar("R")
P = ParamSpec("P")


class MutuallyExclusiveParametersError(CommandSyntaxError):
    def __init__(self, arguments: Sequence[str], details: Optional[str]):
        message = (
            f"[{','.join(arguments)}] are mutually exclusive."
            f"{' '+details if details else ''}"
        )
        super().__init__(arguments, message)


class MutuallyInclusiveParametersMissing(CommandSyntaxError):
    def __init__(self, arguments: Sequence[str], details: Optional[str]):
        message = (
            f"[{','.join(arguments)}] are mutually inclusive and must be provided together."
            f"{' '+details if details else ''}"
        )
        super().__init__(arguments, message)


def mutually_exclusive_parameters(
    *exclusive_params: Union[str, Iterable[str]], details: Optional[str] = None
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]
]:

    primary = set([k for k in exclusive_params if isinstance(k, str)])
    secondary = [k for k in set(exclusive_params) - primary if isinstance(k, Iterable)]

    def wrapper(
        func: Callable[P, Coroutine[Any, Any, R]]
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        sig = inspect.signature(func)

        @functools.wraps(func)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            call_args = sig.bind(*args, **kwargs)
            params = [
                k
                for k in primary
                if not call_args.arguments.get(k)
                == getattr(sig.parameters.get(k), "default")
            ]

            if params:
                for group in secondary:
                    for k in group:
                        if not call_args.arguments.get(k) == getattr(
                            sig.parameters.get(k), "default"
                        ):
                            params.append(k)

                            break

            if len(params) > 1:
                raise MutuallyExclusiveParametersError(params, details)

            return await func(*args, **kwargs)

        return wrapped

    return wrapper


def mutually_inclusive_parameters(
    *inclusive_params: str, details: Optional[str] = None
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]
]:
    def wrapper(
        func: Callable[P, Coroutine[Any, Any, R]]
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        sig = inspect.signature(func)

        @functools.wraps(func)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            call_args = sig.bind(*args, **kwargs)
            params = [
                k
                for k in inclusive_params
                if not call_args.arguments.get(k)
                == getattr(sig.parameters.get(k), "default")
            ]

            if params and len(params) != len(inclusive_params):
                raise MutuallyInclusiveParametersMissing(inclusive_params, details)
            return await func(*args, **kwargs)

        return wrapped

    return wrapper
