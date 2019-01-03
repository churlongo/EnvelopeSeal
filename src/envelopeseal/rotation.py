"""Rotation interval and overdue calculation.

A key declares a rotation interval in days. The key is overdue when the as-of
date is later than its created date plus that interval. The as-of date is passed
in explicitly, never read from the wall clock, so a run is deterministic and two
runs of the same manifest against the same as-of date are byte identical.

A rotation interval of 0 means the key is exempt from rotation (for example a
hardware root that is replaced by ceremony, not by schedule). Such a key is
never overdue.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from envelopeseal.manifest import Key, Manifest


@dataclass(frozen=True)
class RotationStatus:
    """The rotation state of one key against an as-of date."""

    key_id: str
