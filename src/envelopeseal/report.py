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
                Finding(
                    code="inversion",
                    subject=f"{wrap.wrapping_key}->{wrap.wrapped_key}",
                    detail=(
                        f"{wrap.wrapping_key} ({strength_mod.describe(wrapping)}) "
                        f"is weaker than {wrap.wrapped_key} "
                        f"({strength_mod.describe(wrapped)})"
                    ),
                )
            )
    return findings


def _cycle_findings(graph: graph_mod.WrapGraph) -> List[Finding]:
    findings = []
    for cycle in graph_mod.find_cycles(graph):
        chain = " -> ".join(cycle + [cycle[0]])
        findings.append(
            Finding(
                code="cycle",
                subject=cycle[0],
                detail=f"wrap cycle: {chain}",
            )
        )
    return findings


def _orphan_findings(graph: graph_mod.WrapGraph) -> List[Finding]:
    return [
        Finding(
            code="orphan",
            subject=key_id,
            detail="key protects nothing and is protected by nothing",
        )
        for key_id in graph_mod.orphans(graph)
    ]


def _overdue_findings(manifest: Manifest, as_of: datetime.date) -> List[Finding]:
    findings = []
    for status in rotation_mod.overdue(manifest, as_of):
        findings.append(
            Finding(
                code="overdue",
                subject=status.key_id,
                detail=(
                    f"due {status.due_date.isoformat()}, "
                    f"{status.days_overdue} days overdue as of "
                    f"{status.as_of.isoformat()}"
                ),
            )
        )
    return findings


def collect_findings(manifest: Manifest, graph: graph_mod.WrapGraph, as_of: datetime.date) -> List[Finding]:
    """All findings, sorted by (code, subject) for deterministic output."""

    findings: List[Finding] = []
    findings += _missing_wrap_findings(manifest, graph)
    findings += _inversion_findings(manifest)
    findings += _cycle_findings(graph)
    findings += _orphan_findings(graph)
    findings += _overdue_findings(manifest, as_of)
    findings.sort(key=lambda f: (f.code, f.subject))
    return findings


