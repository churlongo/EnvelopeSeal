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
