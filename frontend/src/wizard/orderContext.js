export const ORDER_STORAGE_KEY = 'aeo_order'

/** Commerce site from the order — not the technical shop instance on the order line. */
export function isGatewayShopHost(site) {
  const raw = (site || '').trim().toLowerCase()
  if (!raw) return false
  try {
    const host = new URL(raw.includes('://') ? raw : `https://${raw}`).hostname.toLowerCase()
    return (
      host.endsWith('.aeo.local')
      || host === 'localhost'
      || host.startsWith('127.')
      || host.startsWith('10.')
      || host.startsWith('192.168.')
    )
  } catch {
    return raw.includes('.aeo.local') || raw.includes('localhost')
  }
}

export function normalizeCommerceSite(site) {
  return (site || '').trim()
}

export function restoreOrder() {
  try {
    const raw = sessionStorage.getItem(ORDER_STORAGE_KEY)
    const row = raw ? JSON.parse(raw) : {}
    return {
      license: String(row.license || '').trim(),
      site: String(row.site || '').trim(),
      githubLogin: String(row.githubLogin || '').trim(),
      assistant: String(row.assistant || '').trim(),
    }
  } catch {
    return { license: '', site: '', githubLogin: '', assistant: '' }
  }
}

export function persistOrder({ license, site, githubLogin, assistant }) {
  try {
    const prev = restoreOrder()
    const next = {
      license: (license || prev.license || '').trim(),
      site: (site || prev.site || '').trim(),
      githubLogin: (githubLogin || prev.githubLogin || '').trim(),
      assistant: (assistant || prev.assistant || '').trim(),
    }
    if (!next.license && !next.site) return
    sessionStorage.setItem(ORDER_STORAGE_KEY, JSON.stringify(next))
  } catch {
    /* ignore */
  }
}

export function writeOrderQuery({ license, site, githubLogin, assistant, gscHint }) {
  try {
    const params = new URLSearchParams(window.location.search)
    if (license) params.set('license', license)
    else params.delete('license')
    if (site) params.set('site', site)
    else params.delete('site')
    if (githubLogin) params.set('user', githubLogin)
    else params.delete('user')
    if (assistant) params.set('assistant', assistant)
    else params.delete('assistant')
    if (gscHint) params.set('gsc', 'connected')
    else params.delete('gsc')
    const qs = params.toString()
    const next = qs ? `${window.location.pathname}?${qs}${window.location.hash || ''}` : `${window.location.pathname}${window.location.hash || ''}`
    window.history.replaceState({}, '', next)
  } catch {
    /* ignore */
  }
}

export function readOrderQuery() {
  if (typeof window === 'undefined') {
    return { license: '', site: '', githubLogin: '', assistant: '', gscHint: false }
  }
  try {
    const q = new URLSearchParams(window.location.search)
    const saved = restoreOrder()
    const license = (
      q.get('license')
      || q.get('key')
      || q.get('odoo_license_key')
      || saved.license
      || ''
    ).trim()
    const site =
      normalizeCommerceSite(q.get('site') || '')
      || normalizeCommerceSite(q.get('odoo_hostname') || '')
      || normalizeCommerceSite(q.get('odoo_domain_selected') || '')
      || normalizeCommerceSite(saved.site || '')
    const githubLogin = (q.get('user') || saved.githubLogin || '').trim()
    const gscHint = q.get('gsc') === 'connected'
    const hasLicenseParam = !!(q.get('license') || q.get('key') || q.get('odoo_license_key'))
    const hasSiteParam = !!(q.get('site') || q.get('odoo_hostname') || q.get('odoo_domain_selected'))
    let assistant = ''
    if (q.has('assistant')) {
      assistant = (q.get('assistant') || '').trim()
    } else if (gscHint && !(hasLicenseParam || hasSiteParam)) {
      assistant = (saved.assistant || '').trim()
    } else if (!hasLicenseParam && !hasSiteParam && saved.assistant) {
      assistant = saved.assistant.trim()
    }
    if (license || site || assistant || githubLogin) {
      persistOrder({ license, site: site || undefined, githubLogin, assistant })
    }
    if (gscHint && license && (!q.get('license') || !q.get('site'))) {
      writeOrderQuery({
        license,
        site: site || undefined,
        githubLogin,
        assistant,
        gscHint: true,
      })
    }
    return { license, site, githubLogin, assistant, gscHint }
  } catch {
    return { license: '', site: '', githubLogin: '', assistant: '', gscHint: false }
  }
}
