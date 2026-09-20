# FAQ

**Does EnvelopeSeal decrypt anything?**
No. It reads the manifest that describes the hierarchy and reasons about the
structure. No key material is required, which is why it is safe to run in CI.

**What is the blast radius?**
The set of keys reachable from a compromised KEK, computed over the wrapped
relationships in the manifest.

**Why is rotation order deterministic?**
So two plans diff cleanly and a review can see exactly what changed between
runs.
