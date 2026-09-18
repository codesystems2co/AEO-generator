# HIDE_INFRA_TESTED

**Date:** 2026-09-18  
**Live:** http://2.28.106.22:9012/  
**Product:** Search Engine Optimizator  
**Card:** Phase 4 · UX — Ocultar infraestructura (Core/Ollama/puertos)  
**Result:** **PASS** (Tester)

## Customer UI

Live gate and wizard chrome show **zero** generation-infra terms:

- No Core / Ollama / Docker / Kubernetes / K8s
- No ports `:18642` / `:8642` / `:9012` / `server.py`
- No “Re-probe Core”, “Write SEO via Core”, “Ollama pack”
- No Ollama/Core health badges

Primary UI remains wizard-only (`App.jsx` → Layout + Wizard). Header is logo + **Search Engine Optimizator**. Connectors / Packs / Chat / Google Search tabs are not in the nav.

Business language on the live wizard (i18n): Conexión, Google Analysis, AEO, SEO; pack intros talk about tienda / Google / publicar — not generation hosts.

## Code (fork `arkiphere-optimizator`)

| File | Change |
|------|--------|
| `frontend/src/tabs/Connectors.jsx` | Conexión / Publicar / Comprobar publicación. Health probe, `core_url`, JSON dump, “proxy” badge removed. Unreachable from App. |
| `frontend/src/tabs/Packs.jsx` | Pack AEO + SEO. Health badge / backend chip removed. Unreachable from App. |
| `frontend/src/tabs/GoogleSearch.jsx` | No “AEO Core” / env-var copy. Unreachable from App. |
| `frontend/src/tabs/Wizard.jsx` | Gap classifier maps secret/env leaks to business labels (already on branch). |
| `frontend/src/App.jsx` / `Layout.jsx` | Unchanged: wizard only, no Asistente/Herramientas nav. |

`frontend/src/api.js` still builds the API host at runtime (not shown in JSX). Live Vite on `:9012` proxies product calls; customers do not see that string in the UI.

## Evidence

- `screenshots/01_wizard_home.png` — live gate, empty key (md5 `69338cbf…`)
- `screenshots/02_wizard_after_nav.png` — same gate after `AEO-TEST` check (md5 `67b14724…`, distinct)
- `GREP_SRC_DIST.txt` — no `Ollama` / `:18642` / Re-probe / Write SEO via Core / AEO Core in `frontend/src`
- `LIVE_GREP.json` — visible DOM hits empty
- Live modules `copy.js` / Packs / Connectors / GoogleSearch: infra regex empty
- DevTools: http://2.28.106.22:9012/ title Search Engine Optimizator; innerText hits `[]`; no console errors

## Git

Fork only: `https://github.com/codesystems2co/AEO-generator` branch `arkiphere-optimizator` (never gwrxuk).

## Note for Tester

Unlocked pack steps (AEO / SEO / Publicar) need a real order license. Copy for those steps is in live `src/i18n/copy.js` (intros above) with no infra tokens. Deep links `#packs` / `#connectors` do not mount those tabs.
