"""Local encrypted mirror of customer-typed connection details."""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config import settings

_lock = threading.Lock()
PLATFORMS = ("odoo", "prestashop", "woocommerce")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _data_dir() -> str:
    path = getattr(settings, "CONNECTION_STORE", None) or "/app/data/connections.json"
    folder = os.path.dirname(path) or "."
    os.makedirs(folder, exist_ok=True)
    return path


def _key_path() -> str:
    folder = os.path.dirname(_data_dir()) or "."
    return os.path.join(folder, "fernet.key")


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except Exception:
        return None
    env = (getattr(settings, "CONNECTION_FERNET_KEY", None) or "").strip()
    if env:
        raw = env.encode("utf-8") if isinstance(env, str) else env
        try:
            return Fernet(raw)
        except Exception:
            pass
    path = _key_path()
    if os.path.exists(path):
        return Fernet(open(path, "rb").read().strip())
    key = Fernet.generate_key()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(key)
    return Fernet(key)


def encrypt_secret(value: Optional[str]) -> Optional[str]:
    text = (value or "").strip()
    if not text:
        return None
    box = _fernet()
    if box is None:
        return text
    return box.encrypt(text.encode("utf-8")).decode("ascii")


def decrypt_secret(value: Optional[str]) -> Optional[str]:
    text = (value or "").strip()
    if not text:
        return None
    box = _fernet()
    if box is None:
        return text
    try:
        return box.decrypt(text.encode("ascii")).decode("utf-8")
    except Exception:
        return text


def _empty() -> Dict[str, Any]:
    return {"connections": {}, "graph": {}, "apply": [], "changelog": []}


def _load() -> Dict[str, Any]:
    path = _data_dir()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                for key in ("connections", "graph", "apply", "changelog"):
                    data.setdefault(key, {} if key != "changelog" and key != "apply" else [])
                if not isinstance(data["connections"], dict):
                    data["connections"] = {}
                if not isinstance(data["graph"], dict):
                    data["graph"] = {}
                if not isinstance(data["apply"], list):
                    data["apply"] = []
                if not isinstance(data["changelog"], list):
                    data["changelog"] = []
                return data
    except Exception:
        pass
    return _empty()


def _save(data: Dict[str, Any]) -> None:
    path = _data_dir()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def public_view(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    return {
        "license": row.get("license"),
        "sale_order_name": row.get("sale_order_name"),
        "platform": row.get("platform"),
        "url": row.get("url"),
        "database": row.get("database"),
        "username": row.get("username"),
        "has_secrets": bool(row.get("api_key_enc") or row.get("ws_key_enc") or row.get("consumer_secret_enc")),
        "connected": bool(row.get("connected")),
        "arkiphere": row.get("arkiphere") or {},
        "schema_snapshot": row.get("schema_snapshot") or {},
        "updated_at": row.get("updated_at"),
        "recommendations": row.get("recommendations") or [],
    }


def get(license_key: str) -> Optional[Dict[str, Any]]:
    key = (license_key or "").strip()
    if not key:
        return None
    with _lock:
        return (_load().get("connections") or {}).get(key)


def secrets_for(license_key: str) -> Dict[str, Any]:
    row = get(license_key) or {}
    return {
        "platform": row.get("platform"),
        "url": row.get("url"),
        "database": row.get("database"),
        "username": row.get("username"),
        "api_key": decrypt_secret(row.get("api_key_enc")),
        "ws_key": decrypt_secret(row.get("ws_key_enc")),
        "consumer_key": row.get("consumer_key"),
        "consumer_secret": decrypt_secret(row.get("consumer_secret_enc")),
        "target": row.get("target"),
    }


def upsert(license_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    key = (license_key or "").strip()
    if not key:
        raise ValueError("license required")
    platform = (payload.get("platform") or "").strip().lower()
    if platform not in PLATFORMS:
        raise ValueError(f"Unsupported platform. Use: {', '.join(PLATFORMS)}")
    with _lock:
        data = _load()
        prev = dict((data["connections"] or {}).get(key) or {})
        row = {
            **prev,
            "license": key,
            "sale_order_name": payload.get("sale_order_name") or prev.get("sale_order_name"),
            "platform": platform,
            "url": payload.get("url") or prev.get("url"),
            "database": payload.get("database") or None,
            "username": payload.get("username") or None,
            "consumer_key": payload.get("consumer_key") or None,
            "target": payload.get("target") or None,
            "connected": True,
            "updated_at": _now(),
            "arkiphere": payload.get("arkiphere") if "arkiphere" in payload else prev.get("arkiphere"),
            "schema_snapshot": payload.get("schema_snapshot") if "schema_snapshot" in payload else prev.get("schema_snapshot"),
            "recommendations": payload.get("recommendations") if "recommendations" in payload else prev.get("recommendations"),
        }
        if payload.get("api_key"):
            row["api_key_enc"] = encrypt_secret(payload.get("api_key"))
        if payload.get("ws_key"):
            row["ws_key_enc"] = encrypt_secret(payload.get("ws_key"))
        if payload.get("consumer_secret"):
            row["consumer_secret_enc"] = encrypt_secret(payload.get("consumer_secret"))
        data["connections"][key] = row
        host = (payload.get("host") or "").strip()
        if host:
            data["graph"][host] = {
                "license": key,
                "url": row.get("url"),
                "platform": platform,
                "snapshot": payload.get("schema_snapshot") or {},
                "updated_at": _now(),
            }
        data["changelog"].append(
            {
                "at": _now(),
                "action": "register",
                "license": key[-6:],
                "platform": platform,
                "sale_order_name": row.get("sale_order_name"),
            }
        )
        data["changelog"] = data["changelog"][-200:]
        _save(data)
    return public_view(row) or {}


def revoke(license_key: str, sale_order_name: Optional[str] = None) -> Dict[str, Any]:
    key = (license_key or "").strip()
    with _lock:
        data = _load()
        removed = None
        if key and key in (data.get("connections") or {}):
            removed = data["connections"].pop(key)
        elif sale_order_name:
            for item_key, row in list((data.get("connections") or {}).items()):
                if row.get("sale_order_name") == sale_order_name:
                    removed = data["connections"].pop(item_key)
                    key = item_key
                    break
        if removed:
            host_keys = [h for h, g in (data.get("graph") or {}).items() if g.get("license") == key]
            for host in host_keys:
                data["graph"].pop(host, None)
            data["changelog"].append(
                {
                    "at": _now(),
                    "action": "revoke",
                    "license": (key or "")[-6:],
                    "sale_order_name": removed.get("sale_order_name"),
                }
            )
            data["changelog"] = data["changelog"][-200:]
            _save(data)
        return {"ok": True, "revoked": bool(removed), "license": key or None}


def record_apply(license_key: str, result: Dict[str, Any]) -> None:
    with _lock:
        data = _load()
        data["apply"].append(
            {
                "at": _now(),
                "license": (license_key or "")[-6:],
                "ok": bool(result.get("ok")),
                "platform": result.get("platform"),
                "message": (result.get("message") or "")[:240],
            }
        )
        data["apply"] = data["apply"][-200:]
        _save(data)
