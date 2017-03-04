<div align="center">

<img src="docs/assets/logo.svg" alt="EnvelopeSeal wordmark: a closed envelope whose seal is a single filled square, next to the name EnvelopeSeal" width="240" />

# EnvelopeSeal

</div>

<table border="1">
<tr>
<td width="33%" valign="top">
<b>data key</b><br/>
A key that directly encrypts application data. Written <code>dek</code> in the
manifest. It is the thing you are ultimately protecting, and it is never meant
to sit unwrapped.
</td>
<td width="33%" valign="top">
<b>key encrypting key</b><br/>
A key whose only job is to wrap other keys. Written <code>kek</code> in the
manifest. A key encrypting key may wrap data keys or other key encrypting keys,
forming a hierarchy.
</td>
<td width="33%" valign="top">
<b>wrap</b><br/>
To encrypt one key under another. If A wraps B, then holding A lets you recover
B. An arrow in the graph points from the wrapping key down to the key it wraps.
</td>
</tr>
</table>

EnvelopeSeal is an offline auditor for an envelope encryption key hierarchy. You
give it a manifest that lists your keys and which key wraps which, and it checks
the hierarchy the way you would check a graph: are all the data keys actually
covered, is anything protected by something weaker than itself, are there loops,
is anything floating loose, and is anything past the date it should have been
rotated. It then reports blast radius, the number of data keys that fall if a
single key encrypting key is compromised.

It reads a manifest and prints text. It does not hold key material, it does not
talk to a key management service, and it opens no sockets. Everything it needs
is in the manifest you hand it and the as-of date you pass on the command line.

## Why this exists

Envelope encryption is easy to draw on a whiteboard and easy to get subtly wrong
in practice. A data key is wrapped by a key encrypting key, which may itself be
wrapped by another key encrypting key, up to some root. The diagram looks like a
tidy tree. The reality drifts. Someone adds a data key and forgets to wrap it.
Someone rotates a root and points a new key at an old one, closing a loop.
Someone provisions a 2048 bit RSA key to wrap a 256 bit symmetric key, quietly
capping the strength of everything below it. Someone leaves a key in the
manifest that nothing references any more.

None of these are visible from a single key's metadata. They are properties of
the graph. EnvelopeSeal loads the whole graph and asks the questions that only
make sense at the graph level, then prints the answers as plain lines you can
diff between runs.

The blast radius question is the one that changes behaviour. Every key
encrypting key has a number: how many data keys are downstream of it. That
number tells you which key to put in hardware, which to rotate first, and which
compromise would be a bad afternoon versus a company-ending event.

## The manifest format

The manifest is a line-oriented text file. It has two record kinds and ignores
blank lines and lines that start with `#`. Fields are separated by whitespace,
so you can align columns for readability.

A key record declares one key:

```
key <id> <role> <algorithm> <bits> <created> <rotation_days>
```

| Field           | Meaning                                                        |
| --------------- | -------------------------------------------------------------- |
| `id`            | Unique key identifier, any non-whitespace token.               |
| `role`          | `dek` for a data key or `kek` for a key encrypting key.        |
| `algorithm`     | Algorithm token, for example `AES-GCM` or `RSA-OAEP`.          |
| `bits`          | Declared key or modulus size in bits.                          |
| `created`       | ISO date `YYYY-MM-DD` the key was created.                     |
| `rotation_days` | Days until rotation is due. `0` means exempt, never overdue.   |

A wrap record declares one directed edge:

```
wrap <wrapping_key_id> <wrapped_key_id>
```

meaning the first key encrypts the second. Parsing is strict. A record with the
wrong field count, an unknown role, a duplicate id, or a malformed date raises an
error that names the line number, and the tool exits with code 2.

## Install and run

The package is pure standard library and targets Python 3.11. There are no
runtime dependencies to install. You can run it straight from the source tree by
putting `src` on the path:

```
PYTHONPATH=src python -m envelopeseal version
```

or install it so the `envelopeseal` command is on your path:

```
pip install .
envelopeseal version
```

The examples below use the `PYTHONPATH=src` form because that is how the output
in this README was captured.

## The checks

`validate` runs five checks over the manifest. Each produces zero or more
findings, and each finding carries a stable code so the output greps and diffs
cleanly.

| Code           | Question it answers                                             |
| -------------- | --------------------------------------------------------------- |
| `missing-wrap` | Is every data key wrapped by at least one key encrypting key?   |
| `inversion`    | Does any wrap protect a stronger key with a weaker one?         |
| `cycle`        | Is there a wrap loop, so a key transitively wraps itself?       |
| `orphan`       | Is any key attached to nothing in either direction?             |
| `overdue`      | Is any key past its created date plus its rotation interval?    |

