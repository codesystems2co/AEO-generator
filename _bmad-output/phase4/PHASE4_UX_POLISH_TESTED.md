# Phase 4 — Product UX polish tested

**READY** — 2026-09-15

| Item | Value |
|------|--------|
| Open UI | http://2.28.106.22:9012/?gsc=connected#wizard |
| Product | **Search Engine Optimizator** (Arkiphere logo in header) |
| Images | `anyapp/aeo-generator-frontend:local` and `anyapp/aeo-generator-api:local` (`phase4-2026-09-15`) |

## Live checks

| Step | Action | Result | Evidence |
|------|--------|--------|----------|
| Branding | Open live URL | Title + header **Search Engine Optimizator**. AP Arkiphere mark. No Core/Ollama/oauth chips. | `screenshots/01-branding-tienda.png` |
| Paso 1 Tienda | Odoo + URL + **Comprobar conexión** | Connection attempted first. Honest “no pudimos comprobar… puedes continuar”. Continuar enables. | `screenshots/02-tienda-verify.png` |
| Google consent | Continuar with `?gsc=connected` | ✓ Acceso a Search Console concedido. No ○ “User must grant…”. | `screenshots/03-google-consent.png` |
| Google review | **Revisar y mejorar el sitio** | Spanish labels. Completo / Pendiente / Auto-corregido. | `screenshots/04-google-completo.png` |
| AEO pack | Tema / Negocio / Hechos (no PaaS/K8s defaults). Ollama genera el árbol. | Pack tree from business inputs. | `screenshots/05-aeo-pack.png` |
| SEO pack | Continuar | Same wizard shell, tree resume. | `screenshots/06-seo-pack.png` |
| Publicar | **Publicar y comprobar** | **No se publicó**. Escritura/comprobación fallida. Human copy. Success not faked. No `:18642`. | `screenshots/07-publicar-fail.png` |

## Core / shop gap

The shop could not be reached for publish. The UI says the store is unavailable and that a correct result was **not** simulated. Start the store connector service if publish PASS is required.

## Tester formal gate (2026-09-15 evening)

**PASS.** Evidence: `qa/evidence/2026-09-15_phase4_ux/` (`RESULTS.md`, `SCREEN_REVIEW.md`). Live walk confirmed AEO/SEO pack generate + Publicar honest FAIL. Soft note: AEO step prose still mentions Ollama (not a tech chip).
