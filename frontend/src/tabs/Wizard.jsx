import { useEffect, useMemo, useState } from 'react'
import { api, setLicense } from '../api'
import TreeList from '../components/TreeList'
import '../App.css'

const STEPS = [
  { id: 1, key: 'connect', label: 'Conexión' },
  { id: 2, key: 'google', label: 'Google' },
  { id: 3, key: 'aeo', label: 'AEO' },
  { id: 4, key: 'seo', label: 'SEO' },
]

const PLATFORMS = [
  {
    id: 'odoo',
    label: 'Odoo',
    hint: 'URL del pedido + base, usuario y clave API',
  },
  {
    id: 'prestashop',
    label: 'PrestaShop',
    hint: 'URL del pedido + clave del webservice',
  },
  {
    id: 'woocommerce',
    label: 'WooCommerce',
    hint: 'URL del pedido + clave y secreto REST',
  },
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

function businessFromHost(url) {
  const host = hostLabel(url).replace(/^www\./i, '')
  const stem = (host.split('.')[0] || host).replace(/[-_]+/g, ' ')
  if (!stem) return ''
  return stem.charAt(0).toUpperCase() + stem.slice(1)
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

function PlatformMark({ id }) {
  if (id === 'prestashop') {
    return (
      <svg className="platform-mark" viewBox="0 0 48 48" aria-hidden="true">
        <rect width="48" height="48" rx="12" fill="#DF0067" />
        <path fill="#fff" d="M14 32V16h9.2c4.4 0 7.2 2.4 7.2 6.2 0 3.9-2.9 6.3-7.4 6.3H20.4V32H14Zm6.4-13.2v6.2h2.6c2.1 0 3.3-1.1 3.3-3.1 0-2-1.2-3.1-3.3-3.1H20.4Z" />
      </svg>
    )
  }
  if (id === 'woocommerce') {
    return (
      <svg className="platform-mark" viewBox="0 0 48 48" aria-hidden="true">
        <rect width="48" height="48" rx="12" fill="#7F54B3" />
        <path fill="#fff" d="M14.5 18.2 18 31.5h4.1l2.3-8.4 2.3 8.4h4.1L34.5 18.2h-4.1l-2.2 9.2-2.5-9.2h-4.3l-2.5 9.2-2.2-9.2h-4.2Z" />
      </svg>
    )
  }
  return (
    <svg className="platform-mark" viewBox="0 0 48 48" aria-hidden="true">
      <rect width="48" height="48" rx="12" fill="#714B67" />
      <circle cx="24" cy="24" r="9.5" fill="none" stroke="#fff" strokeWidth="3.4" />
      <circle cx="24" cy="24" r="3.2" fill="#fff" />
    </svg>
  )
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
  const [inject, setInject] = useState(null)
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(Boolean(query.license))
  const [error, setError] = useState(null)
  const [entitlement, setEntitlement] = useState(null)
  const [platform, setPlatform] = useState('odoo')
  const [database, setDatabase] = useState('')
  const [username, setUsername] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [wsKey, setWsKey] = useState('')
  const [consumerKey, setConsumerKey] = useState('')
  const [consumerSecret, setConsumerSecret] = useState('')
  const [connection, setConnection] = useState(null)
  const gscHint = query.gscHint
  const githubLogin = query.githubLogin

  async function consumeKey(key) {
    setChecking(true)
    setError(null)
    try {
      setLicense(key)
      const data = await api.entitlement.consume(key, githubLogin || undefined, query.site || undefined)
      setEntitlement(data)
      if (data?.allowed && data?.aeo_site_url) {
        const url = keepHttps(data.aeo_site_url)
        setSiteUrl(url)
        setBusinessName((prev) => prev || businessFromHost(url))
        setTopic((prev) => prev || businessFromHost(url))
      }
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
    const url = keepHttps(entitlement.aeo_site_url || '')
    if (!url) return
    setSiteUrl(url)
    setLicense(query.license)
    setStarted(true)
    setStep(1)
    api.connection.status().then((row) => {
      if (row?.connection?.connected) {
        setConnection(row)
        if (row.connection.platform) setPlatform(row.connection.platform)
        if (row.connection.database) setDatabase(row.connection.database)
        if (row.connection.username) setUsername(row.connection.username)
      }
    }).catch(() => {})
  }, [entitlement, query.license])

  const apiConnected = Boolean(
    status?.google?.modes?.oauth?.connected || google?.auth?.modes?.oauth?.connected
  )
  const googleConnected = gscHint || apiConnected
  const connectDone = Boolean(connection?.connected || connection?.connection?.connected)
  const googleDone = Boolean(google?.step_complete)
  const aeoDone = Boolean(pack?.aeo)
  const seoDone = Boolean(pack?.seo)
  const complete = { 1: connectDone, 2: googleDone, 3: aeoDone, 4: seoDone }
  const canContinue = step < 4 && complete[step]

  const gaps = useMemo(
    () => displayGaps(google?.gaps, googleConnected),
    [google, googleConnected]
  )

  async function saveConnection(e) {
    e?.preventDefault()
    if (!entitlement?.allowed) return
    setError(null)
    setLoading(true)
    try {
      const data = await api.connection.register({
        license: licenseKey,
        platform,
        url: siteUrl,
        database: database || undefined,
        username: username || undefined,
        api_key: apiKey || undefined,
        ws_key: wsKey || undefined,
        consumer_key: consumerKey || undefined,
        consumer_secret: consumerSecret || undefined,
      })
      setConnection(data)
      setApiKey('')
      setWsKey('')
      setConsumerSecret('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

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
        license: licenseKey,
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
        topic: topic.trim() || businessName.trim() || hostLabel(siteUrl),
        url: siteUrl,
        business_name: businessName.trim() || undefined,
        context: context.trim() || undefined,
        locale: 'es',
        license: licenseKey,
      })
      setPack(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function runInject() {
    if (!pack?.seo || !entitlement?.allowed) return
    setError(null)
    setLoading(true)
    try {
      const data = await api.wizard.injectVerify({
        site_url: siteUrl,
        license: licenseKey,
        seo: {
          title: pack.seo.title,
          meta_description: pack.seo.meta_description,
          keywords: pack.seo.keywords,
          canonical: siteUrl,
        },
      })
      setInject(data)
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
  const confirmedSite = keepHttps(entitlement?.aeo_site_url || (allowed ? siteUrl : ''))
  const acquireUrl = PRODUCT_PAGE_URL
  const acquireLabel = BLOCKED_COPY.cta_label
  const selected = PLATFORMS.find((p) => p.id === platform) || PLATFORMS[0]

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
                setLicense(licenseKey)
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
          Primero conecta la tienda del pedido. Luego Google Search, el pack AEO y el pack SEO.
        </p>
        <div className="btn-row" style={{ marginBottom: '0.85rem' }}>
          <span className="badge badge-success">Pedido {entitlement.sale_order_name}</span>
          <span className="badge badge-muted">{hostLabel(siteUrl)}</span>
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
          <h3>Paso 1 — Conexión con la tienda</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            Elige la plataforma e introduce tú los datos de conexión. Search Engine Optimizator los
            guarda en la línea del pedido Arkiphere para interactuar de punta a punta.
          </p>
          <div className="form-row">
            <span className="gate-site-label">Sitio del pedido</span>
            <p className="gate-site-value">{hostLabel(siteUrl)}</p>
          </div>
          <div className="platform-grid">
            {PLATFORMS.map((p) => (
              <button
                key={p.id}
                type="button"
                className={`platform-card ${platform === p.id ? 'active' : ''}`}
                onClick={() => setPlatform(p.id)}
              >
                <PlatformMark id={p.id} />
                <strong>{p.label}</strong>
                <span>{p.hint}</span>
              </button>
            ))}
          </div>
          <form onSubmit={saveConnection}>
            {platform === 'odoo' && (
              <>
                <div className="form-row">
                  <label htmlFor="aeo-db">Base de datos</label>
                  <input id="aeo-db" value={database} onChange={(e) => setDatabase(e.target.value)} placeholder="osh" autoComplete="off" />
                </div>
                <div className="form-row">
                  <label htmlFor="aeo-user">Usuario</label>
                  <input id="aeo-user" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Usuario XML-RPC" autoComplete="off" />
                </div>
                <div className="form-row">
                  <label htmlFor="aeo-key">Clave API</label>
                  <input id="aeo-key" type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} autoComplete="off" />
                </div>
              </>
            )}
            {platform === 'prestashop' && (
              <div className="form-row">
                <label htmlFor="aeo-ws">Clave del webservice</label>
                <input id="aeo-ws" type="password" value={wsKey} onChange={(e) => setWsKey(e.target.value)} autoComplete="off" />
              </div>
            )}
            {platform === 'woocommerce' && (
              <>
                <div className="form-row">
                  <label htmlFor="aeo-ck">Clave de consumidor</label>
                  <input id="aeo-ck" value={consumerKey} onChange={(e) => setConsumerKey(e.target.value)} autoComplete="off" />
                </div>
                <div className="form-row">
                  <label htmlFor="aeo-cs">Secreto de consumidor</label>
                  <input id="aeo-cs" type="password" value={consumerSecret} onChange={(e) => setConsumerSecret(e.target.value)} autoComplete="off" />
                </div>
              </>
            )}
            <button type="submit" className="btn" disabled={loading}>
              {loading ? 'Guardando conexión…' : `Conectar ${selected.label}`}
            </button>
          </form>
          {connectDone && (
            <p className="gap-ok" style={{ marginTop: '0.85rem' }}>
              ✓ {connection?.message || 'Conexión lista. Puedes continuar.'}
            </p>
          )}
          {connection?.arkiphere && (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.4rem' }}>
              {connection.arkiphere.ok
                ? `Pedido ${connection.sale_order_name || entitlement.sale_order_name}: datos visibles en la línea de pedido.`
                : connection.arkiphere.message || 'Espejo local guardado.'}
            </p>
          )}
          {(connection?.connection?.recommendations || []).length > 0 && (
            <ul className="list-unstyled" style={{ marginTop: '0.75rem' }}>
              {connection.connection.recommendations.map((item) => (
                <li key={item.id}>○ {item.label} — {item.why}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <h3>Paso 2 — Google Search</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            Revisamos cómo ve Google tu sitio real y corregimos lo que se pueda de forma automática.
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

      {step === 3 && (
        <div className="card">
          <h3>Paso 3 — Pack AEO</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            Ollama arma el pack General a partir del hostname, el schema y los hechos del negocio.
          </p>
          <div className="form-row">
            <label>Tema *</label>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Qué debe entender Google y los motores de respuesta"
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

      {step === 4 && (
        <div className="card">
          <h3>Paso 4 — Pack SEO</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            Mismo pack: título, descripción y puntuación. Luego se publica en la tienda conectada.
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
              <div className="btn-row" style={{ marginTop: '0.85rem' }}>
                <button type="button" className="btn" disabled={loading} onClick={runInject}>
                  {loading ? 'Publicando…' : 'Publicar en la tienda'}
                </button>
              </div>
              {inject && (
                <p className={inject.ok ? 'ok-msg' : 'error-msg'}>
                  {inject.customer_message || inject.message}
                </p>
              )}
            </>
          )}
        </div>
      )}

      {error && <p className="error-msg">{error}</p>}

      <div className="wizard-nav">
        <button type="button" className="btn btn-secondary" disabled={step === 1 || loading} onClick={goBack}>
          Atrás
        </button>
        {step < 4 ? (
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
