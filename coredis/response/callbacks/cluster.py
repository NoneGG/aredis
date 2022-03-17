from typing import Any, Dict, List, Tuple, TypedDict, Union

from coredis.commands import ParametrizedCallback, SimpleCallback
from coredis.typing import ValueT
from coredis.utils import nativestr


class ClusterNode(TypedDict):
    host: ValueT
    port: int
    node_id: ValueT
    server_type: ValueT


class ClusterInfoCallback(SimpleCallback):
    def transform(self, response: Any) -> Dict[str, str]:
        response = nativestr(response)

        return dict([line.split(":") for line in response.splitlines() if line])


class ClusterSlotsCallback(SimpleCallback):
    def transform(
        self, response: Any
    ) -> Dict[Tuple[int, int], Tuple[ClusterNode, ...]]:
        res = {}

        for slot_info in response:
            min_slot, max_slot = map(int, slot_info[:2])
            nodes = slot_info[2:]
            res[(min_slot, max_slot)] = tuple([self.parse_node(node) for node in nodes])
            res[(min_slot, max_slot)][0]["server_type"] = "master"

        return res

    def parse_node(self, node) -> ClusterNode:
        return ClusterNode(
            host=node[0],
            port=node[1],
            node_id=node[2] if len(node) > 2 else "",
            server_type="slave",
        )


class ClusterNodesCallback(ParametrizedCallback):
    def transform(self, response: Any, **options: Any) -> List[Dict[str, str]]:
        resp: Union[List[str], str]
        if isinstance(response, list):
            resp = [nativestr(row) for row in response]
        else:
            resp = nativestr(response)
        current_host = options.get("current_host", "")

        def parse_slots(s):
            slots: List[Any] = []
            migrations: List[Any] = []

            for r in s.split(" "):
                if "->-" in r:
                    slot_id, dst_node_id = r[1:-1].split("->-", 1)
                    migrations.append(
                        {
                            "slot": int(slot_id),
                            "node_id": dst_node_id,
                            "state": "migrating",
                        }
                    )
                elif "-<-" in r:
                    slot_id, src_node_id = r[1:-1].split("-<-", 1)
                    migrations.append(
                        {
                            "slot": int(slot_id),
                            "node_id": src_node_id,
                            "state": "importing",
                        }
                    )
                elif "-" in r:
                    start, end = r.split("-")
                    slots.extend(range(int(start), int(end) + 1))
                else:
                    slots.append(int(r))

            return slots, migrations

        if isinstance(resp, str):
            resp = resp.splitlines()

        nodes = []

        for line in resp:
            parts = line.split(" ", 8)
            (
                self_id,
                addr,
                flags,
                master_id,
                ping_sent,
                pong_recv,
                config_epoch,
                link_state,
            ) = parts[:8]

            host, port = addr.rsplit(":", 1)

            node: Dict = {
                "id": self_id,
                "host": host or current_host,
                "port": int(port.split("@")[0]),
                "flags": tuple(flags.split(",")),
                "master": master_id if master_id != "-" else None,
                "ping_sent": int(ping_sent),
                "pong_recv": int(pong_recv),
                "link_state": link_state,
                "slots": [],
                "migrations": [],
            }

            if len(parts) >= 9:
                slots, migrations = parse_slots(parts[8])
                node["slots"], node["migrations"] = tuple(slots), migrations

            nodes.append(node)

        return nodes
