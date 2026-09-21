/** Odoo iframe theme bridge — URL param boot + live postMessage sync. */

function normalizeTheme(value) {
  if (!value) return 'light'
  const v = String(value).toLowerCase()
  return v === 'dark' ? 'dark' : 'light'
}

function applyTheme(theme) {
  const t = normalizeTheme(theme)
  document.documentElement.dataset.theme = t
  document.documentElement.classList.toggle('theme-dark', t === 'dark')
}

function readUrlTheme() {
  const params = new URLSearchParams(window.location.search)
  return params.get('odoo_theme') || params.get('theme')
}

export function initThemeBridge() {
  applyTheme(readUrlTheme() || 'light')

  window.addEventListener('message', (event) => {
    const data = event.data
    if (!data || typeof data !== 'object') return
    if (data.type !== 'odoo_theme') return
    if (data.source && data.source !== 'aeo_license') return
    applyTheme(data.theme)
  })
}
