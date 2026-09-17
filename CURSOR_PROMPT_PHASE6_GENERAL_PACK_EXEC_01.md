# Cursor — Phase 6 General Pack EXECUTION (do not stop until DONE)

**Date:** 2026-09-17  
**Pack type:** **General Pack** only (Google → AEO → SEO). NO e-Commerce catalog pack implementation.  
**Board:** https://github.com/orgs/Arkiphere/projects/2  
**Models:** Use **Composer Agent** for code/addons/API/UI. Use **Grok (Cursor)** for long design/docs/PDF prose when helpful. One SSH window per host.

## Non-negotiables

- Do not mark a Project card Done without evidence screenshots that **load correctly** (no blank/broken images).  
- Screenshot must match the step (BMAD rule).  
- Before/after: wipe test Optimizator order data (keep product 109); capture BEFORE then AFTER.  
- Final deliverable: PDF explaining each tested process with embedded verified screenshots.  
- Paths: `_bmad-output/2026-09-17_phase6_final/` on generator and CE `bmad/_bmad-output/`.  
- Index: `bmad/docs/process/INDEX_PHASE6_PAAS_CONTEXT.md`.

## Execution order (solve all)

### A — Hub / index (Grok or Composer docs)
Write/update `INDEX_PHASE6_PAAS_CONTEXT.md` on CE; link all Phase 6 plans. Card: Hub → Done when index + this READY stub exist.

### B — QA reset + BEFORE (Composer)
1. Snapshot BEFORE screens (gate Adquirir, allowed site value, portal if needed) → `…/BEFORE/`.  
2. Reset test orders/licenses (script pattern `reset_aeo_optimizator_orders.py`); keep SKU 109; no AnyApp VPS delete.  
3. Card QA → In Progress then continue after features.

### C — Anti-DevTools (Composer, aeo_generator)
Force site from consume SoT; 403 on mismatched site_url for packs/google/wizard. Prove with curls. Card Phase 5 Hostname anti-DevTools → Done.

### D — First page Conexión + Security + Postgres (Composer; CE + generator)
1. Postgres tables connection/graph/apply/changelog (or migrate).  
2. API register/revoke/encrypt.  
3. UI Step 0 Conexión after entitlement (General Pack path).  
4. Consent + revoke UX.  
Cards: UX Conexión, Security, Data Postgres.

### E — Odoo RPC addon page → register (Composer, arkiphere_ce)
aeo_base/sibling: generate API/RPC details → POST AEO. Card Odoo.

### F — Presta/Woo register wizards (Composer)
Webservice/REST → register + schema snapshot. Card Presta/Woo.

### G — First-use plugin recommendations (Composer)
Show missing module checklist on connect. Card First-use.

### H — Studies (Grok/Composer docs OK)
Embed/iframe signed token memo; Sitemap/robots/GSC sync memo — decisions only unless Alex GO implement. Cards Study → Done when MD+acceptance written.

### I — Fork AEO-generator if still open (Composer, aeo_generator)
Push rich history to https://github.com/codesystems2co/AEO-generator — Stage Git card.

### J — AFTER + full flow + PDF (Composer + screenshots)
1. Fresh order General Pack flow E2E.  
2. AFTER/ screenshots (verify pixels load, not duplicate wrong step).  
3. Build `PHASE6_GENERAL_PACK_TESTED.pdf` — one section per process with captioned screenshots.  
4. READY + PHASE6_GENERAL_PACK_TESTED.md  
5. Priority READY to PM.

## Exclude
Commerce/catalog pack implementation; payment; Project spam.

Priority READY only when all Phase 6 Todo/IP cards above are Done or explicitly deferred Study Done with MD.
