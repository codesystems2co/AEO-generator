import { copyFor, localeOf } from '../i18n/copy'

const GAP_KEYS = {
  'Live URL fetch': 'live',
  'Title tag': 'title',
  'Meta description': 'meta',
  'H1 present': 'h1',
  'robots.txt': 'robots',
  'sitemap.xml': 'sitemap',
  'Client consent': 'consent',
  'GSC property visible': 'property',
  'Commerce signals': 'commerce',
  'Structured data': 'schema',
}

function headingLabel(value) {
  if (value && typeof value === 'object') return String(value.text || value.title || value.heading || '').trim()
  const text = String(value ?? '').trim()
  const match = text.match(/['"]text['"]\s*:\s*(['"])([\s\S]*?)\1/)
  return match ? match[2].trim() : text
}

function hostOf(url) {
  try {
    return new URL(url).host.replace(/^www\./i, '') || url
  } catch {
    return url || ''
  }
}

function publicConnection(connection) {
  const row = connection?.connection || connection || {}
  return {
    connected: Boolean(connection?.connected || row.connected),
    platform: row.platform,
    url: row.url,
    database: row.database,
    username: row.username,
    sale_order_name: connection?.sale_order_name || row.sale_order_name,
    arkiphere: row.arkiphere || connection?.arkiphere || {},
    updated_at: row.updated_at,
  }
}

export function buildJobPayload({
  entitlement,
  siteUrl,
  platform,
  connection,
  google,
  pack,
  inject,
  googleConnected,
  connectDone,
}) {
  const conn = publicConnection(connection)
  return {
    site_url: siteUrl,
    sale_order_name: entitlement?.sale_order_name || conn.sale_order_name,
    platform: platform || conn.platform,
    connect_done: Boolean(connectDone || conn.connected),
    google_connected: Boolean(googleConnected),
    locale: localeOf(entitlement?.lang),
    connection: conn,
    google: google
      ? {
          step_complete: google.step_complete,
          gaps: google.gaps,
          remediation: google.remediation,
        }
      : null,
    pack: pack
      ? {
          topic: pack.topic,
          backend: pack.backend,
          aeo: pack.aeo,
          seo: pack.seo,
          tree: pack.tree,
        }
      : null,
    inject: inject
      ? {
          ok: inject.ok,
          customer_message: inject.customer_message,
          message: inject.message,
        }
      : null,
  }
}

export function buildProgress({ connectDone, googleDone, aeoDone, seoDone, inject, loading, step, lang }) {
  const t = copyFor(lang)
  const items = [
    { id: 'connect', label: t.progress.connect, detail: t.progress.connectDetail, weight: 20, done: Boolean(connectDone), icon: 'plug' },
    { id: 'google', label: t.progress.google, detail: t.progress.googleDetail, weight: 20, done: Boolean(googleDone), icon: 'search' },
    { id: 'aeo', label: t.progress.aeo, detail: t.progress.aeoDetail, weight: 20, done: Boolean(aeoDone), icon: 'chat' },
    { id: 'seo', label: t.progress.seo, detail: t.progress.seoDetail, weight: 15, done: Boolean(seoDone), icon: 'tag' },
    { id: 'inject', label: t.progress.publish, detail: t.progress.publishDetail, weight: 20, done: Boolean(inject?.ok), icon: 'upload' },
    {
      id: 'report',
      label: t.progress.report,
      detail: t.progress.reportDetail,
      weight: 5,
      done: Boolean(connectDone && googleDone && aeoDone && seoDone && inject),
      icon: 'file',
    },
  ]
  const percent = items.reduce((sum, item) => sum + (item.done ? item.weight : 0), 0)
  const current = items.find((item) => !item.done) || items[items.length - 1]
  return { items, percent: Math.min(100, percent), current, loading: Boolean(loading), step }
}

export function assistantLine({ loading, step, percent, inject, connectDone, lang }) {
  const t = copyFor(lang)
  if (loading && step === 1) return t.assistant.load1
  if (loading && step === 2) return t.assistant.load2
  if (loading && step === 3) return t.assistant.load3
  if (loading && step === 4 && !inject) return t.assistant.load4seo
  if (loading && step === 4) return t.assistant.load4pub
  if (percent >= 100) return t.assistant.done
  if (inject && !inject.ok) return t.assistant.injectFail
  if (!connectDone) return t.assistant.waitShop
  if (percent >= 80) return t.assistant.waitPublish
  if (percent >= 60) return t.assistant.packReady
  if (percent >= 40) return t.assistant.googleReady
  return t.assistant.walking
}

