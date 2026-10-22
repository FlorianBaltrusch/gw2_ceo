"""Unit and API tests: no browser, no network (icons and API data are in
git), no server - Flask's test client talks to the app in-process.

    .venv/bin/pytest -q

The first build-catalogue test rebuilds the per-build cache (a few
seconds); everything else runs in milliseconds."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture(scope="session")
def client():
    from gw2ceo.app import app
    app.testing = True
    return app.test_client()


@pytest.fixture(scope="session")
def catalogue():
    """All build files, loaded once."""
    from gw2ceo import builds
    return builds.load_all()


def build_args(slug, **overrides):
    """The solver arguments of a build's optimizer link, optionally with
    query parameters replaced (mode="power", wvw="1" ...)."""
    import tomllib
    from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
    from gw2ceo import buildgear
    data = tomllib.load(open(ROOT / "builds" / f"{slug}.toml", "rb"))
    parts = urlsplit(data["optimizer"])
    query = {key: values[0] for key, values in parse_qs(parts.query, keep_blank_values=True).items()}
    query.update(overrides)
    link = urlunsplit(parts._replace(query=urlencode(query)))
    return buildgear.solver_args(link)[0]