A note on overlap: a data key with no wrap edge at all is reported both as
`missing-wrap` and as `orphan`, because it is genuinely both uncovered and
outside the hierarchy. The tool reports what is true rather than suppressing one
in favour of the other.

## Command reference

```
envelopeseal validate  <manifest> --as-of YYYY-MM-DD
envelopeseal blast     <manifest>
envelopeseal rotation  <manifest> --as-of YYYY-MM-DD
envelopeseal version
```

`validate` and `rotation` require `--as-of` because whether a key is overdue is a
function of a date, and the tool never reads the wall clock. Passing the date
explicitly is what makes a run reproducible: the same manifest and the same date
always produce the same bytes.

## Output format

Every report starts with a header line naming the subcommand, then a few count
lines, then one line per item. The `validate` header reports the key count, the
wrap count, the as-of date, and the finding count.

The command below was run against the healthy sample and captured verbatim:

```
$ PYTHONPATH=src python -m envelopeseal validate samples/healthy.manifest --as-of 2026-09-02
envelopeseal validate
keys 7
wraps 6
as-of 2026-09-02
findings 0
ok no findings
```

The same command against the broken sample reports every finding kind. This
output is captured verbatim:

```
$ PYTHONPATH=src python -m envelopeseal validate samples/broken.manifest --as-of 2026-09-02
envelopeseal validate
keys 8
wraps 4
as-of 2026-09-02
findings 6
cycle loop-a: wrap cycle: loop-a -> loop-b -> loop-a
inversion weak-wrapper->dek-strong: weak-wrapper (RSA-OAEP 2048 (level 112)) is weaker than dek-strong (AES-GCM 256 (level 256))
missing-wrap dek-uncovered: data key is wrapped by no key encrypting key
orphan dek-uncovered: key protects nothing and is protected by nothing
orphan lonely-kek: key protects nothing and is protected by nothing
overdue dek-stale: due 2026-01-31, 214 days overdue as of 2026-09-02
```

## A worked walkthrough

The healthy sample is a three level hierarchy. The diagram below is drawn from
that exact manifest, and the blast radius label on each key encrypting key is
the real number the tool printed.

![Wrap hierarchy for the healthy sample: root-hsm with blast radius 4 wraps mid-payments-kek and mid-telemetry-kek, each with blast radius 2, and those wrap two data keys each](docs/assets/wrap-hierarchy.svg)

Follow `dek-orders` up the tree. It is a data key, so it must be wrapped by
something: it is, by `mid-payments-kek`. That key encrypting key is in turn
wrapped by `root-hsm`. So two keys can recover `dek-orders`: the mid key
directly, and the root transitively. That is why `root-hsm` has a larger blast
radius than either mid key.

Now ask the blast question directly. This output is captured verbatim:

```
$ PYTHONPATH=src python -m envelopeseal blast samples/healthy.manifest
envelopeseal blast
keks 3
root-hsm blast 4 reaches dek-events,dek-invoices,dek-metrics,dek-orders
mid-payments-kek blast 2 reaches dek-invoices,dek-orders
mid-telemetry-kek blast 2 reaches dek-events,dek-metrics
```

`root-hsm` reaches all four data keys, so losing it exposes everything. Each mid
key reaches only its own two. The list is sorted widest first, so the key that
most deserves hardware protection is always the first line.

Finally the rotation view for the same manifest and date. This output is
captured verbatim:

```
$ PYTHONPATH=src python -m envelopeseal rotation samples/healthy.manifest --as-of 2026-09-02
envelopeseal rotation
as-of 2026-09-02
keys 7
overdue 0
dek-events created 2026-07-15 interval 90d due 2026-10-13 ok
dek-invoices created 2026-07-01 interval 90d due 2026-09-29 ok
dek-metrics created 2026-07-15 interval 90d due 2026-10-13 ok
dek-orders created 2026-07-01 interval 90d due 2026-09-29 ok
mid-payments-kek created 2026-02-01 interval 365d due 2027-02-01 ok
mid-telemetry-kek created 2026-02-01 interval 365d due 2027-02-01 ok
root-hsm created 2026-01-01 interval 0d due - exempt
```

`root-hsm` is `exempt` because its interval is `0`: it is replaced by ceremony,
not on a schedule. Every other key has a due date computed as created plus
interval, and all are still open as of the date given.

The version command reports the package version. Captured verbatim:

```
$ PYTHONPATH=src python -m envelopeseal version
envelopeseal 0.1.0
```

## Exit codes

