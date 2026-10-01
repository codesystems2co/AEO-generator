from app.services.arkiphere_connection import merge_public_line_fields


def test_merge_public_line_fields_adds_shop_url_from_line():
    base = {"allowed": True, "aeo_site_url": "https://arkiphere.cloud", "sale_order_name": "S00247"}
    line = {
        "ok": True,
        "aeo_connect_shop_url": "http://shop.example:8081",
        "aeo_connect_platform": "odoo",
        "sale_line_id": 351,
    }
    out = merge_public_line_fields(base, line)
    assert out["aeo_connect_shop_url"] == "http://shop.example:8081"
    assert out["aeo_site_url"] == "https://arkiphere.cloud"
    assert out["sale_line_id"] == 351


def test_merge_public_line_fields_ignores_failed_line():
    base = {"allowed": True, "aeo_site_url": "https://arkiphere.cloud"}
    assert merge_public_line_fields(base, {"ok": False}) == base
