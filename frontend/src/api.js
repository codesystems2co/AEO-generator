const API_BASE = import.meta.env.VITE_API_URL || (
  typeof window !== 'undefined'
    ? `${window.location.protocol}//${window.location.hostname}:8642`
    : ''
)

let licenseKey = ''

export function setLicense(key) {
  licenseKey = (key || '').trim()
}

export function getLicense() {
  return licenseKey
}

// User-friendly field name mapping
const FIELD_LABELS = {
  title: 'Title',
  meta_description: 'Meta description',
  content: 'Content',
  url: 'URL',
  text: 'Text',
  topic: 'Topic',
  keywords: 'Keywords',
  business_name: 'Business name',
  location: 'Location',
  city: 'City',
  country: 'Country',
  latitude: 'Latitude',
  longitude: 'Longitude',
  site_url: 'Site URL',
  json_key: 'Service account JSON',
}

function formatFieldName(loc) {
  const field = loc?.slice(1).join('.') || 'field'
  return FIELD_LABELS[field] || field
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(licenseKey ? { 'X-AEO-License': licenseKey } : {}),
      ...options.headers,
    },
  })
  if (!res.ok) {
    let errorData = null
    let errorMessage = res.statusText
    try {
      errorData = await res.json()
      if (errorData.detail && Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail
          .map((d) => {
            const field = formatFieldName(d.loc)
            let msg = d.msg
            if (d.type === 'string_too_long') {
              msg = `Must be at most ${d.ctx?.max_length} characters`
            } else if (d.type === 'string_too_short') {
              msg = `Must be at least ${d.ctx?.min_length} characters`
            } else if (d.type === 'missing') {
              msg = 'This field is required'
            }
            return `${field}: ${msg}`
          })
          .join('\n')
      } else if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail)
      } else if (errorData.message) {
        errorMessage = errorData.message
      } else if (errorData.error) {
        errorMessage = errorData.error
      }
    } catch {
      // Response wasn't JSON
    }
    const err = new Error(errorMessage)
    err.status = res.status
    err.data = errorData
    throw err
  }
  return res.json()
}

export const api = {
  meta: {
    generate: (body) => request('/api/meta/generate', { method: 'POST', body: JSON.stringify(body) }),
  },
  keywords: {
    extract: (body) => request('/api/keywords/extract', { method: 'POST', body: JSON.stringify(body) }),
  },
  analysis: {
    content: (body) => request('/api/analysis/content', { method: 'POST', body: JSON.stringify(body) }),
  },
  aeo: {
    suggest: (body) => request('/api/aeo/suggest', { method: 'POST', body: JSON.stringify(body) }),
  },
  score: {
    calculate: (body) => request('/api/score/calculate', { method: 'POST', body: JSON.stringify(body) }),
  },
  nlp: {
    keywords: (body) => request('/api/nlp/keywords', { method: 'POST', body: JSON.stringify(body) }),
    readability: (body) => request('/api/nlp/readability', { method: 'POST', body: JSON.stringify(body) }),
  },
  url: {
    analyze: (body) => request('/api/url/analyze', { method: 'POST', body: JSON.stringify(body) }),
  },
  external: {
    moz: (body) => request('/api/external/moz', { method: 'POST', body: JSON.stringify(body) }),
    semrush: (body) => request('/api/external/semrush', { method: 'POST', body: JSON.stringify(body) }),
  },
  geo: {
    analyze: (body) => request('/api/geo/analyze', { method: 'POST', body: JSON.stringify(body) }),
    optimize: (body) => request('/api/geo/optimize', { method: 'POST', body: JSON.stringify(body) }),
    citations: (body) => request('/api/geo/citations', { method: 'POST', body: JSON.stringify(body) }),
  },
  chat: {
    send: (body) => request('/api/chat/', { method: 'POST', body: JSON.stringify(body) }),
    health: () => request('/api/chat/health'),
  },
  google: {
    status: () => request('/api/google/status'),
    readiness: (body) => request('/api/google/readiness', { method: 'POST', body: JSON.stringify(body) }),
    oauthStart: () => request('/api/google/oauth/start', { method: 'POST', body: '{}' }),
    sites: () => request('/api/google/sites'),
    saSession: (body) => request('/api/google/sa/session', { method: 'POST', body: JSON.stringify(body) }),
  },
  packs: {
    health: () => request('/api/packs/health'),
    generate: (body) => request('/api/packs/generate', { method: 'POST', body: JSON.stringify(body) }),
  },
  connectors: {
    health: () => request('/api/connectors/health'),
    platforms: () => request('/api/connectors/platforms'),
    write: (body) => request('/api/connectors/write', { method: 'POST', body: JSON.stringify(body) }),
    verify: (body) => request('/api/connectors/verify', { method: 'POST', body: JSON.stringify(body) }),
  },
  wizard: {
    status: () => request('/api/wizard/status'),
    run: (body) => request('/api/wizard/run', { method: 'POST', body: JSON.stringify(body) }),
    autofix: (body) => request('/api/wizard/google/autofix', { method: 'POST', body: JSON.stringify(body) }),
    injectVerify: (body) => request('/api/wizard/inject-verify', { method: 'POST', body: JSON.stringify(body) }),
  },
  entitlement: {
    consume: (key, github_login, site) => request('/api/entitlement/consume', {
      method: 'POST',
      body: JSON.stringify({
        key: key || '',
        github_login: github_login || undefined,
        site: site || undefined,
      }),
    }),
  },
  connection: {
    status: () => request('/api/connection/status'),
    register: (body) => request('/api/connection/register', { method: 'POST', body: JSON.stringify(body) }),
    revoke: (body) => request('/api/connection/revoke', { method: 'POST', body: JSON.stringify(body || {}) }),
  },
  health: () => request('/health'),
}
