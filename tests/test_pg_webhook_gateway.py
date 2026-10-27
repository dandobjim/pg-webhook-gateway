from importlib.metadata import version

import app


def test_version_matches_package_metadata() -> None:
    assert app.__version__ == version("pg-webhook-gateway")
