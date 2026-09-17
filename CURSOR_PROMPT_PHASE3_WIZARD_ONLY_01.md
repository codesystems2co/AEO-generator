# Cursor Agent — Phase 3: Wizard-only UI + Continuar/Atrás + auto-fix + inject verify

## Product direction (Alex 2026-09-15)
Live UI: http://2.28.106.22:9012/ (`AEO-generator` / SSH `aeo_generator` / `/root/anyapp-github-build/AEO-generator`)

1. **Keep only the step wizard** as the customer experience. Hide or remove loose top tabs (Chat, Meta Tags, Keywords, …) from the primary chrome (advanced/dev escape hatch OK if behind a clear control).
2. **Step 1 — Google Search (GSC):** generate/read site state, **calculate** remaining gaps, and have **Ollama automatically solve** persistent commerce issues before the step is complete.
3. **Navigation:** explicit **Continuar** / **Atrás** buttons between packs. Continuar enabled only when the current step is complete.
4. **Following packs:** after Google Search is fully solved, Continuar → AEO pack → SEO pack (tree resume), same wizard shell.
5. **Final step:** verify the solution was **really injected** across platform surfaces (Core connectors Odoo/Presta/Woo write+verify). Show PASS/FAIL per surface. If Core unreachable from this host, fail clearly and document; do not fake inject success.

## Workspace rules
- **One** SSH session: `AEO-generator [SSH: aeo_generator]` only. No second arkiphere_ce window for this epic.
- Implement in this React/Vite + FastAPI repo. **No** new `aeo-platform/ui/*` light HTML.
- After code changes: rebuild/redeploy local images (`anyapp/aeo-generator-frontend:local` and/or `anyapp/aeo-generator-api:local`) so pods are durable (pod file-copy is ephemeral).
- BMAD screenshot rule applies for evidence: keep screenshots matching the tested step.

## Implementation order
1. Wizard-only shell + Continuar/Atrás state machine
2. Google Search step: readiness + gap calc + Ollama auto-remediation loop until complete (or hard blockers listed)
3. Wire AEO then SEO pack steps into the same wizard
4. Final inject-verify step via existing `/api/connectors/*` → Core
5. Illustrated note: `_bmad-output/phase3/PHASE3_WIZARD_ONLY_TESTED.md` + evidence screenshots
6. READY marker: `_bmad-output/phase3/READY`

## Acceptance
- [ ] Default route opens Wizard-only UX (no primary tab bar clutter)
- [ ] Continuar / Atrás work; Continuar gated on step completion
- [ ] Google Search step auto-solves via Ollama where possible
- [ ] AEO + SEO packs reachable only through wizard navigation
- [ ] Final verify shows real inject results (or honest Core-down)
- [ ] Live UI updated on :9012 after image rebuild
- [ ] READY + tested MD

## Related live facts
- OAuth multi-user already PASS (redirect `https://arkiphere.cloud/aeo/google/oauth/callback`)
- API :8642 / UI :9012
- Core default `http://172.17.0.1:18642` may be down from this node

When finished: priority READY to PM with files changed + how to open UI + any Core gap.