| Code | Meaning                                                              |
| ---- | ------------------------------------------------------------------- |
| `0`  | Clean. No findings for `validate`, no overdue keys for `rotation`.  |
| `1`  | Findings present. `validate` found problems or `rotation` found overdue keys. |
| `2`  | Usage or input error: bad arguments, missing file, malformed manifest, unscorable key. |

`blast` and `version` always exit `0` on success because they report rather than
judge. `validate` exits `1` when any finding is present, which is what makes it
useful as a gate in continuous integration.

## The strength ordering

The inversion check needs to compare two keys and decide which is stronger. It
does this with a single comparable integer per key, called the security level,
in bits of work. The mapping is deliberately coarse and conservative, and it is
not a claim about any specific attack. It exists only so the tool can say, with
a consistent rule, that one key is weaker than another.

Symmetric algorithms (`AES-GCM`, `AES-KW`, `AES-CBC`, `CHACHA20-POLY1305`) use
their key size as the level directly, so `AES-GCM 256` is level 256.

Modulus based algorithms (`RSA-OAEP`, `RSA-PSS`, `DH`) map their modulus size to
a comparable symmetric level using NIST SP 800-57 Part 1 Revision 5, Table 2:

| Modulus bits | Security level |
| ------------ | -------------- |
| 1024         | 80             |
| 2048         | 112            |
| 3072         | 128            |
| 7680         | 192            |
| 15360        | 256            |

An inversion is any wrap where the wrapping key's level is strictly below the
wrapped key's level. In the broken sample, `weak-wrapper` is `RSA-OAEP 2048`,
level 112, and it wraps `dek-strong`, an `AES-GCM 256` key at level 256. The
wrapped key claims 256 bits of protection, but an attacker only needs to defeat
112 bits to reach it, so the claim is false and the tool flags it.

The edge case that makes this hard is that strength is not one dimensional
across algorithm families, and there is no universally agreed table. The tool
handles the ambiguity by refusing to guess: an unknown algorithm or an unmapped
modulus size raises an error and exits `2`, rather than scoring it as zero and
silently hiding a real inversion. If you use an algorithm the table does not
cover, the tool tells you instead of lying.

## How to read the report

Each finding is a line you can act on.

- `missing-wrap <dek>`: a data key has no key encrypting key. Decide which key
  encrypting key owns it and add a wrap record, or delete the data key if it is
  dead.
- `inversion <a>-><b>`: the wrap protects a stronger key with a weaker one.
  Either strengthen the wrapping key or accept that the inner key's effective
  strength is the outer key's, and stop claiming otherwise.
- `cycle <k> ...`: keys wrap each other in a loop, so none has a real root.
  Break the loop by pointing one edge at a genuine root instead.
- `orphan <k>`: the key touches nothing. If it is dead, remove it. If it is
  live, connect it to the hierarchy.
- `overdue <k>`: the key is past its rotation date. Rotate it, then update the
  manifest with the new created date.

The blast report is a priority list, not a finding list. Read it top down: the
first line is the key whose compromise hurts most, so it is the first key to
move into hardware or to rotate on the tightest schedule.

## Design decisions

**A text manifest, not JSON or YAML.** A line-oriented format diffs cleanly, has
no dependency, and needs no schema library. The alternative, a structured format,
would have been more familiar but would have pulled in a parser or forced the use
of the heavier standard library modules, and it would have diffed worse when a
single field changed. The cost is a hand written parser, which is small and fully
tested.

**An explicit as-of date, never the wall clock.** Rotation depends on a date. If
the tool read the current time, two runs of the same manifest on different days
would disagree, which breaks the deterministic output rule and makes the tool
useless as a diffable gate. Passing the date in costs one flag and buys
reproducibility. The alternative, defaulting to today, was rejected because a
default that changes silently is the opposite of deterministic.

**Refuse to score unknown algorithms.** The strength check could have treated an
unknown algorithm as some default level. That would let a run succeed while
hiding a real inversion behind a wrong number. Failing loudly with exit `2` is
noisier but honest, and the fix (extend the table) is obvious. Silence was the
rejected alternative.

**Report overlapping findings rather than deduplicating.** A data key with no
edges is both `missing-wrap` and `orphan`. Collapsing them into one would hide
information: the two codes trigger different fixes. Reporting both, sorted, keeps
each code meaning exactly one thing.

**Cycle safe reachability.** Blast radius is computed with a visited set, so it
returns a finite answer even when the graph has a cycle. The alternative, assuming
the graph is acyclic, would crash on exactly the broken input the tool exists to
diagnose.

## Repository layout

