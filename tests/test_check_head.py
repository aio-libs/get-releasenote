import pytest

from get_releasenote import check_head


def test_check_head_ok():
    check_head("1.2.3", "refs/tags/1.2.3")


def test_check_head_with_v_prefix():
    check_head("1.2.3", "refs/tags/v1.2.3")


def test_check_head_not_a_tag():
    with pytest.raises(
        ValueError, match="Git head 'refs/heads/master' doesn't point at a tag"
    ):
        check_head("1.2.3", "refs/heads/master")


def test_check_head_version_mismatches():
    with pytest.raises(
        ValueError, match="Git tag 'v2.3.4' mismatches with version '1.2.3"
    ):
        check_head("1.2.3", "refs/tags/v2.3.4")
