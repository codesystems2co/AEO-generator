"""OAuth return URL must carry license/site from encoded state when memory is empty."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_gsc():
    root = Path(__file__).resolve().parents[1]
    cfg = types.ModuleType("app.config")

    class S:
        GOOGLE_CLIENT_ID = "x"
        GOOGLE_CLIENT_SECRET = "y"
        GOOGLE_REDIRECT_URI = "https://example/cb"
        GOOGLE_SA_JSON = None
        GOOGLE_SA_FILE = None
        GSC_SITE_URL = None
        FRONTEND_PUBLIC_URL = "http://ui"

        @property
        def google_oauth_configured(self):
            return True

        @property
        def google_sa_configured(self):
            return False

    cfg.settings = S()
    sys.modules["app"] = types.ModuleType("app")
    sys.modules["app.config"] = cfg
    services = types.ModuleType("app.services")
    services.__path__ = [str((root / "app" / "services").resolve())]
    sys.modules["app.services"] = services
    path = root / "app" / "services" / "google_search_service.py"
    spec = importlib.util.spec_from_file_location("app.services.google_search_service", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["app.services.google_search_service"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_oauth_return_query_from_state_without_memory():
    gsc = _load_gsc()
    gsc._oauth_ctx.clear()
    started = gsc.start_oauth(
        license_key="AEO-test",
        site="https://arkiphere.cloud",
        assistant="catalog",
    )
    state = started["state"]
    qs = gsc.oauth_return_query("connected", oauth_state=state)
    assert "license=AEO-test" in qs or "license=AEO" in qs
    assert "site=" in qs
    assert "assistant=catalog" in qs


if __name__ == "__main__":
    test_oauth_return_query_from_state_without_memory()
    print("ok")
