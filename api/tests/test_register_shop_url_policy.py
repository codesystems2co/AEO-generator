import pytest
from fastapi import HTTPException

from app.services.site_guard import resolve_register_shop_url


def test_uses_order_line_shop_when_present():
    url = resolve_register_shop_url("http://woo.aeo.local:8081", None, None)
    assert url == "http://woo.aeo.local:8081"


def test_ignores_matching_typed_shop_when_line_set():
    url = resolve_register_shop_url(
        "http://woo.aeo.local:8081",
        "http://woo.aeo.local:8081",
        None,
    )
    assert url == "http://woo.aeo.local:8081"


def test_rejects_different_typed_shop_when_line_set():
    with pytest.raises(HTTPException) as exc:
        resolve_register_shop_url(
            "http://woo.aeo.local:8081",
            "http://odoo.aeo.local:8081",
            None,
        )
    assert exc.value.status_code == 400
    assert "línea del pedido" in str(exc.value.detail)


def test_allows_typed_shop_when_line_empty():
    url = resolve_register_shop_url(None, "http://shop.example:8081", None)
    assert url == "http://shop.example:8081"


def test_rejects_when_no_line_and_no_typed_shop():
    with pytest.raises(HTTPException) as exc:
        resolve_register_shop_url(None, None, None)
    assert exc.value.status_code == 400
    assert "no tiene URL de tienda" in str(exc.value.detail)
