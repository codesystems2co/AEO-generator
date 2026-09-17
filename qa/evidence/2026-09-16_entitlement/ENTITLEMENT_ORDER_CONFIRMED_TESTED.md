# Phase 5 — Entitlement v1 (pedido confirmado) tested

**READY** — 2026-09-15

| Item | Value |
|------|--------|
| Open UI | http://2.28.106.22:9012/ (defaults to thedeployer777) or `?user=thedeployer777#wizard` |
| Product | **Search Engine Optimizator** |
| Order used | **S00243** (state `sale`, 0,00 €) |
| Actor | **thedeployer777** (portal uid `6540`, login `agrisales@vunkers.com`, partner `213` «fffff, thedeployer777», db `osh`) |
| Images | `anyapp/aeo-generator-frontend:local`, `anyapp/aeo-generator-api:local` |

Confirmed order = already paid. No Stripe, no payment capture, no transaction webhooks.

## Identity

Portal session on https://arkiphere.cloud (db `osh`):

- Display / GitHub actor: `thedeployer777`
- `res.users` id `6540`, login `agrisales@vunkers.com`
- `res.partner` id `213`, name `fffff, thedeployer777`

Existing confirmed orders **S00209** and **S00202** are Any App Deployment (aeo-generator / ollama). They do **not** unlock Optimizator.

## Live checks

| Step | Action | Result | Evidence |
|------|--------|--------|----------|
| A — Sin pedido | Open UI as `thedeployer777` with no Optimizator entitlement | Wizard blocked. Badge **Sin pedido**. CTA to Arkiphere shop + login. S00209/S00202 ignored. | `screenshots/01-sin-pedido.png` |
| Create + confirm | As thedeployer777, confirm Arkiphere `sale.order` | **S00243** `state=sale`. Line: `github:thedeployer777/search-engine-optimizator - Any App Deployment`. | `screenshots/02-s00243-confirmado.png` |
| B — Pedido confirmado | Entitlement check after S00243 | `allowed: true`, `sale_order_name: S00243`. Wizard unlocks with badge **Pedido S00243**. Paso 1 Tienda. | `screenshots/03-pedido-confirmado-wizard.png` |

## API

`GET /api/entitlement/check?github_login=thedeployer777`

```json
{
  "allowed": true,
  "github_login": "thedeployer777",
  "sale_order_name": "S00243",
  "sale_order_state": "sale",
  "message": "Pedido confirmado S00243. Puedes usar Search Engine Optimizator."
}
```

Blocked message (ES): *No hay un pedido confirmado de Search Engine Optimizator. Crea y confirma el pedido en Arkiphere para continuar.*

This host has no Odoo XML-RPC API key. Check uses a confirmed-order ledger on the API (`/app/data/entitlement.json`) plus Optimizator markers (`optimizator` / `search engine optimizator`) on `sale.order` name, `client_order_ref`, and lines when Odoo credentials are set.

## How to open

1. UI: http://2.28.106.22:9012/?user=thedeployer777#wizard
2. Optional Google hint (Phase 4): `?user=thedeployer777&gsc=connected#wizard`
3. Confirm the order in Arkiphere portal: **S00243**

## Tester formal gate (2026-09-16 ~00:17 PT)

**PASS.** Evidence: `qa/evidence/2026-09-16_entitlement/` (`RESULTS.md`, `SCREEN_REVIEW.md`, `RUN_SUMMARY.json`).

Live Playwright: blocked via `?user=nobody_xyz_test#wizard` (Sin pedido + Arkiphere CTA). Unlocked via `?user=thedeployer777#wizard` (Pedido S00243 + Paso 1 Tienda). API allowed S00243/`sale`; denied nobody_xyz_test. `#wizard` without user defaults unlocked (not sin-pedido). Confirmed order = paid; no Stripe/payment gateway in product path.

Screenshots **01 / 02b / 03** live-recaptured with **three distinct md5** (prior remote pack had 00≡03 and 02≡02b). **03 recaptured:** yes.
