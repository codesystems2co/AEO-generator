# Cursor Agent — Phase 4: Product UX polish (Search Engine Optimizator)

## Live
http://2.28.106.22:9012/?gsc=connected#wizard
Workspace: AEO-generator [SSH: aeo_generator] only — one session.

## Must do
1. **Branding:** Primary name **Search Engine Optimizator**; Arkiphere logo in header.
2. **Hide infrastructure from customers:** no Core :18642, no "Ollama ok" / "Core down" / "Google oauth" tech chips. Friendly labels only.
3. **Google Search step labels:** human-eye Spanish (or EN consistent with UI). Fix consent row: if API `connected=true`, show granted checkmark, not ○ "User must grant…".
4. **Paso 1 button + states:** clearer CTA and proper state labels (completo / pendiente / auto-corregido).
5. **New first step (or reorder):** select commerce platform (Odoo / PrestaShop / WooCommerce) + connection verify BEFORE Google → AEO → SEO → Inject. Move shop URL setup earlier.
6. **AEO/SEO pack step copy:** clarify Ollama generates the pack (tree); Tema/Negocio/Hechos are inputs — remove infra PaaS/Docker/K8s default facts.

## Do not
- New aeo-platform light HTML
- Fake inject success if Core down (keep honest message, but word it for humans)
- Full Phase 3 rewrite — polish on current wizard shell

## Deliver
- Rebuild durable frontend (and API if needed) images
- `_bmad-output/phase4/PHASE4_UX_POLISH_TESTED.md` + screenshots
- READY marker

READY-ping PM when done.
