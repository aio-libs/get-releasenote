import pytest

from get_releasenote import check_fix_issue


def test_check_fix_issue_ok1() -> None:
    check_fix_issue("s1", "s2")


def test_check_fix_issue_ok2() -> None:
    check_fix_issue("", "")


def test_check_fix_issue_fail1() -> None:
    with pytest.raises(ValueError):
        check_fix_issue("", "s2")


def test_check_fix_issue_fail2() -> None:
    with pytest.raises(ValueError):
        check_fix_issue("s1", "")
