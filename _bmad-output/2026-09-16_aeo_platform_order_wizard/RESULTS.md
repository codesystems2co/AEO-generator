# RESULTS — AEO platform order → wizard (formal gate)

**Date:** 2026-09-16  
**Tester:** Software Tester (Grok Bot) for Alex Evolutia / AEO Platform  
**UI:** http://2.28.106.22:9012/  
**API LB:** http://2.28.106.22:8642/  
**Order:** S00245 (product 109, confirmed `sale`)  
**Site:** https://www.example.com  
**Key (redacted):** `AEO-EyXd…Aa0A`  
**Finished:** 2026-09-16 14:21 CEST (box/UTC 2026-09-16T12:21:11Z)

## Global: **PASS**

| Check | Result | Notes |
|-------|--------|-------|
| 1 Invalid license blocks | **PASS** | Live Playwright + shot 01 + live API |
| 2 Confirmed S00245 → wizard Google first | **PASS** | Key recovered; live consume + live UI + shots 02/03 |
| 3 API consume proxies Arkiphere | **PASS** | Code + live INVALID/allowed |
| 4 aeo_base / product 109 shop untouched; ports up | **PASS** | :9012/:8642 200; no shop/aeo_base edits in this gate |

## Per-check detail

### 1) Invalid blocked — PASS
- URL: `http://2.28.106.22:9012/?license=INVALID&site=https://www.example.com`
- Live Playwright: `Sin pedido` true; **Comenzar asistente** `disabled: true`
- Live API POST+GET `/api/entitlement/consume` → `allowed: false`, key INVALID
- Evidence: `screenshots/01-license-invalid-blocked.png` (md5 `bef29765a0fd4fcddb72390ac8f42f4d`); `live_playwright/live-01-invalid-blocked.png` (md5 `2c8cf1480bce6064780489325f22af51`)

### 2) Confirmed S00245 product 109 — PASS
- Key recovered from visual Read of shot 02 (OCR initially misread trailing `0` as `O`; live consume confirmed `…Aa0A`)
- Live POST consume → `allowed: true`, `sale_order_name: S00245`, `aeo_site_url: https://www.example.com`, `partner_id: 213`
- Live Playwright with recovered key: UI auto-enters wizard (gate skipped after consume) with badge **Pedido S00245**, stepper **1 Google → 2 AEO → 3 SEO**, **PASO 1 — GOOGLE SEARCH**, URL https://www.example.com
- Prior evidence shot 02: Pedido S00245, Comenzar enabled, confirmed message; shot 03: Google first wizard
- Soft note: live allowed landed directly on wizard (stronger than Comenzar click); gate card with Comenzar enabled is evidence-backed by shot 02
- Evidence: `screenshots/02-…` md5 `caf73355b4d042e9c225a472f4e98616`; `03-…` md5 `ae40872af7c4e1731acda82aab88afbf`; live-02/03 md5 `ef36815c128dd046e3ab7dd5b83f7f09` / `ef36815c128dd046e3ab7dd5b83f7f09` (same frame — auto-wizard)

### 3) Entitlement consume proxy — PASS
- Files on AEO_GENERATOR: `api/app/services/entitlement_service.py`, `api/app/routers/entitlement.py`
- `consume()` docstring: forwards to Arkiphere `/aeo/license/consume/http`; does **not** decide entitlement locally; not GitHub-only unlock
- `config.py`: `ARKIPHERE_CONSUME_URL = https://arkiphere.cloud`, `ODOO_URL = https://arkiphere.cloud`
- Router exposes GET+POST `/consume` → `entitlement.consume`
- Live INVALID → allowed false; live real key → allowed true S00245 (Arkiphere-backed)

### 4) aeo_base / product 109 shop untouched; live up — PASS
- Live HTTP: :9012 → 200, :8642 → 200 (k8s LB `aeo-generator-service` 9012, `aeo-generator-api-lb` 8642)
- This gate verified generator entitlement/UI only; no edits to `aeo_base` or shop product 109
- ARKIPHERE_CE local `aeo-odoo` / `aeo_dev` is bare Odoo 17 (no `sale_order`/`product_template`) — not the production shop; production consume path `https://arkiphere.cloud/aeo/license/consume/http` remains healthy via generator proxy
- Generator working tree changes are AEO-generator api/frontend only (no aeo_base path)

## Key recovery
- **Recovered:** yes (visual Read of `02-license-allowed-begin.png` + live consume confirmation)
- **Stored in RESULTS:** redacted only (`AEO-EyXd…Aa0A`)
- Full key used only in local live URL / API calls; not pasted in PM-facing plaintext beyond redaction

## Artifacts
- `RESULTS.md` (this file)
- `SCREEN_REVIEW.md`
- `RUN_SUMMARY.json`
- `ORDER_WIZARD_TESTED.md` (Tester formal gate note appended)
- `screenshots/`, `live_playwright/`
