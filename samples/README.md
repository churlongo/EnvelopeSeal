# Sample manifests

These two files are hand authored test vectors, not exported production key
material. They contain no real key bytes, only key ids, declared algorithms,
declared sizes, and declared dates. Nothing here can decrypt anything.

## healthy.manifest

A hierarchy that passes every check. One root, `root-hsm`, wraps two mid level
key encrypting keys, and each of those wraps two data keys. Every wrap protects
a key of equal or lower strength, so there is no inversion. There is no cycle.
No key is an orphan. Against the as-of date used in the README, 2026-09-02, no
rotation interval has lapsed. The root is marked with a rotation interval of 0,
meaning it is replaced by ceremony rather than on a schedule, so it is exempt.

## broken.manifest

Constructed to hold exactly one of every fault the tool detects, so the
validate output shows each finding code once or twice:

- inversion: `weak-wrapper` is RSA-OAEP 2048 (security level 112) and it wraps
  `dek-strong`, an AES-GCM 256 key (level 256).
- cycle: `loop-a` wraps `loop-b` and `loop-b` wraps `loop-a`.
- orphan: `lonely-kek` has no wrap edge in either direction. `dek-uncovered`
  also has no edges, so it is reported both as an orphan and as missing-wrap,
  which is correct: a data key with no wrap edge at all is both uncovered and
