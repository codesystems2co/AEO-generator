# AEO-generator UI integration note

**READY** — 2026-09-15

Product UI is the **default React/Vite generator**, not Core light HTML.

| Item | Value |
|------|--------|
| Open UI | http://2.28.106.22:9012/ |
| Deep links | `#wizard` `#google` `#packs` `#connectors` `#meta` |
| API docs | http://2.28.106.22:8642/docs |
| Core | `:18642` (`server.py`) — **proxied only**, not replaced |

## What landed

Existing tabs kept (Chat, Guide, Meta Tags, Keywords, Content Analysis, AEO, SEO Score, NLP, URL, External SEO, GEO).

New dark-UI tabs on the same app:

1. **Wizard** — Google Search → AEO → SEO guided flow.
2. **Google Search** — public readiness checklist plus **OAuth (client consent)** vs **Service Account** modes.
3. **Ollama Packs** — AEO + SEO pack with a human-readable **tree list resume**.
4. **Connectors** — Odoo / PrestaShop / WooCommerce **write/verify forwarded to Core :18642**.

## Live checks (this host)

| Step | Result | Evidence |
|------|--------|----------|
| Open live UI | Wizard is default; all original tabs still present | `01-wizard.png` |
| Google readiness on https://arkiphere.cloud | 4/8 public checks pass (title, robots, sitemap, HTTP 200). OAuth not configured yet | Wizard step 1 + `02-google-search.png` |
| OAuth vs SA | Mode cards + “Start Google consent” / session SA JSON | `02-google-search.png` |
| Ollama pack | `backend=ollama`, model `llama3.2:3b`, tree resume | `04-ollama-packs.png`, `_bmad-output/evidence/pack_resume.txt` |
| Wizard AEO → SEO | Title/meta/FAQ/H2 + SEO score 75/100 (C) | Interactive run on live UI |
| Connectors write | Core **offline**; generator reports unreachable and does not write itself | `05-connectors.png` |
| Regression | Meta Tags form unchanged | `06-meta-tags.png` `#meta` |

Example tree resume from live `/api/packs/generate`:

```
Arkiphere Cloud
├── AEO
│   ├── Title — Arkiphere Cloud Overview
│   ├── FAQ (5)
│   └── H2 (5)
└── SEO
    ├── Title tag / Meta / Keywords
    └── Score — 75 / 100 (C)
```

## API added (generator, not Core)

- `GET/POST /api/google/status|readiness|oauth/start|oauth/callback|sites|sa/session`
- `GET/POST /api/packs/health|generate`
- `GET/POST /api/connectors/health|platforms|write|verify`
- `GET/POST /api/wizard/status|run`

Connectors probe Core at `CORE_BASE_URL` (default `http://172.17.0.1:18642`) and try write-seo / verify path templates. First non-404 wins.

## Google auth

- **OAuth:** set `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` on the API. Redirect: `http://2.28.106.22:8642/api/google/oauth/callback`. User clicks **Start Google consent**.
- **Service Account:** `GOOGLE_SA_JSON` / `GOOGLE_SA_FILE`, or paste JSON for the API process session only. Share the GSC property with the SA email.

## Core status on this node

`:18642` is **not listening**. Connectors correctly stay in proxy-fail mode. Start Core (`server.py`) on the host (reachable as `172.17.0.1:18642` from the API pod, same pattern as Ollama on `:11435`).

## Redeploy (durable)

Live UI already reflects this work via files copied into the running pods (`codesystems2co325v1`). **A pod restart drops those copies** unless images are rebuilt:

```bash
# from this repo
# build and retag into containerd as:
#   anyapp/aeo-generator-frontend:local
#   anyapp/aeo-generator-api:local
# then:
microk8s kubectl rollout restart deploy/aeo-generator-app deploy/aeo-generator-api-app -n codesystems2co325v1
```

Do **not** add pages under `aeo-platform/ui/*` for this epic.

## Files changed

### Frontend
- `frontend/src/App.jsx`
- `frontend/src/api.js`
- `frontend/src/App.css`
- `frontend/src/index.css`
- `frontend/src/components/Layout.css`
- `frontend/src/components/TreeList.jsx`
- `frontend/src/components/TreeList.css`
- `frontend/src/tabs/Wizard.jsx`
- `frontend/src/tabs/GoogleSearch.jsx`
- `frontend/src/tabs/Packs.jsx`
- `frontend/src/tabs/Connectors.jsx`

### API
- `api/main.py`
- `api/app/config.py`
- `api/app/services/core_client.py`
- `api/app/services/google_search_service.py`
- `api/app/services/pack_service.py`
- `api/app/routers/google_search.py`
- `api/app/routers/packs.py`
- `api/app/routers/connectors.py`
- `api/app/routers/wizard.py`

### BMAD
- `_bmad-output/rules/SCREENSHOT_STEP_VERIFICATION.md`
- `_bmad-output/solution/AEO_GENERATOR_UI_INTEGRATION_NOTE.md`
- `_bmad-output/solution/READY`
- `_bmad-output/evidence/screenshots/*.png`
