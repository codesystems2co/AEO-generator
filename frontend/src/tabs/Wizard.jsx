import { useEffect, useMemo, useRef, useState } from 'react'
import { api, setLicense } from '../api'
import Accordion, { AccordionPanel } from '../components/Accordion'
import JobProgress from '../components/JobProgress'
import TreeList from '../components/TreeList'
import {
  assistantLine,
  buildClientTree,
  buildJobPayload,
  buildProgress,
} from '../wizard/jobDossier'
import { copyFor, localeOf } from '../i18n/copy'
import '../App.css'

function stepsFor(t) {
  return [
    { id: 1, key: 'connect', label: t.step.connect },
    { id: 2, key: 'google', label: t.step.google },
    { id: 3, key: 'aeo', label: t.step.aeo },
    { id: 4, key: 'seo', label: t.step.seo },
  ]
}

function stepTitles(t) {
  return { 1: t.step.title1, 2: t.step.title2, 3: t.step.title3, 4: t.step.title4 }
}

function platformsFor(t) {
  return [
    { id: 'odoo', label: 'Odoo', hint: t.connect.odooHint },
    { id: 'prestashop', label: 'PrestaShop', hint: t.connect.prestaHint },
    { id: 'woocommerce', label: 'WooCommerce', hint: t.connect.wooHint },
  ]
}

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

function friendlyGapMessage(name, message, connected, t) {
  if (name === 'Client consent') {
    return connected ? t.gaps.consentOn : t.gaps.consentOff
  }
  if (name === 'OAuth client configured') {
    return t.gaps.done
  }
  if (!message) return ''
  const map = [
    [/User must grant/i, t.gaps.consentOff],
    [/Access token present/i, t.gaps.consentOn],
    [/GOOGLE_CLIENT_ID|SECRET/i, t.gaps.done],
    [/Missing meta description/i, t.gaps.missingMeta],
    [/0 H1 tag/i, t.gaps.missingH1],
    [/No JSON-LD/i, t.gaps.missingSchema],
    [/JSON-LD or schema.org found/i, t.gaps.schemaOk],
    [/HTTP 200/i, t.gaps.liveOk],
    [/Price\/cart\/product language found/i, t.gaps.commerceOk],
  ]
  for (const [re, label] of map) {
    if (re.test(message)) return label
  }
  if (/GOOGLE_|connection|publish|shop api/i.test(message)) return t.gaps.review
  return message
}

function connectionStatusLines(connection, platformLabel, t) {
  const row = connection?.connection || {}
  const probe = connection?.probe || row.probe || {}
  const connected = Boolean(connection?.connected || row.connected)
  const hasProbe = Object.prototype.hasOwnProperty.call(probe, 'ok')
  const ark = connection?.arkiphere || row.arkiphere || {}
  const hasArk = Boolean(
    connection?.arkiphere_message
    || Object.prototype.hasOwnProperty.call(ark, 'ok')
    || ark.message
  )
  if (!connected && !hasProbe && !hasArk) return null
  const shopOk = hasProbe ? Boolean(probe.ok) : connected
  const arkOk = hasArk ? Boolean(ark.ok) : connected
  return {
    shopOk,
    shopMsg: shopOk
      ? t.connect.shopOk.replace('{platform}', platformLabel)
      : t.connect.shopFail.replace('{platform}', platformLabel),
    arkOk,
    arkMsg: arkOk ? t.connect.arkOk : (ark.message || t.connect.arkPending),
  }
}

