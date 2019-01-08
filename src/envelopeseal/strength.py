"""Algorithm and key size ordering.

A wrapping key must be at least as strong as the key it protects. If a weaker
key wraps a stronger one, an attacker breaks the outer key at lower cost and
gains the inner key for free, so the declared inner strength is a fiction. That
is a strength inversion finding.

Strength here is a coarse, comparable integer we call the security level, in
bits of work. It is not a claim about any specific cryptanalytic result, only a
consistent ordering so the tool can say "this wrap protects a stronger key with
a weaker one". The mapping is intentionally conservative and documented in the
README. Symmetric algorithms use their key size directly. RSA and other modulus
based algorithms map their modulus size to an approximate symmetric equivalent
using the ordering published by NIST SP 800-57, rounded to the levels the tool
compares.
"""

from __future__ import annotations

from envelopeseal.manifest import Key


# Family of an algorithm decides how its declared bits map to a security level.
