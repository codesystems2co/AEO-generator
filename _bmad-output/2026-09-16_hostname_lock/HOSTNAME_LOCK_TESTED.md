# Hostname lock + gate UX — tested

**Date:** 2026-09-16  
**Hosts:** arkiphere_ce (`aeo_base` READY_CE) + aeo_generator (live `:9012` / `:8642`)  
**Golden order:** **S00246** (product 109, site `https://www.example.com`, partner 213). Key redacted `AEO-7vb9…TerQ`.

## Board / acceptance

| Item | Result | Proof |
|------|--------|--------|
| Gate UX blocked | **PASS** | Live Wizard: Clave + Comprobar + **Adquirir el pack** only → product 109 URL. No Crear/confirmar, no Entrar. Comenzar hidden until allowed. |
| Sitio not input | **PASS** | Blocked: site row hidden. Allowed: `gate-site-value` read-only label (not `<input>`). Wizard steps also value-only. |
| CE host uniqueness | **PASS** | `READY_CE` + `aeo_base/tests/test_host_lock.py` (8 OK). Global per normalized host on sale/done. |
| Arkiphere consume site mismatch | **PASS** | `GET /aeo/license/consume/http?key=…&site=https://evil.example` → `allowed: false`, still returns order `aeo_site_url`. Matching site → `allowed: true`. |
| Generator consume forwards site | **GAP** | Generator `POST /api/entitlement/consume` with evil site still returned `allowed: true` (does not yet enforce Arkiphere mismatch). UI SoT still overwrites from `aeo_site_url` when present. |
| Packs/google API 403 tamper | **GAP / not proven** | Pack/wizard routes still accept client `site_url` shape; no clear 403 observed in this gate. Follow-up if Tester fails DevTools API cases. |
| Second purchase same host | **PASS (CE)** | Documented in READY_CE live `_aeo_raise_if_host_taken(www.example.com)` Spanish error naming S00246. S00246 not cancelled. |

## Live how to open

- Blocked: http://2.28.106.22:9012/
- Unlocked: Open AEO from portal S00246 (or `?license=AEO-…&site=https%3A%2F%2Fwww.example.com`)

## Screenshots

- `screenshots/01-blocked-adquirir-only.png`
- `screenshots/02-allowed-site-value.png`
- CE: `bmad/_bmad-output/2026-09-16_hostname_lock/READY_CE` on arkiphere_ce

## Note

Gate UX shipped live (Wizard.jsx mtime 2026-09-16 17:05Z). Formal DevTools API 403 may need a short follow-up; Tester can start on live gate UX + CE uniqueness now.
