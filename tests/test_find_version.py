import pathlib

import pytest

from get_releasenote import Context, DistInfo, analyze_dists, find_version

VERSION_FILE_TMPL = """\
from ._inner import Foo, Bar, spam_ham

{version_line}

__all__ = ("Foo", "Bar", "spam_ham")
"""


@pytest.fixture
def root() -> pathlib.Path:
    return pathlib.Path(__file__).parent


@pytest.fixture
def dist(root: pathlib.Path) -> DistInfo:
    ret = analyze_dists(root, "dist_ok")
    assert ret is not None
    return ret


@pytest.fixture
def ctx(tmp_path: pathlib.Path, dist: DistInfo) -> Context:
    return Context(tmp_path, dist)


def test_find_version_autodetected(ctx: Context) -> None:
    assert "0.0.7" == find_version(ctx, "", "")


def test_find_version_ambigous(ctx: Context) -> None:
    with pytest.raises(ValueError, match="ambiguous"):
        (ctx.root / "file.py").write_text(
            VERSION_FILE_TMPL.format(version_line="__version__='1.2.3'")
        )
        find_version(ctx, "file.py", "3.4.5")


def test_find_version_mismatch_with_autodetected(ctx: Context) -> None:
    with pytest.raises(ValueError, match="mismatches with autodetected "):
        find_version(ctx, "", "1.2.3")


def test_find_version_explicit(ctx: Context) -> None:
    assert "0.0.7" == find_version(ctx, "", "0.0.7")


def test_find_version_file_mismatch_with_autodetected(ctx: Context) -> None:
    with pytest.raises(ValueError, match="mismatches with autodetected "):
        (ctx.root / "file.py").write_text(
            VERSION_FILE_TMPL.format(version_line="__version__='1.2.3'")
        )
        find_version(ctx, "file.py", "")


def test_find___version___no_spaces(ctx: Context) -> None:
    (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(version_line="__version__='0.0.7'")
    )
    assert "0.0.7" == find_version(ctx, "file.py", "")


def test_find___version___from_file_single_quotes(ctx: Context) -> None:
    (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(version_line="__version__ = '0.0.7'")
    )
    assert "0.0.7" == find_version(ctx, "file.py", "")


def test_find___version___from_file_double_quotes(ctx: Context) -> None:
    (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(version_line='__version__ = "0.0.7"')
    )
    assert "0.0.7" == find_version(ctx, "file.py", "")


def test_find_version_from_file_single_quotes(ctx: Context) -> None:
    (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(version_line="version = '0.0.7'")
    )
    assert "0.0.7" == find_version(ctx, "file.py", "")


def test_find_version_from_file_double_quotes(ctx: Context) -> None:
    (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(version_line="version = '0.0.7'")
    )
    assert "0.0.7" == find_version(ctx, "file.py", "")


def test_find_version_not_found(ctx: Context) -> None:
    (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(version_line="not_a_version = '0.0.7'")
    )
    with pytest.raises(ValueError, match="Unable to determine version"):
        find_version(ctx, "file.py", "")


@pytest.mark.parametrize("quote", ["'", '"'])
def test_find_version_with_quote_in_comment(ctx: Context, quote: str) -> None:
    (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(
            version_line="version = '0.0.7'  # don't forget to update!"
        ).replace("'", quote)
    )
    assert "0.0.7" == find_version(ctx, "file.py", "")
