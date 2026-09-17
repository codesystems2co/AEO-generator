# RESULTS — Phase 5 Entitlement (pedido confirmado) formal gate

**Date:** 2026-09-16 ~00:17 Europe/Madrid (PT)  
**Global:** **PASS**  
**UI unlocked:** http://2.28.106.22:9012/?user=thedeployer777#wizard  
**UI blocked (discovered):** http://2.28.106.22:9012/?user=nobody_xyz_test#wizard  
**API:** http://2.28.106.22:8642/api/entitlement/check  
**MD:** docs/process/ENTITLEMENT_ORDER_CONFIRMED_TESTED.md · `_bmad-output/phase5/`

## Accept

| Check | Result | Detail |
|-------|--------|--------|
| 1_sin_pedido_blocked | **PASS** | `?user=nobody_xyz_test#wizard` → PEDIDO REQUERIDO, badge **Sin pedido**, CTAs Arkiphere shop + login. Wizard not unlocked. |
| 2_pedido_confirmado_unlocked | **PASS** | `?user=thedeployer777#wizard` → badge **Pedido S00243**, ASISTENTE + **PASO 1 — TU TIENDA** (Odoo/Presta/Woo). |
| 3_api_allowed | **PASS** | `github_login=thedeployer777` → `allowed:true`, `sale_order_name:S00243`, `sale_order_state:sale`. |
| 4_api_denied | **PASS** | `github_login=nobody_xyz_test` → `allowed:false`, ES message + `cta_url` Arkiphere shop. Bare/`github_login=` defaults actor thedeployer777 (allowed) — not a denied path. |
| 5_no_payment_gateway | **PASS** | Gate uses confirmed `sale` order (paid when confirmed). UI copy: pago ya hecho al confirmar. No Stripe/checkout in product path. |
| 6_screenshot_distinct_01_02b_03 | **PASS** | Three distinct md5 after live recapture (see below). |

## Screenshot distinctness (live)

| File | md5 | Frame |
|------|-----|-------|
| `01-sin-pedido.png` | `cce525a4c6645a9642d656ca3cbe1195` | Blocked modal, user nobody_xyz_test, Arkiphere CTAs |
| `02b-s00243-confirmed.png` | `a4a9d0d9aa24641fb253ff98ba89e15d` | Unlocked header strip: green **Pedido S00243** + stepper Tienda |
| `03-pedido-confirmado-wizard.png` | `ef6af16ed54b60f01932450bfe4b6363` | Full wizard unlocked Paso 1 Tienda (platform cards + URL) |

**03 recaptured:** **YES** (live Playwright). Prior remote pack had `00-default-url.png ≡ 03` and `02 ≡ 02b`; Mac evidence now has distinct 01/02b/03. Default `/` and `#wizard` (no user) still unlock as thedeployer777 — expected product default, not used as 03 evidence.

## Discover blocked URL

| URL | Result |
|-----|--------|
| `/#wizard` (no user) | Unlocked (defaults thedeployer777 / S00243) — **does not** show sin-pedido |
| `/?user=nobody_xyz_test#wizard` | **Sin pedido** blocked + Arkiphere CTA |
| `/?user=thedeployer777#wizard` | Unlocked Pedido S00243 |

## Ledger / gate note

Per tested MD: host may use `/app/data/entitlement.json` ledger + Optimizator markers when Odoo XML-RPC key absent. Confirmed = `state=sale`; no payment gateway code required in product.

## Evidence paths

- Mac: `$HOME/Documents/GROK BOT/projects/aeo-platform/qa/evidence/2026-09-16_entitlement/`
- Live JSON: `live_capture/playwright_report.json`
