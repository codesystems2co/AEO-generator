"""Revoke must only remove the requested platform."""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import types
from pathlib import Path


def test_revoke_only_current_platform():
    root = Path(__file__).resolve().parents[1]
    tmpdir = tempfile.mkdtemp()
    cfg = types.ModuleType("app.config")

    class S:
        CONNECTION_STORE = os.path.join(tmpdir, "connections.json")
        CONNECTION_FERNET_KEY = ""

    cfg.settings = S()
    app_pkg = types.ModuleType("app")
    app_pkg.__path__ = [str((root / "app").resolve())]
    sys.modules["app"] = app_pkg
    sys.modules["app.config"] = cfg
    services = types.ModuleType("app.services")
    services.__path__ = [str((root / "app" / "services").resolve())]
    sys.modules["app.services"] = services

    path = root / "app" / "services" / "connection_store.py"
    spec = importlib.util.spec_from_file_location("app.services.connection_store", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["app.services.connection_store"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    lic = "AEO-UNIT-REVOKE"
    mod.upsert(
        lic,
        {
            "platform": "odoo",
            "url": "https://shop.test",
            "username": "admin",
            "api_key": "secret",
            "host": "shop.test",
            "sale_order_name": "S1",
        },
    )
    mod.upsert(
        lic,
        {
            "platform": "woocommerce",
            "url": "https://shop.test",
            "consumer_key": "ck",
            "consumer_secret": "cs",
            "host": "shop.test",
            "sale_order_name": "S1",
        },
    )
    out = mod.revoke(lic, sale_order_name="S1", platform="woocommerce")
    assert out["revoked"] is True
    assert out["remaining_connected"] is True
    pack = mod.public_platforms(lic)
    assert "woocommerce" not in pack["platforms"]
    assert pack["platforms"]["odoo"]["connected"] is True


if __name__ == "__main__":
    test_revoke_only_current_platform()
    print("ok")
