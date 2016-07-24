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

    found: Set[tuple] = set()
    on_stack: List[str] = []
    on_stack_set: Set[str] = set()
    visited: Set[str] = set()

    def normalise(cycle: List[str]) -> tuple:
        smallest = min(range(len(cycle)), key=lambda i: cycle[i])
        rotated = cycle[smallest:] + cycle[:smallest]
        return tuple(rotated)

    def visit(node: str) -> None:
        on_stack.append(node)
        on_stack_set.add(node)
        for nxt in graph.wraps_of(node):
            if nxt in on_stack_set:
                start = on_stack.index(nxt)
                found.add(normalise(on_stack[start:]))
            elif nxt not in visited:
                visit(nxt)
        on_stack.pop()
        on_stack_set.discard(node)
        visited.add(node)

    for key_id in sorted(graph.key_ids):
        if key_id not in visited:
            visit(key_id)

    return [list(cycle) for cycle in sorted(found)]


def reachable_data_keys(graph: WrapGraph, start: str, data_keys: Set[str]) -> Set[str]:
    """Data keys reachable from start by following wrap edges downward.

    Cycle safe: a visited set prevents infinite recursion when the graph is not
    yet known to be acyclic. The start key itself counts only if it is a data
    key, matching the idea that compromising a key exposes what it protects.
    """

    seen: Set[str] = set()
    result: Set[str] = set()

    def visit(node: str) -> None:
        for nxt in graph.wraps_of(node):
            if nxt in seen:
                continue
            seen.add(nxt)
            if nxt in data_keys:
                result.add(nxt)