function displayGaps(gaps, connected, t) {
  const hidden = new Set([
    'OAuth client configured',
    'Service account key',
    'GSC property share',
    'Auth mode selected',
  ])
  return (gaps || [])
    .filter((g) => !hidden.has(g.name))
    .map((g) => {
    const consent = g.name === 'Client consent'
    const passed = consent && connected ? true : Boolean(g.virtual_passed || g.passed)
    const auto = Boolean(g.virtual_passed && !g.passed && !(consent && connected))
    return {
      ...g,
      label: (t?.gaps && {
        'Live URL fetch': t.gaps.live,
        'Title tag': t.gaps.title,
        'Meta description': t.gaps.meta,
        'H1 present': t.gaps.h1,
        'robots.txt': t.gaps.robots,
        'sitemap.xml': t.gaps.sitemap,
        'Client consent': t.gaps.consent,
        'GSC property visible': t.gaps.property,
        'Commerce signals': t.gaps.commerce,
        'Structured data': t.gaps.schema,
      }[g.name]) || GAP_LABELS[g.name] || g.name,
      passed,
      auto,
      stateLabel: passed ? (auto ? (t?.gaps?.auto || 'Auto') : (t?.gaps?.done || 'Listo')) : (t?.gaps?.wait || 'Pendiente'),
      displayMessage: friendlyGapMessage(g.name, g.message, connected, t),
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

function GoogleMark() {
  return (
    <svg className="google-mark" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 8 3l5.7-5.7C34.2 6.1 29.4 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.7-.4-3.9Z" />
      <path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.1 8 3l5.7-5.7C34.2 6.1 29.4 4 24 4 16.3 4 9.7 8.3 6.3 14.7Z" />
      <path fill="#4CAF50" d="M24 44c5.2 0 10-2 13.6-5.2l-6.3-5.3C29.2 35.1 26.8 36 24 36c-5.3 0-9.7-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44Z" />
      <path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-1.1 3.2-3.5 5.7-6.7 7.1l.1.1 6.3 5.3C36.9 41.6 44 36 44 24c0-1.3-.1-2.7-.4-3.9Z" />
    </svg>
  )
}

function WorkingForYou({ message }) {
  return (
    <div className="working-for-you" role="status" aria-live="polite">
      <span className="working-spinner" aria-hidden="true" />
      <p>{message}</p>
    </div>
  )
}

function GoogleAccountCard({ connected, loading, onConnect, t }) {
  return (
    <div className="gsc-auth">
      {connected ? (
        <p className="gap-ok">✓ {t.connect.googleOn}</p>
      ) : (
        <>
          <p className="gsc-auth-kicker">{t.connect.googleKicker}</p>
          <p>{t.connect.googleIntro}</p>
          <button type="button" className="btn btn-google" disabled={loading} onClick={onConnect}>
            <GoogleMark />
            {t.connect.googleBtn}
          </button>
        </>
      )}
    </div>
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
  const [pdfBusy, setPdfBusy] = useState(false)
  const [jobTree, setJobTree] = useState([])
  const [openPlan, setOpenPlan] = useState(true)
  const [openStep, setOpenStep] = useState(true)
  const [revokeBusy, setRevokeBusy] = useState(false)
  const googleAutoRef = useRef(false)
  const packAutoRef = useRef(false)
  const gscHint = query.gscHint
  const githubLogin = query.githubLogin
  const lang = localeOf(entitlement?.lang)
  const t = copyFor(lang)
  const STEPS = stepsFor(t)
  const STEP_TITLES = stepTitles(t)
  const PLATFORMS = platformsFor(t)

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
        ...BLOCKED_COPY,
        message: t.wizard.checkFail,
        cta_label: t.wizard.acquire,
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
  const canContinue = step === 1 ? Boolean(entitlement?.allowed) : (step < 4 && complete[step])
  const jobPayload = useMemo(
    () => buildJobPayload({
      entitlement,
      siteUrl,
      platform,
      connection,
      google,
      pack,
      inject,
      googleConnected,
      connectDone,
    }),
    [entitlement, siteUrl, platform, connection, google, pack, inject, googleConnected, connectDone]
  )
  const progress = useMemo(
    () => buildProgress({ connectDone, googleDone, aeoDone, seoDone, inject, loading, step, lang }),
    [connectDone, googleDone, aeoDone, seoDone, inject, loading, step, lang]
  )
  const localTree = useMemo(
    () => buildClientTree({ payload: jobPayload, googleConnected, lang }),
    [jobPayload, googleConnected, lang]
  )
  const canDownloadPdf = Boolean(googleDone && aeoDone && seoDone && inject)
  const progressMessage = assistantLine({
    loading,
    step,
    percent: progress.percent,
    inject,
    connectDone,
    lang,
  })

  const gaps = useMemo(
    () => displayGaps(google?.gaps, googleConnected, t),
    [google, googleConnected, t]
  )

  useEffect(() => {
    if (!entitlement?.allowed) return
    let cancelled = false
    api.wizard.job(jobPayload).then((data) => {
      if (!cancelled && data?.tree?.length) setJobTree(data.tree)
    }).catch(() => {
      if (!cancelled) setJobTree(localTree)
    })
    return () => { cancelled = true }
  }, [entitlement, connectDone, jobPayload, localTree])

  useEffect(() => {
    if (step !== 2 || googleAutoRef.current || !entitlement?.allowed) return
    googleAutoRef.current = true
    runAutofix()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, entitlement])

  useEffect(() => {
    if (step !== 3 || packAutoRef.current || !entitlement?.allowed) return
    if (!(topic.trim() || businessName.trim())) return
    packAutoRef.current = true
    runPack()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, entitlement])

  useEffect(() => {
    setOpenStep(true)
  }, [step])

  async function downloadPdf() {
    if (!canDownloadPdf) return
    setError(null)
    setPdfBusy(true)
    try {
      const { blob, filename } = await api.wizard.reportPdf(jobPayload)
      const href = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = href
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(href)
    } catch (err) {
      setError(err.message)
    } finally {
      setPdfBusy(false)
    }
  }

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

  async function revokeConnection() {
    if (!entitlement?.allowed || !connectDone) return
    setError(null)
    setRevokeBusy(true)
    try {
      await api.connection.revoke({
        license: licenseKey,
        sale_order_name: entitlement.sale_order_name,
      })
      setConnection(null)
      setJobTree([])
    } catch (err) {
      setError(err.message)
    } finally {
      setRevokeBusy(false)
    }
  }

  async function runAutofix(e) {
    e?.preventDefault?.()
    if (!entitlement?.allowed) return
    setError(null)
    setLoading(true)
    try {
      const data = await api.wizard.autofix({
        site_url: siteUrl,
        mode: 'oauth',
        topic: businessName || topic || undefined,
        context: context || undefined,
        locale: lang,
        license: licenseKey,
      })
      setGoogle(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function startSearchConsole() {
    setError(null)
    setLoading(true)
    try {
      const data = await api.google.oauthStart({
        license: licenseKey,
        site: siteUrl,
      })
      if (data?.auth_url) {
        window.location.href = data.auth_url
        return
      }
      setError(t.wizard.googleAuthFail)
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
        locale: lang,
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
        locale: lang,
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
  const acquireLabel = t.wizard.acquire
  const selected = PLATFORMS.find((p) => p.id === platform) || PLATFORMS[0]
  const orderBadge = allowed
    ? t.wizard.withOrder.replace('{name}', entitlement.sale_order_name || '')
    : t.wizard.noOrder

  if (checking && !entitlement) {
    return (
      <div className="card">
        <h3>{t.wizard.checking}</h3>
        <p style={{ color: 'var(--text-muted)' }}>{t.wizard.checkingHint}</p>
      </div>
    )
  }

  if (showGate) {
    return (
      <div className="card">
        <h3>{t.wizard.orderNeeded}</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          {t.wizard.orderGate}
        </p>
        <p>
          <span className={`badge ${allowed ? 'badge-success' : 'badge-warn'}`}>
            {orderBadge}
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
          <label htmlFor="aeo-license">{t.wizard.license}</label>
          <div className="gate-key">
            <input
              id="aeo-license"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value)}
              placeholder="AEO-…"
              autoComplete="off"
            />
            <button type="submit" className="btn btn-secondary" disabled={checking || !licenseKey.trim()}>
              {checking ? t.wizard.checkingBtn : t.wizard.check}
            </button>
          </div>
        </form>
        {allowed && confirmedSite ? (
          <div className="form-row">
            <span className="gate-site-label">{t.wizard.site}</span>
            <p className="gate-site-value">{hostLabel(confirmedSite)}</p>
          </div>
        ) : null}
        {allowed && entitlement?.message ? (
          <p style={{ marginTop: '0.25rem' }}>{entitlement.message}</p>
        ) : (
          <p style={{ marginTop: '0.25rem' }}>{t.wizard.gateHint}</p>
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
              {t.wizard.start}
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
        <h3>{t.wizard.heading}</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          {t.wizard.intro}
        </p>
        <div className="btn-row" style={{ marginBottom: '0.85rem' }}>
          <span className="badge badge-success">{t.wizard.withOrder.replace('{name}', entitlement.sale_order_name || '')}</span>
          <span className="badge badge-muted">{hostLabel(siteUrl)}</span>
        </div>
        <JobProgress
          progress={progress}
          message={progressMessage}
          onDownload={downloadPdf}
          downloading={pdfBusy}
          canDownload={canDownloadPdf}
          kicker={t.progress.kicker}
          hint={t.progress.hint}
          downloadLabel={t.progress.download}
          downloadingLabel={t.progress.downloading}
        />
        <ol className="stepper" style={{ marginTop: '1rem' }}>
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

      <Accordion>
        <AccordionPanel
          id="plan-de-trabajo"
          kicker={t.step.planKicker}
          title={t.step.plan}
          summary={`${entitlement.sale_order_name || hostLabel(siteUrl)} · ${progress.percent}%`}
          open={openPlan}
          onToggle={() => setOpenPlan((value) => !value)}
        >
          <TreeList
            nodes={jobTree.length ? jobTree : localTree}
            rootLabel={entitlement.sale_order_name || hostLabel(siteUrl)}
          />
        </AccordionPanel>

        <AccordionPanel
          id="paso-actual"
          kicker={t.step.kicker}
          title={t.step.panel.replace('{n}', String(step)).replace('{title}', STEP_TITLES[step])}
          summary={complete[step] ? t.step.complete : loading ? t.step.running : t.step.pending}
          open={openStep}
          onToggle={() => setOpenStep((value) => !value)}
        >
      {step === 1 && (
        <>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            {t.connect.intro}
          </p>
          <div className="form-row">
            <span className="gate-site-label">{t.wizard.orderSite}</span>
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
                <div className="platform-card-copy">
                  <strong>{p.label}</strong>
                  <span>{p.hint}</span>
                </div>
              </button>
            ))}
          </div>
          <form onSubmit={saveConnection}>
            {platform === 'odoo' && (
              <>
                <div className="form-row">
                  <label htmlFor="aeo-db">{t.connect.db}</label>
                  <input id="aeo-db" value={database} onChange={(e) => setDatabase(e.target.value)} placeholder="osh" autoComplete="off" />
                </div>
                <div className="form-row">
                  <label htmlFor="aeo-user">{t.connect.user}</label>
                  <input id="aeo-user" value={username} onChange={(e) => setUsername(e.target.value)} placeholder={t.connect.user} autoComplete="off" />
                </div>
                <div className="form-row">
                  <label htmlFor="aeo-key">{t.connect.password}</label>
                  <input id="aeo-key" type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} autoComplete="off" />
                </div>
              </>
            )}
            {platform === 'prestashop' && (
              <div className="form-row">
                <label htmlFor="aeo-ws">{t.connect.ws}</label>
                <input id="aeo-ws" type="password" value={wsKey} onChange={(e) => setWsKey(e.target.value)} autoComplete="off" />
              </div>
            )}
            {platform === 'woocommerce' && (
              <>
                <div className="form-row">
                  <label htmlFor="aeo-ck">{t.connect.ck}</label>
                  <input id="aeo-ck" value={consumerKey} onChange={(e) => setConsumerKey(e.target.value)} autoComplete="off" />
                </div>
                <div className="form-row">
                  <label htmlFor="aeo-cs">{t.connect.cs}</label>
                  <input id="aeo-cs" type="password" value={consumerSecret} onChange={(e) => setConsumerSecret(e.target.value)} autoComplete="off" />
                </div>
              </>
            )}
            <button type="submit" className="btn" disabled={loading}>
              {loading ? t.connect.checking : t.connect.submit.replace('{platform}', selected.label)}
            </button>
          </form>
          {(() => {
            const lines = connectionStatusLines(connection, selected.label, t)
            if (!lines) return null
            return (
              <div className="connect-status">
                <p className={lines.shopOk ? 'gap-ok' : 'error-msg'}>
                  {lines.shopOk ? '✓' : '○'} {lines.shopMsg}
                </p>
                <p className={lines.arkOk ? 'gap-ok' : 'error-msg'}>
                  {lines.arkOk ? '✓' : '○'} {lines.arkMsg}
                </p>
                {connectDone ? (
                  <button
                    type="button"
                    className="btn btn-secondary btn-revoke"
                    disabled={loading || revokeBusy}
                    onClick={revokeConnection}
                  >
                    {revokeBusy ? t.connect.revoking : t.connect.revoke}
                  </button>
                ) : null}
              </div>
            )
          })()}
          {!connectDone ? (
            <p className="connect-skip-hint">{t.connect.skipHint}</p>
          ) : null}
          <GoogleAccountCard
            connected={googleConnected}
            loading={loading}
            onConnect={startSearchConsole}
            t={t}
          />
        </>
      )}

      {step === 2 && (
        <>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            {t.google.intro}
          </p>
          <div className="form-row">
            <span className="gate-site-label">{t.wizard.site}</span>
            <p className="gate-site-value">{hostLabel(siteUrl)}</p>
          </div>
          {loading ? (
            <WorkingForYou message={t.google.analyzing} />
          ) : null}
          <GoogleAccountCard
            connected={googleConnected}
            loading={loading}
            onConnect={startSearchConsole}
            t={t}
          />
          {google && (
            <div style={{ marginTop: '1rem' }}>
              <span className={`badge ${google.step_complete ? 'badge-success' : 'badge-warn'}`}>
                {google.step_complete ? t.step.complete : t.step.pending}
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
                  <p><strong>{t.tree.proposedTitle}:</strong> {google.remediation.title}</p>
                  <p><strong>{t.tree.proposedDesc}:</strong> {google.remediation.meta_description}</p>
                  <p><strong>{t.tree.proposedH1}:</strong> {google.remediation.h1}</p>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {step === 3 && (
        <>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            {t.aeo.intro}
          </p>
          <div className="form-row">
            <label>{t.aeo.topic}</label>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder={t.aeo.topicPh}
            />
          </div>
          <div className="form-row">
            <label>{t.aeo.business}</label>
            <input
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              placeholder={t.aeo.businessPh}
            />
          </div>
          <div className="form-row">
            <label>{t.aeo.facts}</label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={3}
              placeholder={t.aeo.factsPh}
            />
          </div>
          <button type="button" className="btn" disabled={loading || !(topic.trim() || businessName.trim())} onClick={runPack}>
            {loading ? t.aeo.generating : t.aeo.generate}
          </button>
          {pack?.aeo && (
            <>
              <p style={{ marginTop: '1rem' }}><strong>{pack.aeo.suggested_title}</strong></p>
              <p style={{ color: 'var(--text-muted)' }}>{pack.aeo.summary}</p>
              <TreeList nodes={(pack.tree || []).filter((n) => n.label === 'AEO')} rootLabel="AEO" />
            </>
          )}
        </>
      )}

      {step === 4 && (
        <>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
            {t.seo.intro}
          </p>
          {!pack?.seo && (
            <button type="button" className="btn" disabled={loading || !(topic.trim() || businessName.trim())} onClick={runPack}>
              {loading ? t.seo.generating : t.seo.generate}
            </button>
          )}
          {pack?.seo && (
            <>
              <p><strong>{t.seo.title}:</strong> {pack.seo.title}</p>
              <p><strong>{t.seo.description}:</strong> {pack.seo.meta_description}</p>
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
                  {loading ? t.seo.publishing : (connectDone ? t.seo.publish : t.seo.skipPublish)}
                </button>
              </div>
              {inject && (
                <p className={inject.ok ? 'ok-msg' : 'error-msg'}>
                  {inject.customer_message || inject.message}
                </p>
              )}
              <div className="btn-row" style={{ marginTop: '0.85rem' }}>
                <button type="button" className="btn btn-secondary" disabled={pdfBusy || !canDownloadPdf} onClick={downloadPdf}>
                  {pdfBusy ? t.progress.downloading : t.progress.download}
                </button>
              </div>
            </>
          )}
        </>
      )}
        </AccordionPanel>
      </Accordion>

      {error && <p className="error-msg">{error}</p>}

      <div className="wizard-nav">
        <button type="button" className="btn btn-secondary" disabled={step === 1 || loading} onClick={goBack}>
          {t.step.back}
        </button>
        {step < 4 ? (
          <button type="button" className="btn" disabled={!canContinue || loading} onClick={goNext}>
            {t.step.continue}
          </button>
        ) : (
          <span className="badge badge-muted">{t.step.last}</span>
        )}
      </div>
    </>
  )
}
