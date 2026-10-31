"""Network topology model (NetworkX). Used by the generator, connectivity agent,
correlation agent and orchestrator. The primary links form a tree rooted at the
core router (the monitoring vantage point); extra links give redundancy."""
from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional

import networkx as nx


class NetworkTopology:
    def __init__(self) -> None:
        self.graph = nx.Graph()      # every physical link (incl. redundant)
        self.tree = nx.DiGraph()     # primary parent -> child links
        self.core: Optional[str] = None

    # ---- construction -------------------------------------------------
    def add_device(self, device_id: str, device_type: str, role: str = "") -> None:
        self.graph.add_node(device_id, device_type=device_type, role=role)
        self.tree.add_node(device_id)

    def link(self, parent: str, child: str, primary: bool = True) -> None:
        self.graph.add_edge(parent, child, primary=primary)
        if primary:
            self.tree.add_edge(parent, child)

    @classmethod
    def build_campus(cls, n_routers: int = 3, n_switches: int = 6, n_aps: int = 8, n_servers: int = 3) -> "NetworkTopology":
        t = cls()
        routers = [f"RTR_CAMPUS_{i + 1:02d}" for i in range(n_routers)]
        t.core = routers[0]
        t.add_device(routers[0], "router", "core")
        for r in routers[1:]:
            t.add_device(r, "router", "distribution")
            t.link(routers[0], r)
        if n_routers >= 3:
            t.link(routers[1], routers[2], primary=False)  # redundant lateral link

        switches = []
        for i in range(n_switches):
            sw = f"SW_CAMPUS_{i + 1:02d}"
            switches.append(sw)
            t.add_device(sw, "switch", "access")
            t.link(routers[i % n_routers], sw)

        for i in range(n_aps):
            ap = f"AP_CAMPUS_{i + 1:02d}"
            t.add_device(ap, "access_point", "wifi")
            t.link(switches[i % n_switches], ap)

        roles = ["dns", "dhcp", "app"]
        counters: Dict[str, int] = {}
        for i in range(n_servers):
            role = roles[i] if i < len(roles) else "app"
            counters[role] = counters.get(role, 0) + 1
            sid = f"SRV_{role.upper()}_{counters[role]:02d}"
            t.add_device(sid, "server", role)
            t.link(routers[0], sid)
        return t

    # ---- queries ------------------------------------------------------
    def device_ids(self) -> List[str]:
        return list(self.graph.nodes)

    def type_of(self, device_id: str) -> str:
        return self.graph.nodes[device_id]["device_type"]

    def role_of(self, device_id: str) -> str:
        return self.graph.nodes[device_id].get("role", "")

    def devices_of_type(self, *types: str) -> List[str]:
        return [n for n, d in self.graph.nodes(data=True) if d["device_type"] in types]

    def has_device(self, device_id: str) -> bool:
        return device_id in self.graph

    def parent(self, device_id: str) -> Optional[str]:
        preds = list(self.tree.predecessors(device_id))
        return preds[0] if preds else None

    def children(self, device_id: str) -> List[str]:
        return sorted(self.tree.successors(device_id))

    def downstream(self, device_id: str) -> List[str]:
        """Every device whose primary path to the core passes through `device_id`."""
        if device_id not in self.tree:
            return []
        return sorted(nx.descendants(self.tree, device_id))

    def path_to_core(self, device_id: str) -> List[str]:
        return nx.shortest_path(self.tree.to_undirected(), device_id, self.core)

    def has_alternate_path(self, device_id: str) -> bool:
        """Could `device_id` still reach the core if its primary uplink were cut?"""
        parent = self.parent(device_id)
        if parent is None:
            return True
        g = self.graph.copy()
        g.remove_edge(parent, device_id)
        return nx.has_path(g, device_id, self.core)

    def server_with_role(self, role: str) -> Optional[str]:
        for n, d in self.graph.nodes(data=True):
            if d["device_type"] == "server" and d.get("role") == role:
                return n
        return None

    def to_dict(self) -> dict:
        return {
            "core": self.core,
            "nodes": [
                {"id": n, "type": d["device_type"], "role": d.get("role", ""), "parent": self.parent(n)}
                for n, d in self.graph.nodes(data=True)
            ],
            "edges": [{"source": u, "target": v, "primary": bool(d.get("primary", True))} for u, v, d in self.graph.edges(data=True)],
        }


@lru_cache(maxsize=1)
def default_topology() -> NetworkTopology:
    return NetworkTopology.build_campus()
