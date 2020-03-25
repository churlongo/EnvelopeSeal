"""Compute findings and render line-oriented reports.

A finding is one problem with the hierarchy. Every finding has a stable code so
output diffs cleanly and callers can grep. The finding codes are:

    missing-wrap     a data key wrapped by no key encrypting key
    inversion        a weaker key wraps a stronger key
    cycle            a wrap cycle
    orphan           a key that protects nothing and is protected by nothing
    overdue          a key past its declared rotation interval

Findings are sorted by (code, subject) so the order never depends on manifest
line order. Rendering is pure text with one fact per line.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List

from envelopeseal import blast as blast_mod
from envelopeseal import graph as graph_mod
from envelopeseal import rotation as rotation_mod
from envelopeseal import strength as strength_mod
from envelopeseal.manifest import Manifest


@dataclass(frozen=True)
class Finding:
    """One problem with the hierarchy."""

    code: str
    subject: str
    detail: str


def _missing_wrap_findings(manifest: Manifest, graph: graph_mod.WrapGraph) -> List[Finding]:
    findings = []
    for key in manifest.keys.values():
        if key.is_data_key and not graph.wrappers_of(key.key_id):
            findings.append(
                Finding(
                    code="missing-wrap",
                    subject=key.key_id,
                    detail="data key is wrapped by no key encrypting key",
                )
            )
    return findings


def _inversion_findings(manifest: Manifest) -> List[Finding]:
    findings = []
    for wrap in manifest.wraps:
        wrapping = manifest.keys[wrap.wrapping_key]
        wrapped = manifest.keys[wrap.wrapped_key]
        if strength_mod.is_inversion(wrapping, wrapped):
            findings.append(