function node(label, value, status, children, icon) {
  const item = { label }
  if (value) item.value = value
  if (status) item.status = status
  if (icon) item.icon = icon
  if (children?.length) item.children = children
  return item
}

export function buildClientTree({ payload, googleConnected, lang }) {
  const t = copyFor(lang)
  const connection = payload?.connection || {}
  const google = payload?.google || {}
  const pack = payload?.pack || {}
  const inject = payload?.inject || {}
  const aeo = pack.aeo || {}
  const seo = pack.seo || {}
  const faqs = aeo.questions_answers || []
  const h2s = aeo.structured_sections || []
  const entities = aeo.key_entities || []
  const keywords = seo.keywords || []
  const score = seo.score || {}
  const hidden = new Set(['OAuth client configured', 'Service account key', 'GSC property share', 'Auth mode selected'])
  const gaps = (google.gaps || []).filter((gap) => !hidden.has(gap.name)).map((gap) => {
    const consent = gap.name === 'Client consent'
    const passed = consent && googleConnected ? true : Boolean(gap.virtual_passed || gap.passed)
    const auto = Boolean(gap.virtual_passed && !gap.passed && !(consent && googleConnected))
    const gapKey = GAP_KEYS[gap.name]
    return node(
      gapKey ? t.gaps[gapKey] : gap.name,
      passed ? (auto ? t.gaps.auto : t.gaps.done) : t.gaps.wait,
      passed ? 'done' : 'pending',
    )
  })
  return [
    node(t.tree.order, payload.sale_order_name || '—', payload.sale_order_name ? 'done' : 'pending', [
      node(t.wizard.site, hostOf(payload.site_url) || payload.site_url || '—', payload.site_url ? 'done' : 'pending'),
    ], 'order'),
    node(t.progress.connect, connection.platform || t.progress.connectDetail, connection.connected ? 'done' : 'pending', [
      node(
        t.step.complete,
        connection.connected ? t.connect.shopOk.replace('{platform}', connection.platform || '') : t.step.pending,
        connection.connected ? 'done' : 'pending',
      ),
      node(
        t.connect.googleKicker.split('·')[0].trim(),
        googleConnected ? t.tree.googleOn : t.tree.googleOff,
        googleConnected ? 'done' : 'pending',
      ),
    ], 'plug'),
    node(t.progress.google, t.progress.googleDetail, google.step_complete ? 'done' : 'pending', [
      node(t.tree.competitors, t.tree.competitorsCopy, google.step_complete ? 'done' : 'info'),
      node(t.tree.demand, t.tree.demandCopy, google.step_complete ? 'done' : 'info'),
      ...gaps,
    ], 'search'),
    node(t.tree.aeo, aeo.suggested_title || t.progress.aeoDetail, aeo.suggested_title ? 'done' : 'pending', [
      node(t.tree.summary, aeo.summary || t.step.pending, aeo.summary ? 'done' : 'pending'),
      node(t.tree.entities, entities.length ? entities.slice(0, 10).join(', ') : t.step.pending, entities.length ? 'done' : 'pending'),
      node(`${t.tree.faq} (${faqs.length})`, null, faqs.length ? 'done' : 'pending', faqs.map((qa) => node(qa.question, qa.answer, 'done'))),
      node(`${t.tree.sections} (${h2s.length})`, null, h2s.length ? 'done' : 'pending', h2s.map((h) => node(headingLabel(h), null, 'done'))),
    ], 'chat'),
    node(t.tree.seo, seo.title || t.progress.seoDetail, seo.title ? 'done' : 'pending', [
      node(t.seo.title, seo.title || t.step.pending, seo.title ? 'done' : 'pending'),
      node(t.seo.description, seo.meta_description || t.step.pending, seo.meta_description ? 'done' : 'pending'),
      node(t.tree.keywords, keywords.length ? keywords.slice(0, 12).join(', ') : t.step.pending, keywords.length ? 'done' : 'pending'),
      node(t.tree.score, score.overall_score != null ? `${score.overall_score}/${score.max_score} · ${score.grade}` : t.step.pending, score.overall_score != null ? 'done' : 'pending'),
    ], 'tag'),
    node(t.progress.publish, inject.ok ? t.progress.publish : (inject?.skipped ? t.seo.skipPublish : t.step.pending), inject?.ok ? 'done' : (inject?.skipped ? 'info' : (inject ? 'warn' : 'pending')), [
      node(t.step.complete, inject?.customer_message || inject?.message || t.step.pending, inject?.ok ? 'done' : (inject?.skipped ? 'info' : (inject ? 'warn' : 'pending'))),
    ], 'upload'),
  ]
}
