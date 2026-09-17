# Cursor — Phase 5 lifecycle UX: wizard chrome + portal/mail activation

**Date:** 2026-09-16  
**Plan:** `docs/process/PLAN_AEO_LIFECYCLE_IMPROVEMENT_LOOP.md`  
**Hosts (ONE SSH window at a time):**

1. **aeo_generator** — hide Asistente/Herramientas  
2. **arkiphere_ce** — portal confirmed-order block + professional activation document + mail align  

Do not mix windows. Close the other host before switching.

## A) aeo_generator — no Asistente / Herramientas

- Remove customer-visible **Asistente** and **Herramientas** tabs/menus entirely (not just default-select).
- Wizard-only shell remains (Phase 3/4). No hatch that reopens Herramientas for customers.
- Keep license+site consume unlock (S00245 path / product 109). Do not break `?license=&site=`.
- Rebuild live `:9012` (and API if needed). Pod copy is ephemeral.

## B) arkiphere_ce — `aeo_base` portal + mail + document

Confirmed order page (e.g. `/my/orders/...` S00245 style) must look **professional**, not ERP-default:

1. **Activation panel (redesign “Open AEO” block)**  
   - Branded card: title, 2–3 short steps (site confirmed → open Optimizator → start wizard).  
   - Primary CTA **Open AEO** (deep link `aeo_base.ui_url` + license + site).  
   - Secondary: view order PDF / details (keep existing if present).  
   - Show site hostname + order name; never show infra ports.

2. **Activation guide (replace simple .txt attach)**  
   - Stop seeding a bare text `product.document` as the only customer-facing help.  
   - Prefer **rendered QWeb / portal HTML page** (or polished PDF) titled e.g. “How to activate IA Search Optimizator Pack” with numbered steps, screenshots placeholders OK, es_ES + en.  
   - Link from the activation panel (“View activation guide”) instead of a lonely attachment card that looks like a raw file dump.  
   - If a `product.document` remains for mail attach, make it a proper PDF or HTML-derived doc — not a `.txt`.

3. **Confirmation mail**  
   - Same hierarchy: short intro → Open AEO button → link to guide. Match portal copy.

4. **Minimal diffs** — no butterfly on AnyApp/Odoo provision; do not change product 109 flags / skip-VPS logic.

5. Reload: `kill -HUP 1` after `-u aeo_base`. Never `kubectl rollout restart`.

## C) Test data reset (after UX lands)

- Document how to cancel/archive **test** Optimizator orders used for gates (e.g. S00245) **without** deleting the product 109 SKU.  
- Prefer cancel + archive portal visibility OR unlink license for re-test; keep one golden evidence folder dated.  
- Re-create **one** fresh confirmed order with hostname, prove Open AEO → wizard with new chrome.  
- Evidence MD + screenshots under `_bmad-output/` dated folder. READY ping.

## Do not

- Re-add GitHub login tasks.  
- Touch Any App 108 VPS SKU.  
- Payment gateways.  
- Stack duplicate Composer prompts.

## Acceptance

- [ ] Live `:9012` has **no** Asistente/Herramientas UI.  
- [ ] Portal confirmed Optimizator order shows redesigned activation panel + professional guide entry.  
- [ ] Mail matches.  
- [ ] No `.txt`-only activation attach as primary UX.  
- [ ] Fresh order E2E after reset PASS.  
- [ ] READY + illustrated MD.
