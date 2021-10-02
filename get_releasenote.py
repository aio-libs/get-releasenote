#!/usr/bin/env python

import os
import re
import sys
from pathlib import Path
from typing import Tuple

from distlib.wheel import Wheel

__version__ = "1.1.3"


def parse(
    *,
    changes: str,
    version: str,
    start_line: str,
    head_line: str,
    fix_issue_regex: str,
    fix_issue_repl: str,
) -> str:
    check_fix_issue(fix_issue_regex, fix_issue_repl)

    top, sep, msg = changes.partition(start_line)
    if not sep:
        raise ValueError(f"Cannot find TOWNCRIER start mark ({start_line!r})")

    msg = msg.strip()
    head_re = re.compile(
        head_line.format(
            version="(?P<version>[0-9][0-9.abcr]+)",
            date=r"\d+-\d+-\d+",
        ),
        re.MULTILINE,
    )
    match = head_re.match(msg)
    if match is None:
        raise ValueError(
            f"Cannot find TOWNCRIER version head mark ({head_re.pattern!r})"
        )
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

    if fix_issue_regex:
        msg = re.sub(fix_issue_regex, fix_issue_repl, msg)
    return msg.strip()


def analyze_wheels(dist_dir: Path, check_name: str) -> Tuple[str, str]:
    names = set()
    versions = set()
    for fname in dist_dir.glob("*.whl"):
        wheel = Wheel(str(fname))
        names.add(wheel.name)
        versions.add(wheel.version)
    if not names:
        raise ValueError(f"No wheels are found in {dist_dir}")
    if len(names) != 1:
        raise ValueError(f"Multiple distributions are found: {','.join(names)}")
    name = list(names)[0]
    if check_name and name != check_name:
        raise ValueError(
            f"name argument conflicts with autodected: {check_name} != {name}"
        )
    version = list(versions)[0]
    return name, version


def find_version(
    root: Path, version_file: str, version: str, name: str, dist_dir: str
) -> Tuple[str, str]:
    if not version and not version_file:
        if not dist_dir:
            raise ValueError("dist_dir is required for name and version autodetection")
        return analyze_wheels(root / dist_dir, name)
    if not name:
        raise ValueError(
            "name argument should be explicitly passes in non-autodetect mode"
        )
    if version:
        if version_file:
            raise ValueError("version and version_file arguments are ambiguous")
        return name, version
    fname = root / version_file
    txt = fname.read_text("utf-8")
    match = re.search(
        r"""
          __version__\s*=\s*"([^"]+)"|
          __version__\s*=\s*'([^']+)'
        """,
        txt,
        re.VERBOSE,
    )
    if not match:
        raise ValueError(f"Unable to determine version in {fname}")
    return name, match.group(1)


def check_fix_issue(fix_issue_regex: str, fix_issue_repl: str) -> None:
    if fix_issue_regex and not fix_issue_repl or not fix_issue_regex and fix_issue_repl:
        raise ValueError("fix_issue_regex and fix_issue_repl should be used together")


def main() -> int:
    root = Path(os.environ["GITHUB_WORKSPACE"])
    output_file = os.environ["INPUT_OUTPUT_FILE"]
    name, version = find_version(
        root,
        os.environ["INPUT_VERSION_FILE"],
        os.environ["INPUT_VERSION"],
        os.environ["INPUT_NAME"],
        os.environ["INPUT_DIST_DIR"],
    )
    start_line = os.environ["INPUT_START_LINE"]
    head_line = os.environ["INPUT_HEAD_LINE"]
    fix_issue_regex = os.environ["INPUT_FIX_ISSUE_REGEX"]
    fix_issue_repl = os.environ["INPUT_FIX_ISSUE_REPL"]
    changes = root / os.environ["INPUT_CHANGES_FILE"]
    note = parse(
        changes=changes.read_text("utf-8"),
        version=version,
        start_line=start_line,
        head_line=head_line,
        fix_issue_regex=fix_issue_regex,
        fix_issue_repl=fix_issue_repl,
    )
    print(f"::set-output name=version::{version}")
    print(f"::set-output name=name::{name}")
    is_prerelease = "a" in version or "b" in "version" or "r" in version
    print(f"::set-output name=prerelease::{str(is_prerelease).lower()}")
    (root / output_file).write_text(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
