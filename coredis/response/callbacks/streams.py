from typing import Any, AnyStr, Dict, Optional, Tuple, Union

from coredis.commands import ParametrizedCallback, SimpleCallback
from coredis.response.types import (
    StreamEntry,
    StreamInfo,
    StreamPending,
    StreamPendingExt,
)
from coredis.utils import pairs_to_dict, pairs_to_ordered_dict


class StreamRangeCallback(SimpleCallback):
    def transform(self, response: Any) -> Tuple[StreamEntry, ...]:
        return tuple(StreamEntry(r[0], pairs_to_ordered_dict(r[1])) for r in response)


class ClaimCallback(ParametrizedCallback):
    def transform(
        self, response: Any, **options: Any
    ) -> Union[Tuple[AnyStr, ...], Tuple[StreamEntry, ...]]:
        if options.get("justid") is not None:
            return tuple(response)
        else:
            return StreamRangeCallback()(response)


class AutoClaimCallback(ParametrizedCallback):
    def transform(
        self, response: Any, **options: Any
    ) -> Union[
        Tuple[AnyStr, Tuple[AnyStr, ...]],
        Tuple[AnyStr, Tuple[StreamEntry, ...], Tuple[AnyStr, ...]],
    ]:
        if options.get("justid") is not None:
            return response[0], tuple(response[1])
        else:
            return (
                response[0],
                StreamRangeCallback()(response[1]),
                tuple(response[2]) if len(response) > 2 else (),
            )


class MultiStreamRangeCallback(SimpleCallback):
    def transform(
        self, response: Any
    ) -> Optional[Dict[AnyStr, Tuple[StreamEntry, ...]]]:
        if response:
            mapping = {}

            for stream_id, entries in response:
                mapping[stream_id] = tuple(
                    StreamEntry(r[0], pairs_to_ordered_dict(r[1])) for r in entries
                )

            return mapping
        return None


class PendingCallback(ParametrizedCallback):
    def transform(
        self, response: Any, **options: Any
    ) -> Union[StreamPending, Tuple[StreamPendingExt, ...]]:
        if not options.get("count"):
            return StreamPending(
                response[0],
                response[1],
                response[2],
                pairs_to_ordered_dict(response[3:]),
            )
        else:
            return tuple(
                StreamPendingExt(sub[0], sub[1], sub[2], sub[3]) for sub in response
            )


class XInfoCallback(SimpleCallback):
    def transform(self, response: Any) -> Tuple[Dict[AnyStr, AnyStr], ...]:
        return tuple(pairs_to_dict(row) for row in response)


class StreamInfoCallback(ParametrizedCallback):
    def transform(self, response: Any, **options: Any) -> StreamInfo:
        res = pairs_to_dict(response)
        if not options.get("full"):

            k1 = "first-entry"
            kn = "last-entry"
            e1, en = None, None

            if res[k1] and len(res[k1]) > 0:
                e1 = StreamEntry(res[k1][0], pairs_to_ordered_dict(res[k1][1]))
                res.pop(k1)

            if res[kn] and len(res[kn]) > 0:
                en = StreamEntry(res[kn][0], pairs_to_ordered_dict(res[kn][1]))
                res.pop(kn)
            res.update({"first-entry": e1, "last-entry": en})
        else:
            groups = res.get("groups")
            if groups:
                res.update({"groups": pairs_to_dict(groups)})
            res.update(
                {
                    "entries": tuple(
                        StreamEntry(k[0], pairs_to_ordered_dict(k[1]))
                        for k in res.get("entries", [])
                    )
                }
            )
        stream_info: StreamInfo = {
            "first-entry": res.get("first-entry"),
            "last-entry": res.get("last-entry"),
            "length": res["length"],
            "radix-tree-keys": res["radix-tree-keys"],
            "radix-tree-nodes": res["radix-tree-nodes"],
            "groups": res["groups"],
            "last-generated-id": res["last-generated-id"],
            "max-deleted-entry-id": str(res.get("max-deleted-entry-id")),
            "entries-added": int(res.get("entries-added", 0)),
            "recorded-first-entry-id": str(res.get("recorded-first-entry-id")),
            "entries-read": int(res.get("entries-read", 0)),
            "entries": res.get("entries"),
        }
        return stream_info
