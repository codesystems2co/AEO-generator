# Cursor Agent — Entitlement v1: pedido Arkiphere confirmado (thedeployer777)

## Business rule (Alex)
**Orden/pedido confirmado = pago ya realizado.** Do **not** implement payment gateways, Stripe, or transaction webhooks. Only entitlement from Arkiphere `sale.order` (or equivalent) in a **confirmed** state.

## Test user
- GitHub / Arkiphere actor: **thedeployer777** (same user as Cursor session / thedeployer777)
- Must exercise **both**:
  1. **No order yet** → Optimizator must block or clearly send user to create/confirm order in Arkiphere
  2. **Order confirmed** → Optimizator unlocks for that user

## Goals
1. Resolve how to identify thedeployer777’s partner / portal user / sale orders on Arkiphere (Odoo db `osh` / portal).
2. Implement entitlement check (API + UI) for Search Engine Optimizator:
   - Input: logged-in Arkiphere user or explicit partner/SO reference agreed in design
   - Output: `allowed: true/false`, `sale_order_name` if any, human message (ES)
3. UI gate on http://2.28.106.22:9012/ (wizard): before Tienda/Google flow (or as first gate), show status:
   - Sin pedido → CTA to Arkiphere to place/confirm order
   - Pedido confirmado → continue wizard
4. E2E with thedeployer777:
   - A) Ensure no active confirmed Optimizator order → see blocked state
   - B) Create + **confirm** order in Arkiphere as that user (Cursor session) → Optimizator allows access
5. Evidence: screenshots both states + MD `_bmad-output/phase5/ENTITLEMENT_ORDER_CONFIRMED_TESTED.md` + READY

## Workspace
- Prefer **aeo_generator** for Optimizator UI/API changes (single SSH session that host).
- Arkiphere Odoo / order work on **arkiphere_ce** only if needed — **never** two SSH windows on the same host; switch one window, don’t dual-open.
- Composer Agent mode. No aeo-platform light HTML.

## Product name
Search Engine Optimizator (keep Phase 4 branding).

## Out of scope
Payment capture, refunds, multi-SKU catalog redesign, Phase 5 full shell redesign.

## Acceptance
- [ ] Both flows demonstrated for thedeployer777
- [ ] Confirmed order unlocks; unconfirmed/missing blocks
- [ ] No payment transaction code
- [ ] READY + tested MD + screenshots (SCREENSHOT_STEP_VERIFICATION)

READY-ping PM with how to open UI + order name used.
