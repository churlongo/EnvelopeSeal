"""Parse the key manifest.

The manifest is a small line-oriented text format so it diffs cleanly in git and
needs no third-party parser. It has two record kinds.

A key record:

    key <id> <role> <algorithm> <bits> <created> <rotation_days>

where role is one of "dek" (data key) or "kek" (key encrypting key),
algorithm is a token such as AES-GCM or RSA-OAEP, bits is an integer,
created is an ISO date (YYYY-MM-DD), and rotation_days is an integer number of
days after which the key is overdue (0 means the key never expires).

A wrap record:

    wrap <wrapping_key_id> <wrapped_key_id>

meaning wrapping_key_id encrypts (wraps) wrapped_key_id. A key encrypting key
may wrap other key encrypting keys or data keys.

Blank lines and lines beginning with "#" are ignored. Fields are separated by
runs of whitespace. Parsing is strict: a malformed line raises ManifestError
naming the line number.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import List


ROLE_DEK = "dek"
ROLE_KEK = "kek"
_ROLES = (ROLE_DEK, ROLE_KEK)


class ManifestError(ValueError):
    """Raised when the manifest text cannot be parsed."""


@dataclass(frozen=True)
class Key:
    """A single key declared in the manifest."""

    key_id: str
    role: str
    algorithm: str
    bits: int
    created: datetime.date
    rotation_days: int

    @property
    def is_data_key(self) -> bool:
        return self.role == ROLE_DEK

    @property
    def is_kek(self) -> bool:
        return self.role == ROLE_KEK


@dataclass(frozen=True)
class Wrap:
    """A directed wrap edge: wrapping_key protects wrapped_key."""

    wrapping_key: str
    wrapped_key: str


@dataclass
class Manifest:
    """A parsed manifest: keys keyed by id, plus wrap edges in file order."""

    keys: "dict[str, Key]" = field(default_factory=dict)
    wraps: List[Wrap] = field(default_factory=list)

    def key_ids(self) -> List[str]:
        return list(self.keys.keys())


def _parse_date(token: str, lineno: int) -> datetime.date:
    try:
        return datetime.date.fromisoformat(token)
    except ValueError as exc:
        raise ManifestError(
            f"line {lineno}: invalid date {token!r}, expected YYYY-MM-DD"
        ) from exc


def _parse_int(token: str, lineno: int, what: str) -> int:
    try:
        value = int(token)
    except ValueError as exc:
        raise ManifestError(
            f"line {lineno}: invalid {what} {token!r}, expected an integer"
        ) from exc
    if value < 0:
        raise ManifestError(f"line {lineno}: {what} may not be negative")
    return value


def parse_text(text: str) -> Manifest:
    """Parse manifest text into a Manifest, raising ManifestError on any fault."""

    manifest = Manifest()
    for raw_lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        kind = parts[0]
        if kind == "key":
            if len(parts) != 7:
                raise ManifestError(
                    f"line {raw_lineno}: key record needs 6 fields "
                    f"(id role algorithm bits created rotation_days), "
                    f"got {len(parts) - 1}"
                )
            _, key_id, role, algorithm, bits_s, created_s, rot_s = parts
            if role not in _ROLES:
                raise ManifestError(
                    f"line {raw_lineno}: unknown role {role!r}, "
                    f"expected one of {', '.join(_ROLES)}"
                )
            if key_id in manifest.keys:
                raise ManifestError(
                    f"line {raw_lineno}: duplicate key id {key_id!r}"
                )
            key = Key(
                key_id=key_id,
                role=role,
                algorithm=algorithm,
                bits=_parse_int(bits_s, raw_lineno, "bits"),
                created=_parse_date(created_s, raw_lineno),
                rotation_days=_parse_int(rot_s, raw_lineno, "rotation_days"),
            )
            manifest.keys[key_id] = key
        elif kind == "wrap":
            if len(parts) != 3:
                raise ManifestError(
                    f"line {raw_lineno}: wrap record needs 2 fields "
                    f"(wrapping_key wrapped_key), got {len(parts) - 1}"
                )
            manifest.wraps.append(Wrap(wrapping_key=parts[1], wrapped_key=parts[2]))
        else:
            raise ManifestError(
                f"line {raw_lineno}: unknown record kind {kind!r}, "
                f"expected 'key' or 'wrap'"
            )
    return manifest


def parse_file(path: str) -> Manifest:
    """Read and parse a manifest file (UTF-8, offline, no network)."""

    with open(path, "r", encoding="utf-8") as handle:
        return parse_text(handle.read())
