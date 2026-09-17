# Phase 5 — Entitlement v1 (pedido confirmado) tested

**READY** — 2026-09-16

| Item | Value |
|------|--------|
| Open UI (blocked) | http://2.28.106.22:9012/?user=thedeployer777#wizard |
| Open UI (unlocked) | http://2.28.106.22:9012/?license=AEO-…&site=https%3A%2F%2Fwww.example.com |
| Product | **Search Engine Optimizator** |
| Order used | **S00245** (state `sale`, 0,00 €, product 109 AEO-OPTIMIZATOR) |
| Actor | **thedeployer777** (portal uid `6540`, login `agrisales@vunkers.com`, partner `213` «fffff, thedeployer777», db `osh`) |
| Images | `anyapp/aeo-generator-frontend:local`, `anyapp/aeo-generator-api:local` |

Confirmed order = already paid. No Stripe, no payment capture, no transaction webhooks.

## Identity

Portal session on https://arkiphere.cloud (db `osh`):

- Display / GitHub actor: `thedeployer777`
- `res.users` id `6540`, login `agrisales@vunkers.com`
- `res.partner` id `213`, name `fffff, thedeployer777`

Existing confirmed orders **S00209** and **S00202** are Any App Deployment (aeo-generator / ollama). They do **not** unlock Optimizator. GitHub login alone does **not** unlock.

SO reference agreed in design: Arkiphere activation key on confirmed product 109, consumed via `POST /api/entitlement/consume` → Arkiphere `/aeo/license/consume/http`.

## Live checks

| Step | Action | Result | Evidence | Pass |
|------|--------|--------|----------|------|
| A — Sin pedido | Open UI as `thedeployer777` with no license | Wizard blocked. Badge **Sin pedido**. CTA shop + login. Comenzar asistente disabled. | `screenshots/01-sin-pedido.png` | PASS |
| Create + confirm | As thedeployer777, confirmed Arkiphere `sale.order` | **S00245** `state=sale`. Line: `[AEO-OPTIMIZATOR] IA Search Optimizator Pack`. Site `https://www.example.com`. Open AEO. | `screenshots/02-s00245-confirmado.png` | PASS |
| B — Pedido confirmado | Open AEO / consume S00245 key | `allowed: true`, `sale_order_name: S00245`. Wizard unlocks **Pedido S00245**. Paso 1 Google Search. | `screenshots/03-pedido-confirmado-wizard.png` | PASS |

md5 distinct: `01` `3846d894…` · `02` `87c7203b…` · `03` `ae40872a…`

## API

`POST /api/entitlement/consume` (key redacted)

Blocked:

```json
{
  "allowed": false,
  "sale_order_name": null,
  "message": "No hay un pedido confirmado de Search Engine Optimizator. Crea y confirma el pedido en Arkiphere para continuar."
}
```

Unlocked (thedeployer777 / partner 213):

```json
{
  "allowed": true,
  "sale_order_name": "S00245",
  "sale_order_state": "sale",
  "aeo_site_url": "https://www.example.com",
  "partner_id": 213,
  "message": "Pedido confirmado S00245. Puedes usar Search Engine Optimizator."
}
```

## How to open

1. Blocked: http://2.28.106.22:9012/?user=thedeployer777#wizard
2. Unlocked: Open AEO from Arkiphere portal order **S00245** (or consume `open_url`)
