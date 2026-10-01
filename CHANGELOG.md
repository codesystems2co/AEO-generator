# Changelog

All notable changes to the AEO / SEO Optimizator project are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Mac gateway testing secret layout: `.env.gateway-testing.example`, gitignored `.secrets/mac-gateway-testing.env`, `scripts/check-secrets-not-committed.sh`, rule `gateway-testing-secrets.mdc` (no real keys in git).
- `CHANGELOG.md` for release notes on branch `optimizator/light-dark-odoo-compat-01`.
- OAuth return tests: `api/tests/test_oauth_return_state.py`.
- Platform test evidence: `_bmad-output/2026-09-30_issue27_platform_test/`.

### Changed

- **Wizard — connection step:** platform cards use icon + name in two columns; Odoo credentials in a two-column grid with database last; connect/disconnect actions use platform icon buttons (same style as Google).
- **Copy:** shop and Google disconnect labels shortened to **Desconectar** / **Disconnect** (and matching “…ing” states).
- **Google OAuth UI:** show **Disconnect** only when the API reports OAuth connected; `?gsc=connected` alone no longer shows a revoke button before status confirms.
- Issue #27 test `RESULTS.md` updated for OAuth fix and removed local demo shops.

### Removed

- Local demo Docker stacks `.local-shops/` (WooCommerce + PrestaShop) from the repo; demo containers torn down on the server.

---

## [2026-09-30] — Optimizator branch snapshot

### Added

- **Append-only AEO inject** (#27): HTML markers `<!-- AEO:START v1 -->` / `<!-- AEO:END -->`, replace-in-block, SEO metas-only path for Odoo.
- **Multi-platform connections:** per-platform revoke in `connection_store`; catalog assistant API and `CatalogWizard`.
- **OAuth order context:** encoded `state` with `license`, `site`, `assistant`; `frontend/src/wizard/orderContext.js` and `sessionStorage` recovery when returning with `gsc=connected`.
- Wizard UX: Expediente collapsed by default; connected shop hides connect form; Google block two-column layout.

### Fixed

- Google consent redirect landing on “Pedido requerido” without license/site query params.
- Revoking one platform no longer cleared all platform connections.

---

## [2026-09-29] — Theme and customer copy

### Added

- Light default theme and Odoo iframe theme bridge (`9d250cf`).

### Changed

- Customer-facing copy hides Core/Ollama/infra details where required by product rules.
