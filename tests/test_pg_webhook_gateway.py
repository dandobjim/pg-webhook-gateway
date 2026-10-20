from importlib.metadata import version

import pg_webhook_gateway


def test_version_matches_package_metadata() -> None:
    assert pg_webhook_gateway.__version__ == version("pg-webhook-gateway")