```
envelopeseal/
  README.md                     this file
  LICENSE                       MIT, the envelopeseal authors, 2026
  CHANGELOG.md                  release notes
  .gitignore                    ignores build and cache artefacts
  pyproject.toml                setuptools, src layout, console script
  src/envelopeseal/
    __init__.py                 package version
    __main__.py                 module entry point
    cli.py                      argparse subcommands and exit codes
    manifest.py                 parse the line-oriented key manifest
    graph.py                    build the wrap graph, find cycles, reach data keys
    strength.py                 algorithm and size ordering, inversion test
    rotation.py                 interval and overdue against an as-of date
    blast.py                    reachable data key counts per key encrypting key
    report.py                   collect findings and render every report
  tests/
    test_envelopeseal.py        unittest suite covering every module
  samples/
    healthy.manifest            a hierarchy that passes every check
    broken.manifest             one of every fault the tool detects
    README.md                   how each fixture was constructed
  docs/assets/
    logo.svg                    wordmark, envelope mark with a single seal
    wrap-hierarchy.svg          the real healthy graph with real blast counts
```

## Glossary

- **data key (dek)**: a key that encrypts application data directly.
- **key encrypting key (kek)**: a key whose job is to wrap other keys.
- **wrap**: to encrypt one key under another; the edge of the hierarchy.
- **blast radius**: the count of data keys reachable from a key encrypting key,
  which is the number compromised if that one key is.
- **inversion**: a wrap where the wrapping key is weaker than the wrapped key.
- **orphan**: a key with no wrap edge in either direction.
- **overdue**: a key whose created date plus rotation interval is before the
  as-of date.
- **security level**: the comparable integer strength the tool assigns a key.
- **as-of date**: the date rotation is evaluated against, passed explicitly.
- **exempt**: a key with rotation interval `0`, never considered overdue.

## Integration notes

Use `validate` as a gate. In continuous integration, run it against your checked
in manifest with a fixed as-of date, or with the pipeline's date if you want
rotation to fail the build as keys age:

```
PYTHONPATH=src python -m envelopeseal validate manifest.txt --as-of 2026-09-02
```

A non-zero exit fails the job. Exit `1` means the manifest has findings, exit `2`
means the manifest or invocation is broken.

Because output is line-oriented and deterministic, you can diff two runs to see
what changed between commits:

```
envelopeseal validate old.txt --as-of 2026-09-02 > old.out
envelopeseal validate new.txt --as-of 2026-09-02 > new.out
diff old.out new.out
```

A clean diff means the audit result did not change. A new `inversion` or `cycle`
line in the diff is a regression introduced by the commit.

## Verification

The test suite is stdlib `unittest`, run with:

```
PYTHONPATH=src python -m unittest discover -s tests -v
```

It runs 28 tests. They cover manifest parsing including every rejection path,
graph construction and the rejection of edges to unknown keys, cycle detection
and normalisation, orphan detection, cycle safe reachability, the strength
ordering for both algorithm families and both failure modes, rotation including
the exempt and overdue cases, blast radius counts and ordering, and the report
layer including determinism and the exact finding codes for both samples.

The final run reported:

```
Ran 28 tests in 0.003s

OK
```

Both SVG assets under `docs/assets/` parse as XML, carry a `viewBox`, a
`role="img"`, and a title and description, and contain no blur, drop shadow,
turbulence, or em dash.

## Limitations

- It audits declared metadata, not real key material. It cannot tell you that a
  key labelled `AES-GCM 256` is actually 256 bits of good randomness. It trusts
  the manifest.
- The strength ordering is coarse. It compares levels from a small table and
  does not model algorithm-specific weaknesses, quantum resistance, or mode
  misuse. Equal levels across families are treated as equal.
- There is no notion of key usage beyond wrap and data. It does not model signing
  keys, authentication keys, or key purpose restrictions.
- Rotation is a simple created-plus-interval calculation. It does not model grace
  periods, overlap windows during rotation, or staggered re-wrapping.
- It has no opinion on how many wrappers a data key should have. One is enough to
  clear `missing-wrap`; it does not check for a minimum redundancy.
- Blast radius counts reachable data keys. It does not weight them by
  sensitivity, because the manifest carries no sensitivity field.
- The manifest is trusted input. The tool does not authenticate it or verify a
  signature over it.

## Roadmap

These are directions, not commitments, and carry no dates.

- An optional minimum-wrapper check, so a data key wrapped by only one key
  encrypting key can be flagged when policy requires redundancy.
- A per-key sensitivity field so blast radius can be weighted, not just counted.
- A machine-readable output mode alongside the text mode, for pipelines that
  prefer to parse structured records.
- A wider strength table covering elliptic curve sizes.

## License

MIT. See [LICENSE](LICENSE). Copyright 2026 the EnvelopeSeal authors.

<!-- draft note 122 -->
