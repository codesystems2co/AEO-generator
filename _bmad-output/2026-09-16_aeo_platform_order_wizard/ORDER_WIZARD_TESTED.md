# AEO platform order → wizard (generator)

**READY** — 2026-09-16

| Item | Value |
|------|--------|
| Open UI | http://2.28.106.22:9012/?license=AEO-…&site=https%3A%2F%2Fwww.example.com |
| Order | **S00245** (product 109, confirmed `sale`, 0 €) |
| Site | `https://www.example.com` (host `www.example.com`) |
| Product | Search Engine Optimizator |
| Consume | `POST /api/entitlement/consume` → Arkiphere `/aeo/license/consume/http` |

The generator does not decide entitlement. It forwards the activation key to Arkiphere. Packs do not start until `allowed: true`. No GitHub OAuth required to unlock. No payment code.

## Consume JSON (key redacted)

Invalid:

```json
{"allowed": false, "key": "INVALID", "sale_order_name": null, "aeo_site_url": null, "partner_id": null}
```

Confirmed product 109:

```json
{
  "allowed": true,
  "key": "AEO-EyXd…Aa0A",
  "sale_order_name": "S00245",
  "aeo_site_url": "https://www.example.com",
  "partner_id": 213,
  "open_url": "http://2.28.106.22:9012/?license=AEO-…&site=https%3A%2F%2Fwww.example.com"
}
```

## Live checks

| Step | Action | Result | Evidence |
|------|--------|--------|----------|
| Invalid key | `?license=INVALID&site=https://www.example.com` | **Sin pedido**. Clave + sitio filled. **Comenzar asistente** disabled. No packs. | `screenshots/01-license-invalid-blocked.png` |
| Open AEO | Real key + site from confirmed S00245 | Consume `allowed: true`. Fields filled. **Comenzar asistente** enabled. | `screenshots/02-license-allowed-begin.png` |
| First step | Begin / Open AEO | Wizard **Google → AEO → SEO**. Paso 1 Google Search, URL `https://www.example.com`, badge **Pedido S00245**. | `screenshots/03-wizard-google-first.png` |

## How to open

1. Invalid: http://2.28.106.22:9012/?license=INVALID&site=https://www.example.com
2. Confirmed: Open AEO from Arkiphere S00245 (or the `open_url` from consume)

## Tester formal gate (2026-09-16)

**Global: PASS** — Software Tester (Grok Bot).

| Check | Result |
|-------|--------|
| 1 Invalid → Sin pedido / Comenzar disabled (live Playwright + shot 01) | PASS |
| 2 S00245 product 109 → consume allowed → wizard Google→AEO→SEO (key recovered; live + shots 02/03) | PASS |
| 3 POST/GET `/api/entitlement/consume` → Arkiphere `/aeo/license/consume/http` (code + live) | PASS |
| 4 aeo_base / product 109 shop untouched; :9012/:8642 up | PASS |

Key recovered for live allowed path; RESULTS/PM text uses redacted `AEO-EyXd…Aa0A` only.
Deliverables: `RESULTS.md`, `SCREEN_REVIEW.md`, `RUN_SUMMARY.json`, `live_playwright/`.
