n# Cursor Agent — Complete default AEO-generator UI (NOT light HTML)

## Context
Alex confirmed the product UI is the **live default** React/Vite app from `github:gwrxuk/AEO-generator`, already running on Arkiphere My Space:

| Item | Value |
|------|--------|
| Live URL | http://2.28.106.22:9012/ |
| Title | AEO / SEO Generator |
| My Space | thedeployer777-aeo-generator / S00203 / repo 321 |
| Upstream | https://github.com/gwrxuk/AEO-generator |
| Stack | FastAPI :8000 + React/Vite :5173 (proxied on client :9012) |

**STOP** creating or extending light HTML under `bmad/handoff/aeo-platform/ui/connectors|onboarding|packages`. Those stay as Core helpers only.

## Workspace rule (critical)
- **One** Cursor SSH session only for this host.
- Develop against the **aeo-generator** deploy/workspace (My Space / repo 321), **not** the `18.0` addons tree and **not** inventing new `aeo-platform/ui/*` pages.
- If you only have `aeo-platform [SSH: arkiphere_ce]` open, do not open a second window; either work files reachable from that session that belong to generator, or switch that single window to the generator project — never two SSH windows on arkiphere_ce.

## Goal
Complete / extend the **default generator UI** so it can deliver the full Arkiphere package:

1. Keep existing tabs (MetaTags, Keywords, ContentAnalysis, AEO, SEOScore, Geo, NLP, URL, external).
2. Add integration surfaces (same React UI, same design language — dark complete UI):
   - **Google Search** readiness + client consent/OAuth path (or clear SA vs OAuth modes)
   - **Ollama** pack generation (AEO + SEO) with human-readable **tree list resume**
   - **Connectors** write/verify to Odoo / PrestaShop / WooCommerce via AEO Core `:18642` APIs
   - **Step wizard**: Google Search → AEO → SEO (guided)
3. Wire frontend → generator API and/or Core API; do not replace Core (`server.py` on :18642).

## Acceptance
- [ ] No new ad-hoc HTML pages under `aeo-platform/ui/*` for this epic
- [ ] Changes land in aeo-generator frontend (and API only if needed)
- [ ] Live UI at http://2.28.106.22:9012/ reflects the work (or document redeploy steps)
- [ ] Illustrated MD + screenshots under BMAD screenshot rule: `_bmad-output/rules/SCREENSHOT_STEP_VERIFICATION.md`
- [ ] Deliverable note: `_bmad-output/solution/AEO_GENERATOR_UI_INTEGRATION_NOTE.md`

## BMAD refs
- `_bmad-output/solution/AEO_GENERATOR_DEFAULT_UI.md`
- `artifacts/aeo-platform/README.md` (My Space table)
- Phase 2 intent still applies, but **UI host is generator**, not light packages HTML

When finished: leave READY marker and list files changed + how to open the UI.
