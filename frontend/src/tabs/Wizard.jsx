import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import TreeList from '../components/TreeList'
import '../App.css'

const STEPS = [
  { id: 1, key: 'google', label: 'Google' },
  { id: 2, key: 'aeo', label: 'AEO' },
  { id: 3, key: 'seo', label: 'SEO' },
]

const PRODUCT_PAGE_URL =
  'https://arkiphere.cloud/shop/aeo-optimizator-ia-search-optimizator-pack-aeo-seo-and-google-search-109'

const BLOCKED_COPY = {
  message: 'Si ya tienes una clave, pégala aquí. Si no, adquiere el pack en la ficha del producto.',
  cta_url: PRODUCT_PAGE_URL,
  cta_label: 'Adquirir el pack',
}

const GAP_LABELS = {
  'Live URL fetch': 'Página accesible',
  'Title tag': 'Título',
  'Meta description': 'Descripción',
  'H1 present': 'Encabezado principal',
  'robots.txt': 'Archivo robots',
  'sitemap.xml': 'Mapa del sitio',
  'OAuth client configured': 'Search Console listo',
  'Client consent': 'Acceso a Search Console',
  'GSC property visible': 'Propiedad en Search Console',
  'Service account key': 'Cuenta de servicio',
  'GSC property share': 'Propiedad compartida',
  'Auth mode selected': 'Modo de acceso',
  'Commerce signals': 'Señales de tienda',
  'Structured data': 'Datos estructurados',
}

function readQuery() {
  if (typeof window === 'undefined') {
    return { license: '', site: '', githubLogin: '', gscHint: false }
  }
  try {
    const q = new URLSearchParams(window.location.search)
    return {
      license: (q.get('license') || q.get('key') || '').trim(),
      site: (q.get('site') || '').trim(),
      githubLogin: (q.get('user') || '').trim(),
      gscHint: q.get('gsc') === 'connected',
    }
  } catch {
    return { license: '', site: '', githubLogin: '', gscHint: false }
  }
}

