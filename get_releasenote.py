#!/usr/bin/env python3

import dataclasses
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

from packaging.utils import parse_sdist_filename, parse_wheel_filename
from packaging.version import parse as parse_version


@dataclasses.dataclass
class DistInfo:
    version: str
    name: str
    tarball_path: Path


@dataclasses.dataclass
class Context:
    root: Path
    dist: Optional[DistInfo]
    version: str = ""

    def read_file(self, name: str) -> str:
        fname = self.root / name
        if not fname.exists():
            if self.dist is not None:
                fname = self.dist.tarball_path / name
        if not fname.exists():
            raise ValueError(f"file '{name}' doesn't exist")
        return fname.read_text("utf-8")


def analyze_dists(root: Path, dist_dir: str) -> Optional[DistInfo]:
    if not dist_dir:
        return None
    name = None
    version = None
    tarball_path = None
    dists = root / dist_dir
    for dist in dists.iterdir():
        if ".tar" in dist.suffixes:
            tmp_path = Path(tempfile.mkdtemp(suffix="tarfile"))
            shutil.unpack_archive(dist, tmp_path)
            tarball_path = tmp_path / dist.name
            # drop '.tar.gz' suffix
            tarball_path = tarball_path.with_suffix("").with_suffix("")
            assert tarball_path.is_dir()
            nam, ver = parse_sdist_filename(dist.name)
        else:
            nam, ver, build, tags = parse_wheel_filename(dist.name)
        if name is not None:
            assert name == nam, f"{nam} != {name} for {dist}"
        else:
            name = nam
        if version is not None:
            assert version == ver, f"{ver} != {version} for {dist}"
        else:
            version = ver
    return DistInfo(str(version), name, tarball_path)


def parse_changes(
    ctx: Context,
    *,
    changes_file: str,
    start_line: str,
    head_line: str,
    fix_issue_regex: str,
    fix_issue_repl: str,
    name: Optional[str],
) -> str:
    check_fix_issue(fix_issue_regex, fix_issue_repl)
    changes = ctx.read_file(changes_file)

    if not name:
        # take name from dict if not set
        if ctx.dist is not None:
            name = ctx.dist.name

    return _parse_changes(
        changes=changes,
        changes_file=changes_file,
        version=ctx.version,
        start_line=start_line,
        head_line=head_line,
        fix_issue_regex=fix_issue_regex,
        fix_issue_repl=fix_issue_repl,
    )


def _parse_changes(
    *,
    changes: str,
    changes_file: str,
    version: str,
    start_line: str,
    head_line: str,
    fix_issue_regex: str,
    fix_issue_repl: str,
    name: Optional[str],
) -> str:
    top, sep, msg = changes.partition(start_line)
    if not sep:
        raise ValueError(
            f"Cannot find TOWNCRIER start mark ({start_line!r}) "
            "in file '{changes_file}'"
        )

    msg = msg.strip()
    head_re = re.compile(
        head_line.format(
            version=r"(?P<version>[0-9][0-9.abcr]+(\.post[0-9]+)?)",
            date=r"\d+-\d+-\d+",
            name=name,
        ),
        re.MULTILINE,
    )
    match = head_re.match(msg)
    if match is None:
        raise ValueError(
            f"Cannot find TOWNCRIER version head mark ({head_re.pattern!r}) "
            f"in file '{changes_file}'"
        )
    found_version = match.group("version")
    check_changes_version(version, found_version, changes_file)

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


def check_changes_version(
    declared_version: str, found_version: str, changes_file: str
) -> None:
    if declared_version == found_version:
        return
    dver = parse_version(declared_version)
    fver = parse_version(found_version)

    if dver < fver:
        raise ValueError(
            f"The distribution version {dver} is older than "
            f"{fver} (from '{changes_file}').\n"
            "Hint: push git tag with the latest version."
        )

    else:
        raise ValueError(
            f"The distribution version {dver} is younger than "
            f"{fver} (from '{changes_file}').\n"
            "Hint: run 'towncrier' again."
        )


VERSION_RE = re.compile(
    "^{version} *= *{spec}".format(
        version="(?:__version__|version)",
        spec=r"""(['"])([^\1]+)\1""",
    )
)


def find_version(ctx: Context, version_file: str, version: str) -> str:
    if not version and not version_file:
        if not ctx.dist:
            raise ValueError("No one of 'dist', 'version', 'version_file' is set")
        return ctx.dist.version
    if version:
        if version_file:
            raise ValueError("version and version_file arguments are ambiguous")
        if ctx.dist and version != ctx.dist.version:
            raise ValueError(
                f"version {version} mismatches " f"with autodetected {ctx.dist.version}"
            )
        return version
    txt = ctx.read_file(version_file)
    match = VERSION_RE.match(txt)
    if match:
        ret = match.group(2)
        if ctx.dist and ret != ctx.dist.version:
            raise ValueError(
                f"version {ret} from file {version_file} "
                f"mismatches with autodetected {ctx.dist.version}"
            )
        return ret
    else:
        raise ValueError(f"Unable to determine version in file '{version_file}'")


def check_fix_issue(fix_issue_regex: str, fix_issue_repl: str) -> None:
    if fix_issue_regex and not fix_issue_repl or not fix_issue_regex and fix_issue_repl:
        raise ValueError("fix_issue_regex and fix_issue_repl should be used together")


def check_head(version: str, head: Optional[str]) -> None:
    if not head:
        return
    PRE = "refs/tags/"
    if not head.startswith(PRE):
        raise ValueError(f"Git head '{head}' doesn't point at a tag")
    tag = head[len(PRE) :]
    if tag != version and tag != "v" + version:
        raise ValueError(f"Git tag '{tag}' mismatches with version '{version}'")


def main() -> int:
    root = Path.cwd()
    info = analyze_dists(root, os.environ["INPUT_DIST_DIR"])
    ctx = Context(root, info)
    ctx.version = find_version(
        ctx,
        os.environ["INPUT_VERSION_FILE"],
        os.environ["INPUT_VERSION"],
    )
    version = parse_version(ctx.version)
    check_head(ctx.version, os.environ["INPUT_CHECK_REF"])
    note = parse_changes(
        ctx,
        changes_file=os.environ["INPUT_CHANGES_FILE"],
        start_line=os.environ["INPUT_START_LINE"],
        head_line=os.environ["INPUT_HEAD_LINE"],
        fix_issue_regex=os.environ["INPUT_FIX_ISSUE_REGEX"],
        fix_issue_repl=os.environ["INPUT_FIX_ISSUE_REPL"],
        name=os.environ["INPUT_NAME"],
    )
    print(f"::set-output name=version::{ctx.version}")
    is_prerelease = version.is_prerelease
    print(f"::set-output name=prerelease::{str(is_prerelease).lower()}")
    is_devrelease = version.is_devrelease
    print(f"::set-output name=devrelease::{str(is_devrelease).lower()}")
    output_file = os.environ["INPUT_OUTPUT_FILE"]
    (root / output_file).write_text(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
