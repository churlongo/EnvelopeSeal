# Architecture

EnvelopeSeal is an offline auditor for an envelope encryption key hierarchy. It
reads a text manifest that declares keys and the wrap edges between them, builds
a directed graph from those edges, and answers questions that only make sense at
the graph level. It prints plain text and exits with a status code. It holds no
key material, opens no sockets, and never reads the wall clock.

This document describes the modules that exist under `src/envelopeseal/`, how
data flows between them, and why the boundaries fall where they do.

## The shape of the design

The tool is a pipeline with a single direction of flow:

```
manifest file
  -> manifest.parse_file      (text  -> Manifest)
  -> graph.build_graph        (Manifest -> WrapGraph)
  -> strength / rotation / blast   (pure analysis over Manifest + WrapGraph)
  -> report.collect_findings / render_*   (analysis -> text)
  -> cli.main                 (arguments, exit codes, stdout/stderr)
```

Each stage depends only on the stages above it. `manifest` depends on nothing in
the package. `graph`, `strength`, and `rotation` depend on `manifest` only.
`blast` depends on `graph` and `manifest`. `report` depends on all of the
analysis modules. `cli` sits at the top and depends on everything below. There
are no cycles in the module dependency graph, which mirrors the property the
tool checks for in its input.

## What the tool touches, and what it does not

The tool reads exactly one thing: a manifest file, as UTF-8 text, passed as a
positional argument. It never touches key material. The manifest declares key
ids, roles, algorithm tokens, declared bit sizes, creation dates, and rotation
intervals. It carries no key bytes, no secrets, and no credentials. `manifest`
opens the file, reads it, and closes it. Nothing else in the package performs
IO except `cli`, which writes text to stdout and errors to stderr. There is no
network access, no key management service client, and no environment or clock
read anywhere in the analysis path. The as-of date used by rotation is always
passed in explicitly on the command line, never sampled from the system clock,
so a run is a pure function of its two inputs: the manifest text and the as-of
date.

## Modules

### `manifest.py` — parse the line-oriented key manifest

Owns the input format and nothing else. It defines the immutable `Key` and
`Wrap` records and the `Manifest` container that holds keys keyed by id plus
wrap edges in file order. `parse_text` walks the text line by line; blank lines
and `#` comment lines are skipped, and every other line must be a `key` record
of seven fields or a `wrap` record of three. Parsing is strict: a wrong field
count, an unknown role, a duplicate id, a non-integer size, a negative number,
or a malformed date raises `ManifestError` naming the line number. `parse_file`
is the only place the tool opens the manifest. Keeping the parser standalone,
with no dependency on the graph or analysis code, is what lets every other
module treat a `Manifest` as trusted, well-formed data.

### `graph.py` — the wrap graph and its three operations

The centre of the design. A `WrapGraph` is a directed graph whose nodes are key
ids and whose edges point from a wrapping key down to the key it wraps, so
following edges moves from key encrypting keys toward data keys. It stores
adjacency in both directions (`out_edges` and `in_edges`) so that both
"what does this key wrap" and "what wraps this key" are cheap. `build_graph`
constructs it from a `Manifest` and raises `GraphError` if any wrap edge names a
key id that was never declared. Every traversal sorts neighbours by id before
recursing, so the output is deterministic regardless of the order wrap records
appeared in the file. The three graph operations are described in their own
section below because they are the heart of the tool.

### `strength.py` — algorithm and size ordering, inversion test