function keepHttps(value) {
  const v = (value || '').trim()
  if (!v) return ''
  if (/^https:\/\//i.test(v)) return v
  if (/^http:\/\//i.test(v)) return `https://${v.slice(7)}`
  return `https://${v.replace(/^\/+/, '')}`
}

function hostLabel(url) {
  try {
    return new URL(keepHttps(url)).host || url
  } catch {
    return url
  }
}

function friendlyGapMessage(name, message, connected) {
  if (name === 'Client consent') {
    return connected ? 'Acceso concedido' : 'Pendiente de autorización'
  }
  if (name === 'OAuth client configured') {
    return 'Disponible'
  }
  if (!message) return ''
  const map = [
    [/User must grant/i, 'Pendiente de autorización'],
    [/Access token present/i, 'Acceso concedido'],
    [/GOOGLE_CLIENT_ID|SECRET/i, 'Listo para conectar'],
    [/Missing meta description/i, 'Falta la descripción'],
    [/0 H1 tag/i, 'Falta el encabezado principal'],
    [/No JSON-LD/i, 'Faltan datos estructurados'],
    [/HTTP 200/i, 'Correcto'],
    [/Price\/cart\/product language found/i, 'La página habla de productos o compra'],
  ]
  for (const [re, label] of map) {
    if (re.test(message)) return label
  }
  if (/GOOGLE_|:18642|Ollama|Core /i.test(message)) return 'Revisar este punto'
  return message
}

function displayGaps(gaps, connected) {
  return (gaps || []).map((g) => {
    const consent = g.name === 'Client consent'
    const passed = consent && connected ? true : Boolean(g.virtual_passed || g.passed)
    const auto = Boolean(g.virtual_passed && !g.passed && !(consent && connected))
    return {
      ...g,
      label: GAP_LABELS[g.name] || g.name,
      passed,
      auto,
      stateLabel: passed ? (auto ? 'Auto-corregido' : 'Completo') : 'Pendiente',
      displayMessage: friendlyGapMessage(g.name, g.message, connected),
    }
  })
}

export default function Wizard() {
  const query = readQuery()
  const [step, setStep] = useState(1)
  const [started, setStarted] = useState(false)
  const [status, setStatus] = useState(null)
  const [siteUrl, setSiteUrl] = useState('')
  const [licenseKey, setLicenseKey] = useState(query.license)
  const [topic, setTopic] = useState('')
  const [businessName, setBusinessName] = useState('')
  const [context, setContext] = useState('')
  const [google, setGoogle] = useState(null)
  const [pack, setPack] = useState(null)
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(Boolean(query.license))
  const [error, setError] = useState(null)
  const [entitlement, setEntitlement] = useState(null)
  const gscHint = query.gscHint
  const githubLogin = query.githubLogin

  async function consumeKey(key) {
    setChecking(true)
    setError(null)
    try {
      const data = await api.entitlement.consume(key, githubLogin || undefined)
      setEntitlement(data)
      if (data?.aeo_site_url) setSiteUrl(keepHttps(data.aeo_site_url))
      return data
    } catch (err) {
      const blocked = {
        allowed: false,
        key,
        message: 'No pudimos comprobar el pedido ahora. Inténtalo de nuevo.',
        ...BLOCKED_COPY,
      }
      setEntitlement(blocked)
      return blocked
    } finally {
      setChecking(false)
    }
  }

  useEffect(() => {
    api.wizard.status().then(setStatus).catch(() => {})
    if (query.license) {
      consumeKey(query.license)
    } else {
      setEntitlement({
        allowed: false,
        ...BLOCKED_COPY,
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!entitlement?.allowed || !query.license) return
    const url = keepHttps(entitlement.aeo_site_url || query.site)
    if (!url) return
    setSiteUrl(url)
    setStarted(true)
    setStep(1)
  }, [entitlement, query.license, query.site])

  const apiConnected = Boolean(
    status?.google?.modes?.oauth?.connected || google?.auth?.modes?.oauth?.connected
  )
  const googleConnected = gscHint || apiConnected

  const googleDone = Boolean(google?.step_complete)
  const aeoDone = Boolean(pack?.aeo)
  const seoDone = Boolean(pack?.seo)
  const complete = { 1: googleDone, 2: aeoDone, 3: seoDone }
  const canContinue = step < 3 && complete[step]

  const gaps = useMemo(
    () => displayGaps(google?.gaps, googleConnected),
    [google, googleConnected]
  )

  async function runAutofix(e) {
    e?.preventDefault()
    if (!entitlement?.allowed) return
    setError(null)
    setLoading(true)
    try {
      const data = await api.wizard.autofix({
        site_url: siteUrl,
        mode: 'oauth',
        topic: businessName || topic || undefined,
        context: context || undefined,
        locale: 'es',
      })
      setGoogle(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function runPack() {
    setError(null)
    if (!entitlement?.allowed) return
    setLoading(true)
    try {
      const data = await api.packs.generate({
        topic: topic.trim() || businessName.trim() || 'Mi tienda',
        url: siteUrl,
        business_name: businessName.trim() || undefined,
        context: context.trim() || undefined,
        locale: 'es',
      })
      setPack(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function goBack() {
    if (step > 1) setStep(step - 1)
  }

  function goNext() {
    if (canContinue) setStep(step + 1)
  }

  const allowed = Boolean(entitlement?.allowed)
  const showGate = !started
  const confirmedSite = keepHttps(entitlement?.aeo_site_url || (allowed ? query.site : '') || siteUrl)
  const acquireUrl = PRODUCT_PAGE_URL
  const acquireLabel = BLOCKED_COPY.cta_label

  if (checking && !entitlement) {
    return (
      <div className="card">
        <h3>Comprobando pedido</h3>
        <p style={{ color: 'var(--text-muted)' }}>Verificando la clave de activación…</p>
      </div>
    )
  }

  if (showGate) {
    return (
      <div className="card">
        <h3>Pedido requerido</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          Si llegas desde Arkiphere con un pedido confirmado, el asistente se abre solo.
          También puedes pegar una clave de activación de otra tienda.
        </p>
        <p>
          <span className={`badge ${allowed ? 'badge-success' : 'badge-warn'}`}>
            {allowed ? `Pedido ${entitlement.sale_order_name}` : 'Sin pedido'}
          </span>
        </p>
        <form
          className="form-row"
          style={{ marginTop: '0.85rem' }}
          onSubmit={(e) => {
            e.preventDefault()
            if (licenseKey.trim()) consumeKey(licenseKey.trim())
          }}
        >
          <label htmlFor="aeo-license">Clave de activación</label>
          <div className="gate-key">
            <input
              id="aeo-license"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value)}
              placeholder="AEO-…"
              autoComplete="off"
            />
            <button type="submit" className="btn btn-secondary" disabled={checking || !licenseKey.trim()}>
              {checking ? 'Comprobando…' : 'Comprobar clave'}
            </button>
          </div>
        </form>
        {allowed && confirmedSite ? (
          <div className="form-row">
            <span className="gate-site-label">Sitio</span>
            <p className="gate-site-value">{hostLabel(confirmedSite)}</p>
          </div>
        ) : null}
        {allowed && entitlement?.message ? (
          <p style={{ marginTop: '0.25rem' }}>{entitlement.message}</p>
        ) : (
          <p style={{ marginTop: '0.25rem' }}>{BLOCKED_COPY.message}</p>
        )}
        {error && <p className="error-msg">{error}</p>}
        {allowed ? (
          <div className="btn-row" style={{ marginTop: '1rem' }}>
            <button
              type="button"
              className="btn"
              disabled={!confirmedSite || checking}
              onClick={() => {
                setSiteUrl(confirmedSite)
                setStarted(true)
                setStep(1)
              }}
            >
              Comenzar asistente
            </button>
          </div>
        ) : (
          <a className="btn gate-acquire" href={acquireUrl}>
            <svg className="gate-acquire-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="currentColor"
                d="M7 18a2 2 0 1 0 0 4 2 2 0 0 0 0-4Zm10 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4ZM3.1 3.3h1.7l.3 1.4h13.8a1 1 0 0 1 1 .8l1.1 6.2a2 2 0 0 1-2 2.3H7.6l.4 2h10.2v2H7.2a2 2 0 0 1-2-2.3L4.1 5.3H2.2l-.1-2ZM7.3 11.7h10.9l.7-4H6.5l.8 4Z"
              />
            </svg>
            {acquireLabel}
          </a>
        )}
      </div>
    )
  }

  return (
    <>
      <div className="card">
        <h3>Asistente de optimización</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Completa cada paso para habilitar Continuar. Empezamos por Google Search, luego el pack AEO y el pack SEO.
        </p>
        <div className="btn-row" style={{ marginBottom: '0.85rem' }}>
          <span className="badge badge-success">Pedido {entitlement.sale_order_name}</span>
        </div>
        <ol className="stepper">
          {STEPS.map((s) => (
            <li key={s.id} className={step === s.id ? 'active' : step > s.id ? 'done' : ''}>
              <button
                type="button"
                disabled={s.id > step && !complete[s.id - 1]}
                onClick={() => {
                  if (s.id <= step) setStep(s.id)
                }}
              >
                <span className="step-num">{s.id}</span>
                {s.label}
              </button>
            </li>
          ))}
        </ol>
      </div>

      {step === 1 && (
        <div className="card">
          <h3>Paso 1 — Google Search</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            Revisamos cómo ve Google tu sitio y corregimos lo que se pueda de forma automática.
          </p>
          <form onSubmit={runAutofix}>
            <div className="form-row">
              <span className="gate-site-label">Sitio</span>
              <p className="gate-site-value">{hostLabel(siteUrl)}</p>
            </div>
            {googleConnected && (
              <p className="gap-ok" style={{ marginBottom: '0.75rem' }}>
                ✓ Acceso a Search Console concedido
              </p>
            )}
            <button type="submit" className="btn" disabled={loading}>
              {loading ? 'Revisando el sitio…' : 'Revisar y mejorar el sitio'}
            </button>
          </form>
          {google && (
            <div style={{ marginTop: '1rem' }}>
              <span className={`badge ${google.step_complete ? 'badge-success' : 'badge-warn'}`}>
                {google.step_complete ? 'Completo' : 'Pendiente'}
              </span>
              <ul className="list-unstyled" style={{ marginTop: '0.75rem' }}>
                {gaps.map((g, i) => (
                  <li key={i}>
                    {g.passed ? '✓' : '○'} {g.label}
                    {' '}
                    <span className={`badge ${g.passed ? (g.auto ? 'badge-muted' : 'badge-success') : 'badge-warn'}`}>
                      {g.stateLabel}
                    </span>
                    {g.displayMessage ? ` — ${g.displayMessage}` : ''}
                  </li>
                ))}
              </ul>
              {google.remediation?.title && (
                <div style={{ marginTop: '0.75rem' }}>
                  <p><strong>Título propuesto:</strong> {google.remediation.title}</p>
                  <p><strong>Descripción:</strong> {google.remediation.meta_description}</p>
                  <p><strong>Encabezado:</strong> {google.remediation.h1}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <h3>Paso 2 — Pack AEO</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            Ollama genera el pack en forma de árbol. Tema, Negocio y Hechos son los datos de entrada — no hace falta hablar de infraestructura.
          </p>
          <div className="form-row">
            <label>Tema *</label>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Ej. zapatos de running para ciudad"
            />
          </div>
          <div className="form-row">
            <label>Negocio</label>
            <input
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              placeholder="Nombre de la tienda"
            />
          </div>
          <div className="form-row">
            <label>Hechos</label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={3}
              placeholder="Qué vendes, para quién, y qué te diferencia"
            />
          </div>
          <button type="button" className="btn" disabled={loading || !(topic.trim() || businessName.trim())} onClick={runPack}>
            {loading ? 'Generando el árbol…' : 'Generar pack AEO'}
          </button>
          {pack?.aeo && (
            <>
              <p style={{ marginTop: '1rem' }}><strong>{pack.aeo.suggested_title}</strong></p>
              <p style={{ color: 'var(--text-muted)' }}>{pack.aeo.summary}</p>
              <TreeList nodes={(pack.tree || []).filter((n) => n.label === 'AEO')} rootLabel="AEO" />
            </>
          )}
        </div>
      )}

      {step === 3 && (
        <div className="card">
          <h3>Paso 3 — Pack SEO</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            Mismo pack: Ollama arma el árbol SEO (título, descripción, palabras clave y puntuación) a partir de los datos del paso anterior.
          </p>
          {!pack?.seo && (
            <button type="button" className="btn" disabled={loading || !(topic.trim() || businessName.trim())} onClick={runPack}>
              {loading ? 'Generando el árbol…' : 'Generar pack SEO'}
            </button>
          )}
          {pack?.seo && (
            <>
              <p><strong>Título:</strong> {pack.seo.title}</p>
              <p><strong>Descripción:</strong> {pack.seo.meta_description}</p>
              {pack.seo.score && (
                <p>
                  <span className="badge badge-success">
                    {pack.seo.score.overall_score}/{pack.seo.score.max_score} · {pack.seo.score.grade}
                  </span>
                </p>
              )}
              <TreeList nodes={pack.tree} rootLabel={pack.topic} />
              <pre className="resume-pre">{pack.resume}</pre>
            </>
          )}
        </div>
      )}

      {error && <p className="error-msg">{error}</p>}

      <div className="wizard-nav">
        <button type="button" className="btn btn-secondary" disabled={step === 1 || loading} onClick={goBack}>
          Atrás
        </button>
        {step < 3 ? (
          <button type="button" className="btn" disabled={!canContinue || loading} onClick={goNext}>
            Continuar
          </button>
        ) : (
          <span className="badge badge-muted">Último paso</span>
        )}
      </div>
    </>
  )
}
