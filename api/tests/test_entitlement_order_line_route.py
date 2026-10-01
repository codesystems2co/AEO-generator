from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import entitlement as entitlement_router


@patch("app.services.arkiphere_connection.fetch_order_line_public_sync")
def test_order_line_route_returns_line_shop(mock_fetch):
    app = FastAPI()
    app.include_router(entitlement_router.router, prefix="/api/entitlement")
    mock_fetch.return_value = {
        "ok": True,
        "mode": "http",
        "sale_order_name": "S00247",
        "sale_line_id": 351,
        "aeo_connect_platform": "woocommerce",
        "aeo_connect_shop_url": "http://woo.aeo.local:8081",
    }
    client = TestClient(app)
    response = client.get(
        "/api/entitlement/order-line",
        params={"key": "AEO-test", "sale_order_name": "S00247"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["aeo_connect_shop_url"] == "http://woo.aeo.local:8081"
    mock_fetch.assert_called_once_with("AEO-test", "S00247")
