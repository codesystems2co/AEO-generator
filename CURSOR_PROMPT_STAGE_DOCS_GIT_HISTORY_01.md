# Cursor — Stage freeze: PaaS docs + rich git history push

**Date:** 2026-09-16  
**Priority:** Documentation + git hygiene for AI-agent future ecosystems.  
**Hosts:** Prefer `arkiphere_ce` first (ARKISPHERE), then `aeo_generator` (Optimizator fork). One SSH window at a time.

## Security first (blocking)

1. On CE `18.0`, `git remote get-url origin` currently embeds a `ghp_` PAT.  
2. **Rewrite** to `https://github.com/codesystems2co/ARKISPHERE.git` (no token in URL).  
3. Auth via `gh auth` / credential helper / SSH — never print the old token.  
4. Tell Alex (via READY note) to **rotate** that PAT in GitHub.  
5. Never commit `client_secret*.json`, `.env`, or tokens.

## A) Documentation deliverable

Create/update under `bmad/`:

- `docs/process/WORKFLOW_PAAS_CONTEXT_REFERENCE.md` (copy from Mac/handoff if needed)  
- `docs/process/STAGE_AEO_OPTIMIZATOR_CAPABILITY_MAP.md` — map Project Done cards → modules/paths  
- `stories/feature/STORY_stage_docs_git_history.md` — what was pushed  

Include commerce connectors intent: Odoo / Presta / Woo addons as the solution surface Arkiphere supplies.

## B) ARKISPHERE (`18.0` on arkiphere_ce)

Repo: `codesystems2co/ARKISPHERE`, branch `main`, **already ahead 9** of origin.

1. Fix remote (no PAT).  
2. Review unstaged/untracked: commit **aeo_base / aeo_gsc / so_server / sh_subscription / bmad evidence+handoff** with **rich messages** (feat/docs/fix) grouped by feature.  
3. **Exclude** unless Alex asked: `.cursor/skills/gstack*`, `node_modules`, `bmad/resources/superpowers` huge vendor, secret json.  
4. Push `main` (or open PR if policy requires — prefer push if this is the team main).  
5. Messages must explain *why* (entitlement, no-VPS, hostname lock, portal guide, etc.).

Example style:

```
feat(aeo_base): lock Optimizator to one purchase per commerce hostname

Normalize host on cart/confirm; reject duplicate sale/done lines;
consume RPC returns allowed:false on site mismatch. Evidence under
bmad/_bmad-output/2026-09-16_hostname_lock/.
```

## C) AEO-generator

Checkout is **upstream** `gwrxuk/AEO-generator`. Do **not** force-push upstream.

1. Create/use fork under `codesystems2co` or `Arkiphere` (or `thedeployer777`) named e.g. `AEO-generator` / `search-engine-optimizator`.  
2. Add `fork` remote; commit local Optimizator work (wizard gate, entitlement consume, packs, GSC, branding) in logical rich commits.  
3. Push fork branch; optional PR to upstream later.  
4. Do not commit `.bak` files, buildstamps, secrets.

## D) Mac `aeo-platform`

Not a git root today. Either init+push as `aeo-platform` docs/sandbox repo under org, or document that CE `bmad/handoff/aeo-platform` is SoT — pick one and state it in the story.

## Acceptance

- [ ] Remote URLs have **no** embedded PAT  
- [ ] ARKISPHERE push includes aeo_* + BMAD stage docs + evidence (no secrets)  
- [ ] Generator changes on **fork** with rich history  
- [ ] `WORKFLOW_PAAS_CONTEXT_REFERENCE.md` + capability map on CE bmad  
- [ ] READY + STAGE_DOCS_GIT_HISTORY_TESTED.md under `_bmad-output/2026-09-16_stage_docs/`  
- [ ] Priority READY with commit SHAs + repo URLs  

No kubectl rollout restart. No hostname API rework unless idle after this.
