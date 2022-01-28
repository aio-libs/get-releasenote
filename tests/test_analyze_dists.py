from pathlib import Path

import pytest

from get_releasenote import analyze_dists


@pytest.fixture
def assets() -> Path:
    here = Path(__file__)
    return here.parent


def test_anazyze_dists_ok(assets: Path) -> None:
    ret = analyze_dists(assets, "dist_ok")
    assert ret is not None
    assert str(ret.version) == "0.0.7"
    assert ret.name == "aioloop-proxy"
    assert ret.tarball_path.name == f"{ret.name}-{ret.version}"
