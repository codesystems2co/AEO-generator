"""Inject generated SEO across Core connector surfaces and verify."""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.core_client import PLATFORMS, probe_core, verify_seo, write_seo


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


async def inject_and_verify(
    seo: Dict[str, Any],
    connections: Optional[Dict[str, Any]] = None,
    target: Optional[str] = None,
) -> Dict[str, Any]:
    core = await probe_core()
    core_up = bool(core.get("reachable"))
    connections = connections or {}
    requested = []
    for key in connections:
        k = (key or "").strip().lower()
        if k in PLATFORMS:
            requested.append(k)
    platforms = requested or list(PLATFORMS)
    surfaces = []
    for platform in platforms:
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
