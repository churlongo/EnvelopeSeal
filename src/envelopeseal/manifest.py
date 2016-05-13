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
