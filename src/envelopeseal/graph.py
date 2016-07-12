"""Wrap graph construction, cycle detection, and reachability.

The wrap graph is a directed graph. A node is a key id. An edge points from a
wrapping key to the key it wraps, so following edges moves down the hierarchy
from key encrypting keys toward data keys.

All traversals sort neighbours by id before recursing, so results are
deterministic regardless of the order wrap records appeared in the manifest.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from envelopeseal.manifest import Manifest


class GraphError(ValueError):
    """Raised when a wrap edge references a key id that was never declared."""


@dataclass
class WrapGraph:
    """Adjacency lists in both directions plus the set of known key ids."""

    key_ids: Set[str]
    out_edges: Dict[str, List[str]] = field(default_factory=dict)
    in_edges: Dict[str, List[str]] = field(default_factory=dict)

    def wraps_of(self, key_id: str) -> List[str]:
        """Keys directly wrapped by key_id, sorted by id."""

        return sorted(self.out_edges.get(key_id, []))

    def wrappers_of(self, key_id: str) -> List[str]:
        """Keys that directly wrap key_id, sorted by id."""

        return sorted(self.in_edges.get(key_id, []))


def build_graph(manifest: Manifest) -> WrapGraph:
    """Build a WrapGraph, raising GraphError for edges to unknown keys."""

    key_ids = set(manifest.keys.keys())
    graph = WrapGraph(key_ids=key_ids)
    for key_id in key_ids:
        graph.out_edges[key_id] = []
        graph.in_edges[key_id] = []
    for wrap in manifest.wraps:
        if wrap.wrapping_key not in key_ids:
            raise GraphError(
                f"wrap references unknown wrapping key {wrap.wrapping_key!r}"
            )
        if wrap.wrapped_key not in key_ids:
            raise GraphError(
                f"wrap references unknown wrapped key {wrap.wrapped_key!r}"
            )
        graph.out_edges[wrap.wrapping_key].append(wrap.wrapped_key)
        graph.in_edges[wrap.wrapped_key].append(wrap.wrapping_key)
    return graph


def find_cycles(graph: WrapGraph) -> List[List[str]]:
    """Return every simple cycle as a list of key ids in traversal order.

    Uses depth first search with a recursion stack. Each cycle is reported once,
    normalised to start at its lexicographically smallest member so identical
    input yields identical output. The returned list is sorted.
    """

