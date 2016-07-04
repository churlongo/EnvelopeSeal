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

