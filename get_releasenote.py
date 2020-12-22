#!/usr/bin/env python

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional


def parse(
    changes: str,
    version: str,
    *,
    name: Optional[str] = None,
    start_line: str = ".. towncrier release notes start",
    head_line: str = r"{name}(?P<version>[0-9][0-9.abcr]+)\s+\(\d+-\d+-\d+\)\n====+\n",
    fix_issue: str = "",
) -> str:
    top, sep, msg = changes.partition(start_line)
    if not sep:
        raise ValueError(f"Cannot find TOWNCRIER start mark ({start_line!a})")
    msg = msg.strip()
    if name:
        name = re.escape(name) + r"\s+"
    else:
        name = ""
    head_re = re.compile(head_line.format(name=name))
    match = head_re.match(msg)
    if match is None:
        raise ValueError(f"Cannot find TOWNCRIER version head mark ({head_re!a})")
    found_version = match.group("version")
    if version != found_version:
        raise ValueError(f"Version check mismatch: {version} != {found_version}")

    match2 = head_re.search(msg, match.end())
    if match2 is not None:
        # There are older release records
        msg = msg[match.end() : match2.start()]
    else:
        # There is the only release record
        msg = msg[match.end() :]

    if fix_issue:
        patt, repl = fix_issue
        msg = re.sub(patt, repl, msg)
    return msg


def read_version(fname: Path) -> str:
    txt = fname.read_text("utf-8")
    try:
        return re.findall(r'^__version__ = "([^"]+)"\r?$', txt, re.M)[0]
    except IndexError:
        raise RuntimeError("Unable to determine version.")


def main(argv: List[str]) -> int:
    root = Path(__file__).parent.parent
    parser = argparse.ArgumentParser(description="Release notes extractor")
    parser.add_argument(
        "--version", help="Checked version (fetched from aiohttp/__init__.py by default"
    )
    args = parser.parse_args(argv)
    version = args.version
    if version is None:
        version = read_version(root / "aiohttp" / "__init__.py")
    changes = root / "CHANGES.rst"
    print(
        parse(
            changes.read_text("utf-8"),
            version,
            fix_issue=(
                r"\n?\s*`#(\d+) <https://github.com/aio-libs/aiohttp/issues/\1>`_",
                r" (#\1)",
            ),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
