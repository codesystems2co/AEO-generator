# SCREEN_REVIEW — order → wizard gate

**Date:** 2026-09-16  
**Rule:** visual + live Playwright (no product code)

| File | Expected | Visible | Tester |
|------|----------|---------|--------|
| `screenshots/01-license-invalid-blocked.png` | INVALID → Sin pedido; Comenzar disabled | PEDIDO REQUERIDO; badge Sin pedido; Clave INVALID; Sitio https://www.example.com; Comenzar dimmed/disabled | **PASS** md5 `bef29765a0fd4fcddb72390ac8f42f4d` |
| `screenshots/02-license-allowed-begin.png` | Allowed S00245; Comenzar enabled | Pedido S00245; Clave AEO-EyXd…Aa0A (full in field); Sitio example.com; “Pedido confirmado S00245…”; Comenzar enabled | **PASS** md5 `caf73355b4d042e9c225a472f4e98616` |
| `screenshots/03-wizard-google-first.png` | Wizard Google→AEO→SEO; Pedido S00245 | ASISTENTE; Empezamos por Google Search, luego pack AEO y SEO; badge Pedido S00245; PASO 1 — GOOGLE SEARCH; URL example.com | **PASS** md5 `ae40872af7c4e1731acda82aab88afbf` |
| `live_playwright/live-01-invalid-blocked.png` | Live invalid | Same blocked gate as 01 | **PASS** md5 `2c8cf1480bce6064780489325f22af51` |
| `live_playwright/live-02-allowed-begin.png` | Live allowed | Auto-wizard Pedido S00245 / Google first (gate auto-consumed) | **PASS** md5 `ef36815c128dd046e3ab7dd5b83f7f09` |
| `live_playwright/live-03-wizard-google-first.png` | Live wizard | Same as live-02 (identical md5) | **PASS** md5 `ef36815c128dd046e3ab7dd5b83f7f09` |

## Global visual
**PASS** — distinct prior evidence md5s for 01/02/03; live confirms invalid block + allowed wizard path.
