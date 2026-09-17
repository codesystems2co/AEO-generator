# RESULTS — Google→Wizard OAuth consent formal gate

**Date:** 2026-09-15 (Europe/Madrid)  
**Global:** **PASS**  
**UI:** http://2.28.106.22:9012/ `#google` · `#wizard`  
**API:** http://2.28.106.22:8642  
**PM E2E:** codesystems.co@gmail.com → `gsc=connected`  
**Callback:** https://arkiphere.cloud/aeo/google/oauth/callback  

## Accept

| Check | Result |
|-------|--------|
| API oauth configured + **connected** | **PASS** |
| Readiness Client consent OK + GSC property visible | **PASS** (7/9; meta/H1 page gaps unrelated) |
| UI #google shows consent granted / checklist OK | **PASS** |
| UI #wizard Google oauth chip + Continue to AEO | **PASS** |
| Public callback 307 | **PASS** |

## Step log

| Step | Result | Detail |
|------|--------|--------|
| api_google_connected | **PASS** | {'configured': True, 'connected': True, 'client_id_set': True, 'redirect_uri': 'https://arkiphere.cloud/aeo/google/oauth |
| api_readiness_consent | **PASS** | passed=7/9 |
| ui_google_connected | **PASS** | ◇
AEO / SEO Generator
①
Wizard
G
Google Search
☰
Ollama Packs
⇄
Connectors
💬
Chat IA
📖
Guide
◇
Meta Tags
◆
Keywords
▣
Co |
| ui_wizard_consent_path | **PASS** | ◇
AEO / SEO Generator
①
Wizard
G
Google Search
☰
Ollama Packs
⇄
Connectors
💬
Chat IA
📖
Guide
◇
Meta Tags
◆
Keywords
▣
Co |
| ui_wizard_continue_aeo | **PASS** | ◇
AEO / SEO Generator
①
Wizard
G
Google Search
☰
Ollama Packs
⇄
Connectors
💬
Chat IA
📖
Guide
◇
Meta Tags
◆
Keywords
▣
Co |
| callback_public_307 | **PASS** | https://arkiphere.cloud/aeo/google/oauth/callback → 307 (PM+precheck) |

## Env notes (not consent FAIL)

- Core `:18642` still down from generator (badge Core down).
- Page SEO gaps (meta description / H1) on arkiphere.cloud — separate from OAuth gate.

## Evidence

`qa/evidence/2026-09-15_aeo_generator_oauth_consent/` — RESULTS, SCREEN_REVIEW, screenshots, api_*.json
