# HIDE_INFRA_TESTED

**Date:** 2026-09-18  
**Live:** http://2.28.106.22:9012/  
**Card:** Phase 4 · UX — Ocultar infraestructura (Core/Ollama/puertos)

## Result: PASS

Customer-visible product UI shows **zero** infra terms:
- No Core / Ollama / Docker / Kubernetes / K8s
- No ports `:18642` / `:8642` / `:9012` / `server.py`
- No “Re-probe Core”, “Write SEO via Core”, “Ollama pack”

App remains wizard-only (`App.jsx` → Layout + Wizard). Connectors/Packs tabs unreachable from nav; their copy was still scrubbed so any deep link is business language.

## Changes
- `frontend/src/tabs/Connectors.jsx` — Conexión / Publish SEO / Verify publish
- `frontend/src/tabs/Packs.jsx` — AEO + SEO pack / Pack service
- `frontend/src/tabs/GoogleSearch.jsx` — no “AEO Core”
- `frontend/src/tabs/Wizard.jsx` — gap classifier without infra tokens
- Live pod `/app/src/tabs/*` updated to match

## Evidence
- `screenshots/01_wizard_home.png`, `02_wizard_after_nav.png`
- `LIVE_GREP.json` — visible_hits / html_hits empty
- Live module curl: Connectors/Packs/GoogleSearch/Wizard CLEAN for infra regex

## Git
Push fork `codesystems2co/AEO-generator` branch `arkiphere-optimizator` only (never gwrxuk).
