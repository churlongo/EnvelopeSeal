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
    created: datetime.date
    rotation_days: int
    due_date: "datetime.date | None"
    as_of: datetime.date

    @property
    def exempt(self) -> bool:
        return self.rotation_days == 0

    @property
    def overdue(self) -> bool:
        if self.exempt or self.due_date is None:
            return False
        return self.as_of > self.due_date

    @property
    def days_overdue(self) -> int:
        if not self.overdue or self.due_date is None:
            return 0
        return (self.as_of - self.due_date).days


def status_for(key: Key, as_of: datetime.date) -> RotationStatus:
    """Compute the rotation status of one key."""

    if key.rotation_days == 0:
        due = None
    else:
        due = key.created + datetime.timedelta(days=key.rotation_days)
    return RotationStatus(
        key_id=key.key_id,
        created=key.created,
        rotation_days=key.rotation_days,
        due_date=due,
        as_of=as_of,
    )


def statuses(manifest: Manifest, as_of: datetime.date) -> "list[RotationStatus]":
    """Rotation status for every key, sorted by key id."""

    return [
        status_for(manifest.keys[key_id], as_of)
        for key_id in sorted(manifest.keys)
    ]


def overdue(manifest: Manifest, as_of: datetime.date) -> "list[RotationStatus]":
    """Only the overdue keys, sorted by key id."""

