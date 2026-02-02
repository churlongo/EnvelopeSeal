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
# "symmetric" means the key size is the security level directly.
# "modulus" means an RSA or finite field modulus size, mapped below.
_SYMMETRIC = {"AES-GCM", "AES-KW", "AES-CBC", "CHACHA20-POLY1305"}
_MODULUS = {"RSA-OAEP", "RSA-PSS", "DH"}

# NIST SP 800-57 Part 1 Rev 5, Table 2: modulus size to comparable symmetric
# security strength. Keys are the declared modulus bits, values the level.
_MODULUS_LEVELS = {
    1024: 80,
    2048: 112,
    3072: 128,
    7680: 192,
    15360: 256,
}


class StrengthError(ValueError):
    """Raised when a key's algorithm or size cannot be scored."""


def security_level(key: Key) -> int:
    """Return the comparable security level in bits for a key.

    Raises StrengthError for an unknown algorithm or an unmapped modulus size,
    rather than guessing, because a silent wrong number would hide a real
    inversion.
    """

    algo = key.algorithm.upper()
    if algo in _SYMMETRIC:
        return key.bits
    if algo in _MODULUS:
        level = _MODULUS_LEVELS.get(key.bits)
        if level is None:
            raise StrengthError(
                f"key {key.key_id!r}: modulus size {key.bits} for {key.algorithm} "
                f"is not in the mapped set {sorted(_MODULUS_LEVELS)}"
            )
        return level
    raise StrengthError(
        f"key {key.key_id!r}: unknown algorithm {key.algorithm!r}"
    )


def is_inversion(wrapping: Key, wrapped: Key) -> bool:
    """True when wrapping is weaker than the key it protects."""

    return security_level(wrapping) < security_level(wrapped)


def describe(key: Key) -> str:
    """A short human string for a key's strength, for reports."""

    return f"{key.algorithm} {key.bits} (level {security_level(key)})"
