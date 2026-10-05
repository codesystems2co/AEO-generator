/** Derive Paso 3 Tema / Negocio / Hechos from store page (+ optional remediation). */

const TITLE_SPLIT = /\s*[|—·]\s*|\s+-\s+/

function firstNonEmpty(...values) {
  for (const value of values) {
    const text = String(value || '').trim()
    if (text) return text
  }
  return ''
}

function firstH1(page) {
  const list = page?.h1_list
  if (!Array.isArray(list) || !list.length) return ''
  return String(list[0] || '').trim()
}

function splitTitle(title) {
  const raw = String(title || '').trim()
  if (!raw) return { brand: '', topic: '' }
  const parts = raw.split(TITLE_SPLIT).map((part) => part.trim()).filter(Boolean)
  if (parts.length < 2) return { brand: '', topic: raw }
  return { brand: parts[0], topic: parts.slice(1).join(' — ') }
}

function significantTokens(text) {
  return String(text || '')
    .toLowerCase()
    .split(/[^a-z0-9áéíóúüñ]+/i)
    .map((token) => token.trim())
    .filter((token) => token.length >= 3)
}

function isRedundant(haystack, needle) {
  const a = String(haystack || '').trim().toLowerCase()
  const b = String(needle || '').trim().toLowerCase()
  if (!b) return true
  if (!a) return false
  if (a.includes(b) || b.includes(a)) return true
  const needleTokens = significantTokens(b)
  if (!needleTokens.length) return false
  const hayTokens = new Set(significantTokens(a))
  const overlap = needleTokens.filter((token) => hayTokens.has(token)).length
  return overlap / needleTokens.length >= 0.5
}

/**
 * @param {object} page - { title, meta_description, h1_list, og_site_name?, organization_name? }
 * @param {object} [remediation] - optional { title, meta_description, h1, organization_name?, og_site_name? }
 * @param {string} [hostFallback] - hostname stem, last resort only
 * @returns {{ topic: string, business: string, facts: string }}
 */
export function deriveStoreProfile(page = {}, remediation = {}, hostFallback = '') {
  const rem = remediation && typeof remediation === 'object' ? remediation : {}
  const pg = page && typeof page === 'object' ? page : {}

  const title = firstNonEmpty(rem.title, pg.title)
  const meta = firstNonEmpty(rem.meta_description, pg.meta_description)
  const h1 = firstNonEmpty(rem.h1, firstH1(pg))
  const org = firstNonEmpty(rem.organization_name, pg.organization_name)
  const og = firstNonEmpty(rem.og_site_name, pg.og_site_name)
  const host = String(hostFallback || '').trim()
  const { brand: titleBrand, topic: titleTopic } = splitTitle(title)

  const topic = firstNonEmpty(h1, titleTopic, title, host)
  const business = firstNonEmpty(org, og, titleBrand, host)

  const factParts = []
  if (meta) factParts.push(meta)
  if (h1 && !isRedundant(meta, h1)) factParts.push(h1)
  else if (!meta && titleTopic && titleTopic !== h1 && !isRedundant(h1, titleTopic)) {
    factParts.push(titleTopic)
  }
  const facts = factParts.join('\n').trim()

  return { topic, business, facts }
}
