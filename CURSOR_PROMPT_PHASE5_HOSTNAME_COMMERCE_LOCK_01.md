# Cursor — Hostname commerce lock (one purchase per shop + server SoT)

**Date:** 2026-09-16  
**Plan:** `docs/process/PLAN_AEO_HOSTNAME_COMMERCE_LOCK.md`  
**Alex rule:** Hostname prevents multi-use; one Optimizator buy per commerce name; preload from that name; not editable; DevTools tamper must fail server-side.

## Do not

- Break product 109 / skip-VPS / license mint / Open AEO deep link.  
- Payment gateways. GitHub OAuth. kubectl rollout restart.  
- Stack duplicate full prompts — one Agent thread.

## Host order (ONE SSH at a time)

### 1) arkiphere_ce — `aeo_base`

1. Normalize host helper (reuse `url_validate` / display hostname) → lowercase FQDN without scheme/path.
2. **Uniqueness:** Before cart add / on confirm for pack lines, block if another pack line on `sale`/`done` already has the same normalized host (any partner or same partner — prefer **global per host** so one commerce = one active entitlement). Cancelled/draft ignored. Clear Spanish/English error: already active for this commerce; open existing order / Open AEO.
3. Optional SQL/Python constraint on normalized host for active pack lines (document migration if needed).
4. Consume may accept optional `site` and return `allowed:false` if provided site normalizes ≠ line site (still return order site when key valid and site omitted).
5. `-u aeo_base` + `kill -HUP 1`. Tests for uniqueness + normalize.

### 2) aeo_generator — UI + API

1. After consume success: set site **only** from `data.aeo_site_url`; mark locked.
2. Landing + wizard: site input **readOnly** (and license readOnly when unlocked via query). Remove `onChange` that edits commerce URL once locked.
3. All pack/Google/connector calls: send license key; **API overwrites/forces `site_url` from consume** — never trust client body for host.
4. If client sends mismatched `site_url`, return 403/400 with clear message; do not generate packs for wrong host.
5. Rebuild live `:9012` / `:8642`.

## Acceptance

- [ ] Second confirmed purchase same hostname blocked on Arkiphere.  
- [ ] Open AEO preloads host; UI cannot edit host.  
- [ ] DevTools change of input or forged API `site_url` rejected; SoT remains order host.  
- [ ] Existing unlock for valid license still works.  
- [ ] Evidence MD + screenshots under `_bmad-output/2026-09-16_hostname_lock/` + READY.  
- [ ] Priority READY with paths.

## Tester will verify (PM)

Formal gate including DevTools/API tamper cases.
