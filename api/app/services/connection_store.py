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
    return {"connections": {}, "graph": {}, "apply": [], "changelog": [], "jobs": {}}


def _load() -> Dict[str, Any]:
    path = _data_dir()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                for key in ("connections", "graph", "apply", "changelog", "jobs"):
                    data.setdefault(key, {} if key in ("connections", "graph", "jobs") else [])
                if not isinstance(data["connections"], dict):
                    data["connections"] = {}
                if not isinstance(data["graph"], dict):
                    data["graph"] = {}
                if not isinstance(data.get("jobs"), dict):
                    data["jobs"] = {}
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


def _public_ark(ark: Any, connected: bool) -> Dict[str, Any]:
    if not isinstance(ark, dict):
        ark = {}
    msg = str(ark.get("message") or "")
    infra = bool(
        ark.get("xmlrpc")
        or str(ark.get("mode") or "").lower() in ("xmlrpc", "pending")
        or "xml-rpc" in msg.lower()
        or "xmlrpc" in msg.lower()
        or "no configurado" in msg.lower()
    )
    if connected and infra:
        return {
            "ok": True,
            "mode": "local",
            "sale_line_id": ark.get("sale_line_id"),
            "written": ark.get("written"),
            "message": None,
        }
    return {
        "ok": bool(ark.get("ok")) if "ok" in ark else connected,
        "mode": ark.get("mode"),
        "sale_line_id": ark.get("sale_line_id"),
        "written": ark.get("written"),
        "message": None if infra else (ark.get("message") or None),
    }


