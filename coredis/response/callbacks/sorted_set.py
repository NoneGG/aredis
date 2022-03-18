from typing import Any, AnyStr, Optional, Tuple, Union

from coredis.commands import ParametrizedCallback, SimpleCallback
from coredis.response.types import ScoredMember, ScoredMembers

VALID_ZADD_OPTIONS = {"NX", "XX", "CH", "INCR"}


class ZMembersOrScoredMembers(ParametrizedCallback):
    def transform(
        self, response: Any, **kwargs: Any
    ) -> Tuple[Union[AnyStr, ScoredMember], ...]:
        if not response:
            return ()
        elif kwargs.get("withscores"):
            it = iter(response)

            return tuple(ScoredMember(*v) for v in zip(it, map(float, it)))
        else:
            return tuple(response)


class ZSetScorePairCallback(ParametrizedCallback):
    def transform(
        self, response: Any, **kwargs: Any
    ) -> Optional[Union[ScoredMember, ScoredMembers]]:
        if not response:
            return None
        elif not (kwargs.get("withscores") or kwargs.get("count")):
            if isinstance(response, list):
                return ScoredMember(response[0], float(response[1]))
            else:
                return response
        it = iter(response)

        return tuple(ScoredMember(*v) for v in zip(it, map(float, it)))


class ZMPopCallback(SimpleCallback):
    def transform(self, response: Any) -> Optional[Tuple[AnyStr, ScoredMembers]]:
        if response:
            return (
                response[0],
                tuple(ScoredMember(v[0], float(v[1])) for v in response[1]),
            )
        return None


class ZMScoreCallback(SimpleCallback):
    def transform(self, response: Any) -> Tuple[Optional[float], ...]:
        return tuple(float(score) if score is not None else None for score in response)


class ZScanCallback(SimpleCallback):
    def transform(self, response: Any) -> Tuple[int, ScoredMembers]:
        cursor, r = response
        it = iter(r)

        return int(cursor), tuple(ScoredMember(*v) for v in zip(it, map(float, it)))


class ZRandMemberCallback(ParametrizedCallback):
    def transform(self, response: Any, **kwargs: Any) -> Union[AnyStr, ScoredMembers]:
        if not response or not kwargs.get("withscores"):
            return response
        it = iter(response)

        return tuple(ScoredMember(*v) for v in zip(it, map(float, it)))


class BZPopCallback(SimpleCallback):
    def transform(self, response: Any) -> Optional[Tuple[AnyStr, AnyStr, float]]:
        return response and (response[0], response[1], float(response[2]))


class ZAddCallback(ParametrizedCallback):
    def transform(self, response: Any, *args: Any, **kwargs: Any) -> Union[int, float]:
        if kwargs.get("condition"):
            return float(response)
        return int(response)
