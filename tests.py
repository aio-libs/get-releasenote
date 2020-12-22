import pathlib
from textwrap import dedent

import pytest

from get_releasenote import __version__, check_fix_issue, find_version, parse


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


def test_find_version_ambigous(root: pathlib.Path) -> None:
    with pytest.raises(ValueError, match="ambiguous"):
        find_version(root, "get_releasenote.py", "1.2.3")


def test_find_version_explicit(root: pathlib.Path) -> None:
    assert "1.2.3" == find_version(root, "", "1.2.3")


def test_find_version_from_file(root: pathlib.Path) -> None:
    assert __version__ == find_version(root, "get_releasenote.py", "")


def test_find_version_not_found(root: pathlib.Path) -> None:
    with pytest.raises(ValueError, match="Unable to determine version"):
        find_version(root, "tests.py", "")


##################


def test_parse_no_start_line() -> None:
    with pytest.raises(ValueError, match="Cannot find TOWNCRIER start mark"):
        parse(
            changes="text",
            version="1.2.3",
            name="",
            start_line=START_LINE,
            head_line="{name}{version} \\({date}\\)\n=====+\n?",
            fix_issue_regex="",
            fix_issue_repl="",
        )


def test_parse_no_head_line() -> None:
    CHANGES = dedent(
        f"""\
      {START_LINE}
      NO-VERSION
    """
    )
    with pytest.raises(ValueError, match="Cannot find TOWNCRIER version head mark"):
        parse(
            changes=CHANGES,
            version="1.2.3",
            name="",
            start_line=START_LINE,
            head_line="{name}{version} \\({date}\\)\n=====+\n?",
            fix_issue_regex="",
            fix_issue_repl="",
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
        parse(
            changes=CHANGES,
            version="1.2.3",
            name="",
            start_line=START_LINE,
            head_line="{name}{version} \\({date}\\)\n=====+\n?",
            fix_issue_regex="",
            fix_issue_repl="",
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
    ret = parse(
        changes=CHANGES,
        version="1.2.3",
        name="",
        start_line=START_LINE,
        head_line="{name}{version} \\({date}\\)\n=====+\n?",
        fix_issue_regex="",
        fix_issue_repl="",
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
    ret = parse(
        changes=CHANGES,
        version="1.2.3",
        name="",
        start_line=START_LINE,
        head_line="{name}{version} \\({date}\\)\n=====+\n?",
        fix_issue_regex="",
        fix_issue_repl="",
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
    ret = parse(
        changes=CHANGES,
        version="1.2.3",
        name="",
        start_line=START_LINE,
        head_line="{name}{version} \\({date}\\)\n=====+\n?",
        fix_issue_regex=(
            "\n?\\s*`#(\\d+) <https://github.com/aio-libs/aiohttp/issues/\\1>`_"
        ),
        fix_issue_repl=" (#\\1)",
    )
    assert ret == dedent(
        """\
      Features
      --------

      - Feature 1 (#4603)"""
    )