def public_view(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    platform = str(row.get("platform") or "").strip().lower() or None
    connected = bool(row.get("connected"))
    return {
        "license": row.get("license"),
        "sale_order_name": row.get("sale_order_name"),
        "platform": platform,
        "url": row.get("url"),
        "host": (row.get("host") or "").strip() or None,
        "database": row.get("database"),
        "username": row.get("username"),
        "has_secrets": bool(row.get("api_key_enc") or row.get("ws_key_enc") or row.get("consumer_secret_enc")),
        "connected": connected,
        "arkiphere": _public_ark(row.get("arkiphere"), connected),
        "schema_snapshot": row.get("schema_snapshot") or {},
        "updated_at": row.get("updated_at"),
        "recommendations": row.get("recommendations") or [],
    }


def _entry(license_key: str) -> Optional[Dict[str, Any]]:
    key = (license_key or "").strip()
    if not key:
        return None
    with _lock:
        return (_load().get("connections") or {}).get(key)


def _platforms(entry: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not isinstance(entry, dict):
        return {}
    raw = entry.get("platforms")
    if isinstance(raw, dict) and raw:
        out: Dict[str, Dict[str, Any]] = {}
        for name, row in raw.items():
            pid = str(name or "").strip().lower()
            if pid in PLATFORMS and isinstance(row, dict):
                out[pid] = dict(row)
                out[pid]["platform"] = pid
        return out
    pid = str(entry.get("platform") or "").strip().lower()
    if pid in PLATFORMS:
        return {pid: dict(entry)}
    return {}


def _pick_row(plats: Dict[str, Dict[str, Any]], platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
    pid = str(platform or "").strip().lower()
    if pid and pid in plats:
        return plats.get(pid)
    for name in PLATFORMS:
        row = plats.get(name)
        if row and row.get("connected"):
            return row
    return next(iter(plats.values()), None)


def public_platforms(license_key: str) -> Dict[str, Any]:
    plats = _platforms(_entry(license_key))
    views = {pid: public_view(row) for pid, row in plats.items()}
    current = _pick_row(plats)
    return {
        "platforms": views,
        "connected": any(bool(v and v.get("connected")) for v in views.values()),
        "connection": public_view(current),
    }


def get(license_key: str, platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return _pick_row(_platforms(_entry(license_key)), platform)


def remember_database(license_key: str, platform: str, database: str) -> None:
    name = (database or "").strip()
    pid = (platform or "").strip().lower()
    key = (license_key or "").strip()
    if not name or not key or pid not in PLATFORMS:
        return
    with _lock:
        data = _load()
        entry = (data.get("connections") or {}).get(key)
        if not isinstance(entry, dict):
            return
        plats = _platforms(entry)
        row = plats.get(pid)
        if not row or row.get("database"):
            return
        saved = dict(row)
        saved["database"] = name
        plats[pid] = saved
        data["connections"][key] = {
            "license": key,
            "sale_order_name": entry.get("sale_order_name") or saved.get("sale_order_name"),
            "platforms": plats,
        }
        _save(data)


def secrets_for(license_key: str, platform: Optional[str] = None) -> Dict[str, Any]:
    row = get(license_key, platform) or {}
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
        prev_entry = dict((data["connections"] or {}).get(key) or {})
        plats = _platforms(prev_entry)
        prev = dict(plats.get(platform) or {})
        row = {
            **prev,
            "license": key,
            "sale_order_name": payload.get("sale_order_name") or prev.get("sale_order_name") or prev_entry.get("sale_order_name"),
            "platform": platform,
            "url": payload.get("url") or prev.get("url"),
            "host": (payload.get("host") or prev.get("host") or "").strip() or None,
            "database": payload.get("database") or prev.get("database") or None,
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
        plats[platform] = row
        data["connections"][key] = {
            "license": key,
            "sale_order_name": row.get("sale_order_name"),
            "platforms": plats,
        }
        host = (payload.get("host") or "").strip()
        if host:
            data["graph"][f"{host}::{platform}"] = {
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


def revoke(
    license_key: str,
    sale_order_name: Optional[str] = None,
    platform: Optional[str] = None,
) -> Dict[str, Any]:
    key = (license_key or "").strip()
    pid = str(platform or "").strip().lower()
    with _lock:
        data = _load()
        removed = None
        remaining_connected = False
        entry_key = key
        if key and key in (data.get("connections") or {}):
            entry_key = key
        elif sale_order_name:
            for item_key, row in list((data.get("connections") or {}).items()):
                if row.get("sale_order_name") == sale_order_name or any(
                    isinstance(v, dict) and v.get("sale_order_name") == sale_order_name
                    for v in (row.get("platforms") or {}).values()
                ):
                    entry_key = item_key
                    break
        entry = dict((data.get("connections") or {}).get(entry_key) or {})
        plats = _platforms(entry)
        if pid and pid in plats:
            removed = plats.pop(pid)
            remaining_connected = any(bool(r.get("connected")) for r in plats.values())
            if plats:
                data["connections"][entry_key] = {
                    "license": entry_key,
                    "sale_order_name": entry.get("sale_order_name") or removed.get("sale_order_name"),
                    "platforms": plats,
                }
            else:
                data["connections"].pop(entry_key, None)
        elif not pid and entry:
            removed = _pick_row(plats) or entry
            remaining_connected = False
            data["connections"].pop(entry_key, None)
            plats = {}
        if removed:
            host_keys = [
                h
                for h, g in (data.get("graph") or {}).items()
                if g.get("license") == entry_key and (not pid or g.get("platform") == pid or h == g.get("url"))
            ]
            if pid:
                host_keys = [
                    h
                    for h, g in (data.get("graph") or {}).items()
                    if g.get("license") == entry_key and (g.get("platform") == pid or str(h).endswith(f"::{pid}"))
                ]
            for host in host_keys:
                data["graph"].pop(host, None)
            data["changelog"].append(
                {
                    "at": _now(),
                    "action": "revoke",
                    "license": (entry_key or "")[-6:],
                    "platform": pid or removed.get("platform"),
                    "sale_order_name": removed.get("sale_order_name"),
                }
            )
            data["changelog"] = data["changelog"][-200:]
            _save(data)
        return {
            "ok": True,
            "revoked": bool(removed),
            "license": entry_key or None,
            "platform": pid or (removed or {}).get("platform"),
            "remaining_connected": remaining_connected,
        }


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


def record_job(license_key: str, dossier: Dict[str, Any]) -> None:
    key = (license_key or "").strip()
    if not key:
        return
    from app.services.job_changelog import append_cycle
    from app.services.job_memory import append_archive, public_snapshot, remember_reading

    fingerprint = dossier.get("fingerprint") if isinstance(dossier.get("fingerprint"), dict) else {}
    slim = {
        "generated_at": dossier.get("generated_at"),
        "sale_order_name": dossier.get("sale_order_name"),
        "site_url": dossier.get("site_url"),
        "host": dossier.get("host"),
        "progress": dossier.get("progress"),
        "summary": dossier.get("summary"),
        "tree": dossier.get("tree"),
        "payload": dossier.get("payload") or {},
        "fingerprint": fingerprint,
        "changelog": dossier.get("changelog") or {},
    }
    with _lock:
        data = _load()
        jobs = data.get("jobs")
        if not isinstance(jobs, dict):
            jobs = {}
            data["jobs"] = jobs
        previous = jobs.get(key) if isinstance(jobs.get(key), dict) else {}
        cycles = append_cycle(previous.get("cycles"), fingerprint, _now())
        archives = append_archive(previous.get("archives"), public_snapshot(dossier))
        readings = remember_reading(previous.get("readings"), dossier.get("reading"))
        jobs[key] = {
            "updated_at": _now(),
            "cycles": cycles,
            "archives": archives,
            "readings": readings,
            **slim,
        }
        _save(data)


def get_job(license_key: str) -> Optional[Dict[str, Any]]:
    key = (license_key or "").strip()
    if not key:
        return None
    with _lock:
        jobs = _load().get("jobs") or {}
        row = jobs.get(key)
        return dict(row) if isinstance(row, dict) else None
