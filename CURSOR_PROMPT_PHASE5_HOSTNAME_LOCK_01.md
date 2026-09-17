# Cursor — Hostname lock: one Optimizator purchase per commerce

**Date:** 2026-09-16  
**Plan:** `docs/process/PLAN_AEO_HOSTNAME_LOCK.md`  
**Hosts:** ONE SSH at a time. **aeo_generator FIRST**, then arkiphere_ce only if consume SoT still omits site check on pack APIs.

## Business

Hostname on the confirmed order **is** the shop. One active pack per commerce name. Client cannot change it in UI or via DevTools. Prefill Optimizator from that hostname. Server (consume + pack APIs) is source of truth.

## Do not

- GitHub OAuth. Payment. Product 109 flags / skip-VPS. `kubectl rollout restart`.
- Re-open Asistente/Herramientas.
- Stack a second Composer thread if this prompt is already running.

## A) aeo_generator

Live UI `:9012` API `:8642`. Workspace `/root/anyapp-github-build/AEO-generator`.

1. **UI lock** (`frontend/src/tabs/Wizard.jsx`): after Open AEO / consume, **license** and **site** are display-only (`readOnly`/`disabled`, no `onChange` that mutates). Prefill `businessName` from hostname (host label; strip `www.` if useful). Do not let packs start on a different host than `entitlement.aeo_site_url`.
2. **Consume:** `api.entitlement.consume` POST `{ key, site, github_login? }` using query `site` **and** always overwrite local site from response `aeo_site_url`.
3. **API lock:** `entitlement_service.consume` forwards `site`. Wizard/google/pack routes: require activation `license` (header or body); re-call consume; if provided `site_url` host ≠ order host → **403** with honest message. Generate/readiness **use order site**, not the tampered body.
4. Rebuild live `:9012`/`:8642`.

## B) arkiphere_ce (`aeo_base`) — only if needed

Uniqueness already exists (`_aeo_raise_if_host_taken`, constrain). Keep it.

- Consume: mismatch → `allowed: false`. Omitted site may stay allowed (mail link) but **always** return line `aeo_site_url`.
- Confirm second sale/done pack for same normalized host still raises.
- Reload: `-u aeo_base` then `kill -HUP 1`.

## Acceptance

- [ ] Same hostname second buy blocked (live or unittest + one live cart if possible without wrecking S00246).
- [ ] Wizard: license + site not editable; business prefilled from host.
- [ ] Consume key S00246 + `site=https://evil.example` → allowed false.
- [ ] Pack/google POST tampered site_url → 403 or still bound to order host.
- [ ] Evidence `_bmad-output/2026-09-16_hostname_lock/` + READY + screenshots (readonly fields, consume mismatch JSON redacted).

Priority READY when live.
