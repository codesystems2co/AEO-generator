# Phase 3 — Wizard-only UI tested

**READY** — 2026-09-15

| Item | Value |
|------|--------|
| Open UI | http://2.28.106.22:9012/ |
| API | http://2.28.106.22:8642/docs |
| Images | `anyapp/aeo-generator-frontend:local` (stamp `phase3-2026-09-15-nav`), `anyapp/aeo-generator-api:local` (`phase3-2026-09-15`) |
| Core | `http://172.17.0.1:18642` — **unreachable** from this node |

Customer chrome is the 4-step wizard only. Loose tabs (Chat, Meta Tags, Keywords, …) stay behind **Herramientas**.

## Live checks

| Step | Action | Result | Evidence |
|------|--------|--------|----------|
| Default route | Open `/` | Wizard-only. No primary tab bar. **Atrás** disabled. **Continuar** disabled until the step is complete. | `screenshots/01-wizard-only.png` |
| Escape hatch | Click **Herramientas** | Advanced tabs appear. **Ocultar herramientas** returns to wizard-only. | `screenshots/02-herramientas.png` |
| Google Search | Click **Analizar y auto-corregir con Ollama** on `https://arkiphere.cloud` | Gaps calculated. Meta / H1 / JSON-LD **auto-corregido**. Loop `1/ollama`. Badge **Paso completo**. Continuar enables. Client consent remains a non-blocking GSC reminder. | `screenshots/03-google-autofix.png` |
| Atrás | Continuar → AEO, then **Atrás** | Returns to Google Search with autofix state kept. | `screenshots/03b-atras-from-aeo.png` |
| AEO pack | Continuar → **Generar pack AEO** | Pack + AEO tree (title, FAQ, H2). Continuar enables. | `screenshots/04-aeo-pack.png` |
| SEO pack | Continuar | Same wizard shell, tree resume + score (live run 80/100 B on capture). Packs are not primary tabs. | `screenshots/05-seo-pack.png` |
| Inject verify | Continuar → **Inyectar y verificar** | **INJECT FAIL**. odoo / prestashop / woocommerce write FAIL + verify FAIL. Message: Core :18642 unreachable — inject not performed. Success not faked. | `screenshots/06-inject-fail.png` |

## Core gap

AEO Core (`server.py` on `:18642`, default `CORE_BASE_URL=http://172.17.0.1:18642`) is down from this host and from the API pod. The generator proxies write+verify; it does **not** inject locally. Start Core on the node if inject PASS is required.

`injected: false` on `POST /api/wizard/inject-verify`.

## How to open

1. UI: http://2.28.106.22:9012/
2. Optional hatch: **Herramientas** (or `#herramientas`)
3. API docs: http://2.28.106.22:8642/docs

## Tester formal gate (2026-09-15 evening)

**PASS.** Evidence: `qa/evidence/2026-09-15_phase3_wizard_only/` (`RESULTS.md`, `SCREEN_REVIEW.md`).

Prior `03-google-autofix.png` and `03b-atras-from-aeo.png` were byte-identical — **recaptured**; now distinct. Inject FAIL with Core down confirmed (not UI FAIL).
