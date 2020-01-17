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


