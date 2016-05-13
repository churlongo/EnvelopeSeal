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
