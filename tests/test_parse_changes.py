from textwrap import dedent

import pytest

from get_releasenote import _parse_changes

START_LINE = ".. towncrier release notes start"


def test_parse_no_start_line() -> None:
    with pytest.raises(ValueError, match="Cannot find TOWNCRIER start mark"):
        _parse_changes(
            changes="text",
            changes_file="CHANGES.rst",
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
            changes_file="CHANGES.rst",
            version="1.2.3",
            start_line=START_LINE,
            head_line="{version} \\({date}\\)\n=====+\n?",
            fix_issue_regex="",
            fix_issue_repl="",
            name="name",
        )


def test_parse_version_older() -> None:
    CHANGES = dedent(
        f"""\
      {START_LINE}

      1.2.4 (2020-12-16)
      ==================

    """
    )
    with pytest.raises(
        ValueError, match="The distribution version 1.2.3 is older than 1.2.4"
    ):
        _parse_changes(
            changes=CHANGES,
            changes_file="CHANGES.rst",
            version="1.2.3",
            start_line=START_LINE,
            head_line="{version} \\({date}\\)\n=====+\n?",
            fix_issue_regex="",
            fix_issue_repl="",
            name="name",
        )


def test_parse_version_younger() -> None:
    CHANGES = dedent(
        f"""\
      {START_LINE}

      1.2.4 (2020-12-16)
      ==================

    """
    )
    with pytest.raises(
        ValueError, match="The distribution version 1.2.5 is younger than 1.2.4"
    ):
        _parse_changes(
            changes=CHANGES,
            changes_file="CHANGES.rst",
            version="1.2.5",
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
        changes_file="CHANGES.rst",
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
        changes_file="CHANGES.rst",
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
        changes_file="CHANGES.rst",
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
        changes_file="CHANGES.rst",
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
