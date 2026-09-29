"""Inject generated SEO across Core connector surfaces and verify."""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.core_client import PLATFORMS, probe_core, verify_seo, write_seo
from app.services.i18n_copy import locale_of, t
from app.services.odoo_inject import inject_product_aeo, inject_website_seo
from app.services.aeo_block import render_faq_html


def _surface_result(platform: str, write: Dict[str, Any], verify: Optional[Dict[str, Any]], core_up: bool) -> Dict[str, Any]:
    write_ok = bool(write.get("ok")) and core_up
    verify_ok = bool(verify and verify.get("ok")) and core_up
    if not core_up:
        write_status = "FAIL"
        verify_status = "FAIL"
        reason = "AEO Core :18642 unreachable — inject not performed. Generator does not fake success."
        customer_reason = "No se pudo publicar: la tienda no está disponible ahora. No se simuló un resultado correcto."
    else:
        write_status = "PASS" if write_ok else "FAIL"
        verify_status = "PASS" if verify_ok else "FAIL"
        reason = None
        customer_reason = None
        if not write_ok:
            reason = write.get("message") or write.get("error") or "write-seo did not succeed"
            customer_reason = "No se pudieron guardar los cambios en la tienda."
        elif not verify_ok:
            reason = (verify or {}).get("message") or (verify or {}).get("error") or "verify did not succeed"
            customer_reason = "Se intentó guardar, pero no pudimos comprobar que los cambios quedaron publicados."
    return {
        "platform": platform,
        "write": write_status,
        "verify": verify_status,
        "ok": write_ok and verify_ok,
        "reason": reason,
        "customer_reason": customer_reason,
        "write_detail": {
            "forwarded": write.get("forwarded"),
            "path": write.get("path"),
            "status_code": write.get("status_code"),
        },
        "verify_detail": {
            "forwarded": (verify or {}).get("forwarded"),
            "path": (verify or {}).get("path"),
            "status_code": (verify or {}).get("status_code"),
        } if verify else None,
    }


def _has_shop_access(conn: Dict[str, Any]) -> bool:
    if not isinstance(conn, dict):
        return False
    if conn.get("api_key") and (conn.get("username") or conn.get("url")):
        return True
    if conn.get("ws_key"):
        return True
    if conn.get("consumer_key") and conn.get("consumer_secret"):
        return True
    return False


async def inject_and_verify(
    seo: Dict[str, Any],
    connections: Optional[Dict[str, Any]] = None,
    target: Optional[str] = None,
    locale: Optional[str] = None,
) -> Dict[str, Any]:
    loc = locale_of(locale)
    core = await probe_core()
    core_up = bool(core.get("reachable"))
    connections = connections or {}
    usable = {
        (key or "").strip().lower(): value
        for key, value in connections.items()
        if (key or "").strip().lower() in PLATFORMS and _has_shop_access(value or {})
    }
    if not usable:
        skip_msg = t(loc, "inject.skip")
        return {
            "ok": False,
            "skipped": True,
            "step_complete": True,
            "injected": False,
            "core": core,
            "surfaces": [],
            "customer_message": skip_msg,
            "message": skip_msg,
        }
    requested = list(usable.keys())
    connections = usable
    surfaces = []
    for platform in requested:
        conn = connections.get(platform) or {}
        payload = {"connection": conn, "seo": seo, "target": target}
        if not core_up:
            write = {
                "ok": False,
                "forwarded": False,
                "message": core.get("message"),
            }
            verify = dict(write)
        else:
            write = await write_seo(platform, payload)
            verify = await verify_seo(platform, payload) if write.get("ok") else {
                "ok": False,
                "forwarded": write.get("forwarded"),
                "message": "verify skipped because write-seo failed",
            }
        surfaces.append(_surface_result(platform, write, verify, core_up))

    overall = core_up and all(s["ok"] for s in surfaces)
    if not overall:
        odoo_conn = connections.get("odoo") or {}
        if odoo_conn.get("api_key") and odoo_conn.get("url"):
            product_id = seo.get("product_id")
            faq = seo.get("faq") if isinstance(seo.get("faq"), list) else None
            schema = seo.get("schema") if isinstance(seo.get("schema"), dict) else None
            aeo_direct = None
            if product_id and (faq or seo.get("faq_html")):
                aeo_direct = inject_product_aeo(
                    odoo_conn,
                    int(product_id),
                    faq=faq,
                    schema=schema,
                    block_html=seo.get("faq_html") or render_faq_html(faq or [], schema),
                )
            direct = inject_website_seo(odoo_conn, seo, target)
            # SEO may fail when target is a product URL with no website.page; AEO alone can still pass.
            if aeo_direct and aeo_direct.get("ok") and not direct.get("ok"):
                combined_ok = True
                primary = aeo_direct
            else:
                combined_ok = bool(direct.get("ok")) and (aeo_direct is None or bool(aeo_direct.get("ok")))
                primary = direct
            surfaces = [
                {
                    "platform": "odoo",
                    "write": "PASS" if combined_ok else "FAIL",
                    "verify": "PASS" if combined_ok else "FAIL",
                    "ok": combined_ok,
                    "reason": None if combined_ok else (primary.get("message") or (aeo_direct or {}).get("message")),
                    "customer_reason": None if combined_ok else "No se pudieron guardar los cambios en Odoo.",
                    "write_detail": {
                        "mode": "odoo-xmlrpc",
                        "page_id": direct.get("page_id"),
                        "product_id": (aeo_direct or {}).get("product_id"),
                        "seo_pack": direct.get("pack"),
                        "aeo_pack": (aeo_direct or {}).get("pack"),
                        "aeo_detection": (aeo_direct or {}).get("detection"),
                    },
                    "verify_detail": {
                        "seo": direct.get("verify"),
                        "aeo": (aeo_direct or {}).get("verify"),
                    },
                }
            ]
            overall = combined_ok
            return {
                "ok": overall,
                "step_complete": True,
                "injected": overall,
                "core": core,
                "direct": direct,
                "aeo": aeo_direct,
                "surfaces": surfaces,
                "customer_message": (
                    "Los cambios se guardaron en Odoo Arkiphere."
                    if overall
                    else primary.get("message") or "No se pudo publicar en Odoo ahora. No se simuló un resultado correcto."
                ),
                "message": (
                    "Inject verified via Odoo XML-RPC."
                    if overall
                    else primary.get("message") or "Odoo XML-RPC inject failed. Success was not faked."
                ),
            }
    return {
        "ok": overall,
        "step_complete": True,
        "injected": overall,
        "core": core,
        "surfaces": surfaces,
        "customer_message": (
            "Los cambios se guardaron y se comprobaron en la tienda."
            if overall
            else "No se pudo publicar en la tienda ahora. No se simuló un resultado correcto."
        ),
        "message": (
            "Inject verified on all surfaces."
            if overall
            else "Inject/verify FAIL. Core down or a platform rejected the write. Success was not faked."
        ),
    }
