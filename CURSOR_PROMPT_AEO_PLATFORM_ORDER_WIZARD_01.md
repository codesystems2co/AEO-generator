# Cursor / GROK BOT — AEO platform: receive Optimizator order + start wizard

**Date:** 2026-09-16  
**Status:** READY TO IMPLEMENT on **aeo_generator** only.  
**Story:** `bmad/stories/feature/STORY_aeo_base_entitlement.md`  
**Why this prompt exists:** Arkiphere shop entitlement is **live**. The AEO platform UI/API is **not** ready to accept that order or open the wizard.

---

## Do not touch

- `18.0/aeo_base` (installed on `osh`, product **109**).
- Any App 108 / `github:gwrxuk/aeo-generator` VPS SKU.
- Extra GitHub OAuth apps. GitHub on Arkiphere stays shop login only.
- Light HTML under `bmad/handoff/aeo-platform/ui`.
- `kubectl rollout restart`. Generator rebuild is that host’s image/pod flow, not platform Odoo HUP.

**Workspace:** one SSH window **`aeo_generator`** (`/root/anyapp-github-build/AEO-generator` or the live My Space checkout). Not the addons monorepo.

Live UI: http://2.28.106.22:9012/  
Live API: http://2.28.106.22:8642/

---

## Business rule

A **confirmed** IA Search Optimizator Pack order + unique **activation key** + **HTTPS site URL** = entitlement to use Optimizator.

The generator must **not** start packs until Arkiphere says `allowed: true` for that key.

---

## What Arkiphere already sends you

Open AEO (mail + portal) lands on:

```
http://2.28.106.22:9012/?license=AEO-…&site=https%3A%2F%2Fwww.example.com
```

Query names: **`license`** and **`site`** (HTTPS URL, already normalized).

Consume (public, key only — not GitHub OAuth):

```
GET  https://arkiphere.cloud/aeo/license/consume/http?key={license}
POST https://arkiphere.cloud/aeo/license/consume/http   JSON { "key": "...", "github_login": "optional" }
JSON-RPC POST https://arkiphere.cloud/aeo/license/consume
```

Success:

```json
{
  "allowed": true,
  "sale_order_name": "S00xxx",
  "aeo_site_url": "https://www.example.com",
  "partner_id": 123,
  "open_url": "http://2.28.106.22:9012/?license=…&site=…"
}
```

Failure (empty/unknown key, unconfirmed order, wrong product): `allowed: false`. Keep **Sin pedido** / wizard locked.

Config on Odoo (`ir.config_parameter`): `aeo_base.ui_url` = `http://2.28.106.22:9012`, `aeo_base.api_url` = `http://2.28.106.22:8642`.

---

## Implement (generator)

1. **On load:** if `license` (or `key`) is in the query, fill the activation-key field; if `site` is present, fill hostname (display host; keep https).
2. **RPC:** call Arkiphere consume with that key. Prefer `/aeo/license/consume/http` (plain JSON). Do not require GitHub to unlock.
3. **If allowed:** store `sale_order_name` + `aeo_site_url`; **enable Begin wizard** (Phase 3 shell: Google Search → AEO → SEO, Continuar/Atrás). Load packs against that hostname.
4. **If not allowed:** stay blocked. No packs. Honest empty/error state.
5. Optional: if a GitHub session exists, pass `github_login` on consume (ignored for allow/deny today).

Do not invent a second entitlement API. Do not key the wizard only on `github_login` for this pack.

---

## Acceptance

- [ ] Opening `http://2.28.106.22:9012/?license=INVALID&site=https://www.example.com` stays blocked / Sin pedido.
- [ ] After a **real confirmed** product-109 order, Open AEO fills license + site and consume returns `allowed: true`.
- [ ] **Begin wizard** is enabled only then; first step is Google Search, then AEO, then SEO.
- [ ] Live `:9012` reflects the work (rebuild frontend/API images; pod copy is ephemeral).
- [ ] Evidence MD + screenshots: `bmad/_bmad-output/` or `bmad/artifacts/testing/` dated folder — not repo root.
- [ ] READY ping: order name, consume JSON (redact full key if needed), wizard first-step shot.

---

## Related prompts (read, do not re-do shop)

- `CURSOR_PROMPT_PHASE3_WIZARD_ONLY_01.md` — wizard-only UX
- `CURSOR_PROMPT_AEO_GENERATOR_UI_01.md` — stay on generator React
- `CURSOR_PROMPT_AEO_GSC_OAUTH_PROXY_01.md` — GSC callback already on Arkiphere
- `CURSOR_PROMPT_AEO_FRIENDLY_UI_01.md` — shop design; **implemented on CE**
