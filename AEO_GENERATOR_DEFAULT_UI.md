# Default UI source — Arkiphere Cloud “aeo” deploy card

**Found from:** Arkiphere Cloud home search “aeo” → `github:gwrxuk/aeo-generator` (Evaluate).

## Upstream product (has default UI)

| Item | Value |
|------|--------|
| GitHub | https://github.com/gwrxuk/AEO-generator |
| Medium write-up | https://medium.com/@gwrx2005/an-integrated-aeo-seo-geo-generator-with-natural-language-processing-and-external-api-integration-51602988c920 |
| Stack | FastAPI API **:8000** + React 18 / Vite UI **:5173** |
| Deploy | `docker-compose.yml` (API + frontend) |
| Tabs in default UI | MetaTags, Keywords, ContentAnalysis, AEO, SEOScore, Geo (+ NLP / URL / external) |
| Docker Hub image `gwrxuk/aeo-generator` | **Not found** on hub.docker.com v2 (object not found) — deploy from **GitHub** / compose, not a Hub image |

## What we built separately (light HTML — not this UI)

| Path | Role |
|------|------|
| `aeo-platform` Core `:18642` | Orchestrator + Odoo/Presta/Woo write-seo/verify |
| `/ui/connectors/` | Minimal light Conectores HTML |
| `/ui/onboarding/` | Domain checklist |
| `/ui/packages/` | Phase 2 GSC→AEO→SEO wizard HTML |

These are **not** the black/complete React UI from AEO-generator.

## Direction (Alex 2026-09-15)

Complete / overall **the default AEO-generator UI** (+ Arkiphere deploy path). Do **not** keep creating ad-hoc HTML UIs in crazy mode. Wire Core connectors / GSC / Ollama into that product UI instead of replacing it.

## Arkiphere Cloud entry

- Main site: https://arkiphere.cloud/
- Search “aeo” → Evaluate `github:gwrxuk/aeo-generator`

## Live My Space deploy (confirmed 2026-09-15)

| Item | Value |
|------|--------|
| Order / project | S00203 / repo 321 / thedeployer777-aeo-generator |
| Client IP | `2.28.106.22` |
| Public UI port | **`:9012`** (Vite React default UI proxied) |
| Live URL | http://2.28.106.22:9012/ |
| HTML title | `AEO / SEO Generator` |
| Evidence | Vite client + `/src/main.jsx`; `openapi.json` returns 200 on same host |
| Not this | Core `:18642` light HTML under `bmad/handoff/aeo-platform/ui/*` |

**Rule:** product UI work continues on this default generator UI, not new light HTML pages.
