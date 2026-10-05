# METERING_NOTE — Catalog ficha metering

Date: 2026-10-05. Branch: `feat/catalog-ficha-metering`.  
Scope: **catalog flow only**. General wizard metering/pricing untouched. No Odoo orders created. No ARKISPHERE / live Odoo changes.

## Design

| Concept | Rule |
|---|---|
| Allowance | Sum of `product_uom_qty` on confirmed (`sale`/`done`) order lines for catalog product **110** / name marker `Product Catalog AEO and SEO pack With IA`, on the license order (`consume` → `sale_order_name`). Prefer lines whose `aeo_site_url` matches the license hostname when several catalog lines exist. |
| S00247 | No catalog line → allowance **0**. General unlock still opens the assistant (`owned` via `general_allowed`). |
| Credit spend | Only when a **new** product/service ID is **successfully applied/written** under `(license, hostname)`. |
| «Processed» | Means **applied/written successfully**, not merely analyzed (`tick_session` / compose do not consume). |
| Re-apply | Already-processed IDs cost **0** (write allowed even when remaining is 0). |
| Block | If remaining ≤ 0 for a never-processed ID → skip write with `reason: no_credits`. Analysis/read/open still allowed. |

## Qty source

`api/app/routers/catalog.py` → `_order_line_rows()` extends the existing XML-RPC `_lines` path: reads `sale.order` (state) + `sale.order.line` fields `name`, `product_id`, `product_uom_qty`, `product_template_id`, and `aeo_site_url` when available. Detection in `catalog_metering.is_catalog_line` by name marker / template id 110 / default_code. Does **not** call aeo_base consume changes.

## Storage

- Path: `/app/data/catalog_metering.json` (config: `CATALOG_METERING_STORE`)
- Pattern: same atomic JSON write as `entitlement.json` / `connections.json`
- Key: `license|normalized_hostname` → `{ processed_ids: [...] }`
- **Deploy note:** k8s currently has no PVC for `/app/data`; orchestrator will add hostPath mount. Without persistence across pod restarts, applied IDs reset and credits could be re-spent until the mount exists.

## Offer / API fields

On catalog offer (and publish response): `allowance`, `used`, `remaining`, `processed_ids` (count), `acquire_url` (always catalog product page — not null just because general unlocked).

## UI

`CatalogWizard.jsx` + `copy.js` ES/EN:

- Badge: «Fichas nuevas: {remaining} restantes · {used} / {allowance}»
- When remaining is 0: blocked message + acquire button to existing product URL (no new checkout flow)

## Files changed

| File | Role |
|---|---|
| `api/app/services/catalog_metering.py` | **New** — store, allowance, can_apply, record_applied, snapshot |
| `api/app/config.py` | `CATALOG_METERING_STORE` |
| `api/app/routers/catalog.py` | Line qty read, merge metering into offer, pass allowance into publish |
| `api/app/services/catalog_apply.py` | Credit gate + record after successful new write |
| `api/app/services/catalog_session.py` | `publish_fixture` host/allowance + blocked counts |
| `api/app/services/catalog_product.py` | `acquire_url` always product page |
| `frontend/src/tabs/CatalogWizard.jsx` | Badge + blocked CTA |
| `frontend/src/i18n/copy.js` | ES/EN ficha strings |
| `api/tests/test_catalog_metering.py` | **New** — unit tests |
| `_bmad-output/issue-46/credits-general/METERING_NOTE.md` | This note |

## Test results

Command (local venv with `api/requirements.txt`):

```text
PYTHONPATH=. python -m unittest tests.test_catalog_metering tests.test_catalog_pack tests.test_catalog_session -v
```

```text
test_acquire_url_stays_when_owned ... ok
test_detects_template_id_110 ... ok
test_s00247_style_order_without_catalog_line_is_zero ... ok
test_sums_catalog_qty_and_prefers_same_hostname ... ok
test_allowance_n_blocks_extra_new_ids ... ok
test_reprocess_processed_id_costs_zero ... ok
test_zero_allowance_blocks_new_writes_analysis_untouched ... ok
test_save_load_round_trip ... ok
test_snapshot_fields ... ok
(+ existing catalog_pack / catalog_session tests)

Ran 22 tests in 0.069s
OK
```

Coverage of required cases:

1. Allowance N, M new IDs with M>N → processes N, blocks M−N  
2. Re-processing processed ID costs 0  
3. Persistence round-trip (save/load store)  
4. Zero allowance → all new writes blocked; analysis does not consume  
