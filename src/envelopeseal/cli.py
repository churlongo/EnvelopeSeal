"""Command line interface for envelopeseal.

Subcommands:

    validate   run every check and report findings; exit 1 if any
    blast      report blast radius per key encrypting key
    rotation   report rotation status per key
    version    print the version

Exit codes: 0 clean, 1 findings present, 2 usage or input error.
The as-of date is required for validate and rotation because rotation is a
function of a date and the tool never reads the wall clock.
"""

from __future__ import annotations

import argparse
import datetime
import sys
from typing import List, Optional

from envelopeseal import __version__
from envelopeseal import graph as graph_mod
from envelopeseal import report as report_mod
from envelopeseal import strength as strength_mod
from envelopeseal.manifest import ManifestError, parse_file


EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2


def _as_of(value: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"invalid as-of date {value!r}, expected YYYY-MM-DD"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envelopeseal",
        description="Audit an envelope encryption key hierarchy.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser(
        "validate", help="run every check and report findings"
    )
    p_validate.add_argument("manifest", help="path to the key manifest")
    p_validate.add_argument(
        "--as-of", type=_as_of, required=True, help="as-of date YYYY-MM-DD"
    )

    p_blast = sub.add_parser("blast", help="report blast radius per key encrypting key")
    p_blast.add_argument("manifest", help="path to the key manifest")

    p_rotation = sub.add_parser("rotation", help="report rotation status per key")
    p_rotation.add_argument("manifest", help="path to the key manifest")
    p_rotation.add_argument(
        "--as-of", type=_as_of, required=True, help="as-of date YYYY-MM-DD"
    )

    sub.add_parser("version", help="print the version")
    return parser


def _load(path: str):
    """Parse manifest and build graph, mapping domain errors to usage exits."""

    manifest = parse_file(path)
    graph = graph_mod.build_graph(manifest)
    # Score every key once so an unknown algorithm or size fails loudly and
    # early, rather than silently skipping an inversion check later.
    for key in manifest.keys.values():
        strength_mod.security_level(key)
    return manifest, graph


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print(f"envelopeseal {__version__}")
