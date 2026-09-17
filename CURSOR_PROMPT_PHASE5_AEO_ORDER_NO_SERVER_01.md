# Cursor Agent — AEO order access-only (NO Hetzner server) + GitHub login in AEO

## Critical business rule (Alex 2026-09-16)
Purchasing AEO / Search Engine Optimizator on Arkiphere = **entitlement to use the AEO platform**.
It must **NOT** create a Hetzner (or other) server.

Confirmed order = paid. Still **no** payment gateway work.

## Butterfly-effect guardrails (MANDATORY)
- **Minimal diffs.** Do not refactor unrelated kuber/AnyApp/Odoo deploy pipelines.
- Touch only the branch that decides “should this sale order line provision a physical/VPS server?”
- **Preserve** provisioning for: AnyApp/anydeploy images, Odoo deployments, and other real infra SKUs.
- Prefer product-type / template / marker check (e.g. Optimizator / `search-engine-optimizator` / SaaS-access category) rather than broad disables.
- Add a regression note: one AnyApp deploy order still provisions; Optimizator order does not.

## Workstreams

### A) Cleanup
- Identify server tied to **S00243** (UI card: Active, 2 VCPU, 4GB, 40GB SSD, Public IP **167.233.121.198**).
- If it was created only because of the Optimizator entitlement order, **remove/decommission** it safely (Arkiphere + Hetzner as applicable).
- Do **not** delete the **sale.order S00243** entitlement itself — order stays for access.

### B) Prevent future server creation for access-only products
- On Arkiphere (arkiphere_ce / Odoo kuber deploy path): skip Hetzner/physical server creation when the order/product is AEO Optimizator access-only.
- Document the exact SKU/template/marker used.

### C) Auth in AEO
- Add/finish **GitHub auth login** on Search Engine Optimizator (aeo_generator) so the session can call entitlement against Arkiphere orders.
- If no GitHub profile, Arkiphere remains profile source of truth (document handoff).
- Session in AEO → consult orders → allow/deny wizard (already have entitlement API; wire real GitHub session).

## Workspaces
- Arkiphere infra gate: single SSH **arkiphere_ce** (no second window).
- Optimizator GitHub login: single SSH **aeo_generator** (not both hosts open at once if same connection pool — switch one window).
- Composer Agent. No light HTML under aeo-platform/ui.

## Deliverables
- `_bmad-output/phase5/AEO_ORDER_NO_SERVER_TESTED.md` + screenshots
- Evidence: S00243 server gone (or justified keep); new Optimizator order does not create VPS; AnyApp still does
- READY marker
- List exact files changed (keep short)

READY-ping PM with order name + before/after server state.
