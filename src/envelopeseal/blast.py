"""Blast radius: how many data keys are reachable from each key encrypting key.

If a key encrypting key is compromised, every data key reachable from it by
following wrap edges is compromised too, because the attacker can unwrap them in
turn. The blast radius of a key encrypting key is the count of those data keys.
It is the single number that says how bad losing that one key would be.

Data keys are not reported here: their blast radius is themselves, which is not
useful for prioritising which key encrypting keys to protect hardest.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set

from envelopeseal.graph import WrapGraph, reachable_data_keys
from envelopeseal.manifest import Manifest


@dataclass(frozen=True)
class BlastRadius:
    """The reachable data keys for one key encrypting key."""

    key_id: str
    data_keys: List[str]

    @property
    def count(self) -> int:
        return len(self.data_keys)


def data_key_ids(manifest: Manifest) -> Set[str]:
    """The set of data key ids in the manifest."""

    return {k.key_id for k in manifest.keys.values() if k.is_data_key}


def blast_radii(manifest: Manifest, graph: WrapGraph) -> List[BlastRadius]:
    """Blast radius for every key encrypting key.
