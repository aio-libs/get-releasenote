import pathlib
from textwrap import dedent

import pytest

from get_releasenote import (
    Context,
    DistInfo,
    _parse_changes,
    analyze_dists,
    check_fix_issue,
    find_version,
)


@pytest.fixture
def root() -> pathlib.Path:
    return pathlib.Path(__file__).parent


START_LINE = ".. towncrier release notes start"


#################


def test_check_fix_issue_ok1() -> None:
    assert check_fix_issue("s1", "s2") is None


def test_check_fix_issue_ok2() -> None:
    assert check_fix_issue("", "") is None


def test_check_fix_issue_fail1() -> None:
    with pytest.raises(ValueError):
        assert check_fix_issue("", "s2")


def test_check_fix_issue_fail2() -> None:
    with pytest.raises(ValueError):
        assert check_fix_issue("s1", "")


##################


@pytest.fixture
def dist(root: pathlib.Path) -> DistInfo:
    return analyze_dists(root, "dist_ok")


@pytest.fixture
def ctx(tmp_path: pathlib.Path, dist: DistInfo) -> Context:
    return Context(tmp_path, dist)


def test_find_version_autodetected(ctx: Context) -> None:
    assert "0.0.7" == find_version(ctx, "", "")


def test_find_version_ambigous(ctx: Context) -> None:
    with pytest.raises(ValueError, match="ambiguous"):
        (ctx.root / "file.py").write_text("__version__='1.2.3'")
        find_version(ctx, "file.py", "3.4.5")


def test_find_version_mismatch_with_autodetected(ctx: Context) -> None:
    with pytest.raises(ValueError, match="mismatches with autodetected "):
        find_version(ctx, "", "1.2.3")


def test_find_version_explicit(ctx: Context) -> None:
    assert "0.0.7" == find_version(ctx, "", "0.0.7")


def test_find_version_file_mismatch_with_autodetected(ctx: Context) -> None:
    with pytest.raises(ValueError, match="mismatches with autodetected "):
        (ctx.root / "file.py").write_text("__version__='1.2.3'")
        find_version(ctx, "file.py", "")


def test_find___version___no_spaces(ctx: Context) -> None:
    (ctx.root / "file.py").write_text("__version__='0.0.7'")
    assert "0.0.7" == find_version(ctx, "file.py", "")


def test_find___version___from_file_single_quotes(ctx: Context) -> None:
    (ctx.root / "file.py").write_text("__version__ = '0.0.7'")
    assert "0.0.7" == find_version(ctx, "file.py", "")


def test_find___version___from_file_double_quotes(ctx: Context) -> None:
    (ctx.root / "file.py").write_text('__version__ = "0.0.7"')
    assert "0.0.7" == find_version(ctx, "file.py", "")


def test_find_version_from_file_single_quotes(ctx: Context) -> None:
    (ctx.root / "file.py").write_text("version = '0.0.7'")
    assert "0.0.7" == find_version(ctx, "file.py", "")


def test_find_version_from_file_double_quotes(ctx: Context) -> None:
    (ctx.root / "file.py").write_text('version = "0.0.7"')
    assert "0.0.7" == find_version(ctx, "file.py", "")


def test_find_version_not_found(ctx: Context) -> None:
    (ctx.root / "file.py").write_text("not_a_version = '0.0.7'")
    with pytest.raises(ValueError, match="Unable to determine version"):
        find_version(ctx, "file.py", "")


##################


def test_parse_no_start_line() -> None:
    with pytest.raises(ValueError, match="Cannot find TOWNCRIER start mark"):
        _parse_changes(
            changes="text",
            version="1.2.3",
            start_line=START_LINE,
            head_line="{version} \\({date}\\)\n=====+\n?",
            fix_issue_regex="",
            fix_issue_repl="",
            name="name",
        )


def test_parse_no_head_line() -> None:
    CHANGES = dedent(
        f"""\
      {START_LINE}
      NO-VERSION
    """
    )
    with pytest.raises(ValueError, match="Cannot find TOWNCRIER version head mark"):
        _parse_changes(
            changes=CHANGES,
            version="1.2.3",
            start_line=START_LINE,
            head_line="{version} \\({date}\\)\n=====+\n?",
            fix_issue_regex="",
            fix_issue_repl="",
            name="name",
        )


def test_parse_version_mismatch() -> None:
    CHANGES = dedent(
        f"""\
      {START_LINE}

      1.2.4 (2020-12-16)
      ==================

    """
    )
    with pytest.raises(ValueError, match="Version check mismatch"):
        _parse_changes(
            changes=CHANGES,
            version="1.2.3",
            start_line=START_LINE,
            head_line="{version} \\({date}\\)\n=====+\n?",
            fix_issue_regex="",
            fix_issue_repl="",
            name="name",
        )


def test_parse_single_changes() -> None:
    CHANGES = dedent(
        f"""\
      Header
      {START_LINE}

      1.2.3 (2020-12-16)
      ==================

      Features
      --------

      - Feature 1 (#1024)

      - Feature 2 (#1025)

    """
    )
    ret = _parse_changes(
        changes=CHANGES,
        version="1.2.3",
        start_line=START_LINE,
        head_line="{version} \\({date}\\)\n=====+\n?",
        fix_issue_regex="",
        fix_issue_repl="",
        name="name",
    )
    assert ret == dedent(
        """\
      Features
      --------

      - Feature 1 (#1024)

      - Feature 2 (#1025)"""
    )


def test_parse_multi_changes() -> None:
    CHANGES = dedent(
        f"""\
      Header
      {START_LINE}

      1.2.3 (2020-12-16)
      ==================

      Features
      --------

      - Feature 1 (#1024)

      - Feature 2 (#1025)



      1.2.2 (2020-12-15)
      ==================

      Bugfixes
      --------
    """
    )
    ret = _parse_changes(
        changes=CHANGES,
        version="1.2.3",
        start_line=START_LINE,
        head_line="{version} \\({date}\\)\n=====+\n?",
        fix_issue_regex="",
        fix_issue_repl="",
        name="name",
    )
    assert ret == dedent(
        """\
      Features
      --------

      - Feature 1 (#1024)

      - Feature 2 (#1025)"""
    )


def test_parse_fix_issues() -> None:
    CHANGES = dedent(
        f"""\
      Header
      {START_LINE}

      1.2.3 (2020-12-16)
      ==================

      Features
      --------

      - Feature 1 `#4603 <https://github.com/aio-libs/aiohttp/issues/4603>`_
    """
    )
    ret = _parse_changes(
        changes=CHANGES,
        version="1.2.3",
        start_line=START_LINE,
        head_line="{version} \\({date}\\)\n=====+\n?",
        fix_issue_regex=(
            "\n?\\s*`#(\\d+) <https://github.com/aio-libs/aiohttp/issues/\\1>`_"
        ),
        fix_issue_repl=" (#\\1)",
        name="name",
    )
    assert ret == dedent(
        """\
      Features
      --------

      - Feature 1 (#4603)"""
    )


def test_parse_with_name() -> None:
    CHANGES = dedent(
        f"""\
      Header
      {START_LINE}

      Project 1.2.3 (2020-12-16)
      ==========================

      Features
      --------

      - Feature 1 (#1024)

    """
    )
    ret = _parse_changes(
        changes=CHANGES,
        version="1.2.3",
        start_line=START_LINE,
        head_line="Project {version} \\({date}\\)\n=====+\n?",
        fix_issue_regex="",
        fix_issue_repl="",
        name="name",
    )
    assert ret == dedent(
        """\
      Features
      --------

      - Feature 1 (#1024)"""
    )
