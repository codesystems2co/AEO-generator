import { useEffect, useMemo, useRef, useState } from 'react'
import Accordion, { AccordionPanel } from '../components/Accordion'
import JobProgress from '../components/JobProgress'
import TreeList from '../components/TreeList'
import { api, setLicense } from '../api'
import { copyFor, localeOf } from '../i18n/copy'
import { persistOrder, readOrderQuery } from '../wizard/orderContext'

const CATALOG_PRODUCT_PAGE_URL =
  'https://arkiphere.cloud/shop/product-catalog-aeo-and-seo-pack-with-ia-110'

function queryOf() {
  const row = readOrderQuery()
  return {
    license: row.license,
    site: row.site,
    gscHint: row.gscHint,
  }
}

function generalHref(license, site) {
  const params = new URLSearchParams()
  if (license) params.set('license', license)
  if (site) params.set('site', site)
  const text = params.toString()
  return text ? `/?${text}` : '/'
}


function withAcquireParams(baseUrl, host, quantity) {
  try {
    const url = new URL(baseUrl || CATALOG_PRODUCT_PAGE_URL)
    let bare = ''
    const raw = (host || '').trim()
    if (raw) {
      try {
        bare = new URL(raw.includes('://') ? raw : `https://${raw}`).hostname || ''
      } catch {
        bare = raw.replace(/^https?:\/\//i, '').split('/')[0]
      }
      bare = bare.toLowerCase().replace(/^www\./, '')
    }
    if (bare) {
      url.searchParams.set('aeo_site_url', `https://${bare}`)
      url.searchParams.set('hostname', bare)
    }
    const qty = Number(quantity)
    if (Number.isFinite(qty) && qty > 0) {
      url.searchParams.set('qty', String(Math.trunc(qty)))
    }
    return url.toString()
  } catch {
    return baseUrl || CATALOG_PRODUCT_PAGE_URL
  }
}

function hostLabel(url) {
  try {
    return new URL(url).host.replace(/^www\./i, '') || url
  } catch {
    return url || ''
  }
}

function saveBlob(blob, filename) {
  const href = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = href
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(href)
}

function IconCart() {
  return (
    <svg className="gate-acquire-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M7 18a2 2 0 1 0 0 4 2 2 0 0 0 0-4Zm10 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4ZM3.1 3.3h1.7l.3 1.4h13.8a1 1 0 0 1 1 .8l1.1 6.2a2 2 0 0 1-2 2.3H7.6l.4 2h10.2v2H7.2a2 2 0 0 1-2-2.3L4.1 5.3H2.2l-.1-2ZM7.3 11.7h10.9l.7-4H6.5l.8 4Z"
      />
    </svg>
  )
}

function IconChevronLeft() {
  return (
    <svg className="btn-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M14.7 6.3 8 13l6.7 6.7 1.4-1.4L10.8 13l5.3-5.3-1.4-1.4Z" />
    </svg>
  )
}

function IconChevronRight() {
  return (
    <svg className="btn-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="m9.3 6.3-1.4 1.4L13.2 13l-5.3 5.3 1.4 1.4L16 13 9.3 6.3Z" />
    </svg>
  )
}

function IconSearch() {
  return (
    <svg className="btn-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M10.5 4a6.5 6.5 0 1 1 0 13 6.5 6.5 0 0 1 0-13Zm0 2a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9Zm7.2 10.1 3.1 3.1-1.4 1.4-3.1-3.1 1.4-1.4Z" />
    </svg>
  )
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

function stateLabel(state, t) {
  if (state === 'analyzing') return t.analyzingState
  if (state === 'analyzed') return t.analyzed
  return t.queued
}

export default function CatalogWizard({ lang: langProp }) {
  const query = queryOf()
  const [offer, setOffer] = useState(null)
  const [error, setError] = useState('')
  const [started, setStarted] = useState(false)
  const [step, setStep] = useState(1)
  const [platform, setPlatform] = useState('odoo')
  const [session, setSession] = useState(null)
  const [run, setRun] = useState(null)
  const [published, setPublished] = useState(null)
  const [busy, setBusy] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [pdfBusy, setPdfBusy] = useState(false)
  const [openPlan, setOpenPlan] = useState(false)
  const [openStep, setOpenStep] = useState(true)
  const ticking = useRef(false)
  const lang = localeOf(langProp)
  const t = copyFor(lang)
  const c = t.catalog

  const STEPS = [
    { id: 1, label: c.stepConnect },
    { id: 2, label: c.stepCatalog },
    { id: 3, label: c.stepAeo },
    { id: 4, label: c.stepSeo },
    { id: 5, label: c.stepReport },
  ]
  const STEP_TITLES = { 1: c.title1, 2: c.title2, 3: c.title3, 4: c.title4, 5: c.title5 }
  const PLATFORMS = [
    { id: 'odoo', label: 'Odoo', hint: c.odooService },
    { id: 'prestashop', label: 'PrestaShop', hint: c.prestaService },
    { id: 'woocommerce', label: 'WooCommerce', hint: c.wooService },
  ]

  useEffect(() => {
    let cancelled = false
    if (query.license) setLicense(query.license)
    // Hard cap so the checking screen cannot hang forever if the API is busy.
    api.catalog.offer(query.license, { signal: AbortSignal.timeout(20000) })
      .then((data) => {
        if (cancelled) return
        setOffer(data)
        const platformsNow = data?.platforms || []
        const unlocked = Boolean(data?.owned || data?.general_allowed)
        if (unlocked || platformsNow.includes('odoo')) {
          setStarted(true)
          setStep(1)
          const first = platformsNow[0]
          if (first) setPlatform(first)
        }
      })
      .catch((err) => {
        if (!cancelled) setError(String(err?.message || err))
      })
    return () => {
      cancelled = true
    }
  }, [query.license])

  useEffect(() => {
    // Wait for offer so /job polls cannot starve the pack check on the API thread pool.
    if (!offer) return undefined
    if (query.license) setLicense(query.license)
    let cancelled = false
    let inFlight = false
    const pull = () => {
      if (cancelled || inFlight) return
      inFlight = true
      api.catalog.job(query.license)
        .then((data) => {
          if (cancelled) return
          const running = data?.catalog
          if (data?.run?.total) setRun(data.run)
          if (running && (running.analyzed_count || running.queue?.window?.length)) {
            setSession(running)
            setStarted(true)
            setStep(2)
          }
          if (data?.run?.total) {
            setStarted(true)
            setStep(2)
          }
        })
        .catch(() => {})
        .finally(() => {
          inFlight = false
        })
    }
    pull()
    const timer = window.setInterval(pull, 2500)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [query.license, offer])

  useEffect(() => {
    if (step !== 2 || !session || session.done || run?.running || ticking.current) return undefined
    ticking.current = true
    const timer = window.setTimeout(() => {
      api.catalog.tick()
        .then((data) => setSession(data))
        .catch((err) => setError(String(err?.message || err)))
        .finally(() => {
          ticking.current = false
        })
    }, 350)
    return () => window.clearTimeout(timer)
  }, [step, session])

  async function startScan() {
    setError('')
    setBusy(true)
    setPublished(null)
    try {
      const data = await api.catalog.start()
      if (data?.reason === 'optional') {
        setError(c.noWrite)
        return
      }
      setSession(data)
    } catch (err) {
      setError(String(err?.message || err))
    } finally {
      setBusy(false)
    }
  }

  async function publishSheet() {
    setError('')
    setPublishing(true)
    try {
      const data = await api.catalog.publish()
      setPublished(data)
      if (data && (data.allowance != null || data.remaining != null)) {
        setOffer((prev) => ({ ...(prev || {}), ...data, sale_order_name: prev?.sale_order_name || data.sale_order_name }))
      }
      if (!data?.ok) {
        if (data?.reason === 'no_credits') {
          const processed = data.processed_ids ?? data.used ?? 0
          const needed = data.blocked_count || 1
          setError(
            c.noCredits
              .replace('{processed}', String(processed))
              .replace('{needed}', String(needed)),
          )
          return null
        }
        setError(c.noWrite)
        return null
      }
      setStep(5)
      return data
    } catch (err) {
      setError(String(err?.message || err))
      return null
    } finally {
      setPublishing(false)
    }
  }

  async function downloadReport() {
    if (!canDownload) return
    setError('')
    setPdfBusy(true)
    try {
      const { blob, filename } = await api.catalog.reportPdf()
      saveBlob(blob, filename)
    } catch (err) {
      setError(String(err?.message || err))
    } finally {
      setPdfBusy(false)
    }
  }

  const platforms = offer?.platforms || []
  const connected = platforms.length > 0
  const owned = Boolean(offer?.owned || offer?.general_allowed)
  const host = offer?.host || query.site || ''
  const allowance = Number(offer?.allowance ?? 0)
  const used = Number(offer?.used ?? offer?.processed_ids ?? 0)
  const remaining = Number(offer?.remaining ?? Math.max(0, allowance - used))
  const catalogTotal = Number(session?.total ?? run?.total ?? 0)
  const neededQty = Math.max(0, catalogTotal - used - remaining)
  const acquireUrl = withAcquireParams(
    offer?.acquire_url || CATALOG_PRODUCT_PAGE_URL,
    host,
    neededQty > 0 ? neededQty : Math.max(1, remaining || 1),
  )
  const fichaBadge = c.fichaBadge
    .replace('{remaining}', String(remaining))
    .replace('{used}', String(used))
    .replace('{allowance}', String(allowance))
  const creditsBlocked = remaining <= 0
  const needsMoreFichas = neededQty > 0
  const selected = PLATFORMS.find((row) => row.id === platform) || PLATFORMS[0]
  const windowRows = session?.queue?.window || []
  const catalogTree = session?.tree || []
  const analyzed = session?.products || []
  const connectDone = connected
  const catalogDone = Boolean(session?.done && session?.analyzed_count)
  const aeoDone = catalogDone
  const seoDone = catalogDone
  const publishDone = Boolean(published?.ok)
  const complete = { 1: connectDone, 2: catalogDone, 3: aeoDone, 4: seoDone, 5: publishDone }
  const canContinue = step === 1 ? (owned || platforms.includes('odoo')) : (step < 5 && complete[step])
  const canDownload = step === 5 && publishDone && catalogDone
  const progress = useMemo(() => {
    const items = [
      { id: 'connect', label: c.stepConnect, detail: c.progressConnect, icon: 'plug', done: connectDone },
      { id: 'catalog', label: c.stepCatalog, detail: c.progressCatalog, icon: 'search', done: catalogDone },
      { id: 'aeo', label: c.stepAeo, detail: c.progressAeo, icon: 'chat', done: aeoDone },
      { id: 'seo', label: c.stepSeo, detail: c.progressSeo, icon: 'tag', done: seoDone },
      { id: 'publish', label: t.progress.publish, detail: c.progressPublish, icon: 'upload', done: publishDone },
      { id: 'report', label: t.progress.report, detail: c.progressReport, icon: 'file', done: canDownload },
    ]
    const doneCount = items.filter((item) => item.done).length
    return {
      percent: Math.round((doneCount / items.length) * 100),
      items,
      current: items.find((item) => !item.done) || items[items.length - 1],
      loading: busy || publishing,
    }
  }, [c, t.progress.publish, t.progress.report, connectDone, catalogDone, aeoDone, seoDone, publishDone, canDownload, busy, publishing])

  if (!offer && !error) {
    return (
      <div className="card">
        <h3>{c.checking}</h3>
        <p style={{ color: 'var(--text-muted)' }}>{c.checkingHint}</p>
      </div>
    )
  }

  if (!started) {
    return (
      <div className="card">
        <p className="accordion-kicker">{c.kicker}</p>
        <h3>{c.orderNeeded}</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }}>{c.orderGate}</p>
        <p>
          <span className={`badge ${owned ? 'badge-success' : 'badge-warn'}`}>
            {owned ? t.wizard.withOrder.replace('{name}', offer?.sale_order_name || '') : t.wizard.noOrder}
          </span>
          {host ? <span className="badge badge-muted" style={{ marginLeft: '0.4rem' }}>{hostLabel(host)}</span> : null}
          <span className={`badge ${creditsBlocked ? 'badge-warn' : 'badge-muted'}`} style={{ marginLeft: '0.4rem' }}>
            {fichaBadge}
          </span>
        </p>
        <p>{c.locked}</p>
        <p>{c.gateHint}</p>
        <h3 className="catalog-include-title">{c.includeTitle}</h3>
        <div className="mode-grid catalog-service-grid">
          <article className="mode-card">
            <strong>{c.serviceCatalogTitle}</strong>
            <span>{c.include1}</span>
          </article>
          <article className="mode-card">
            <strong>{c.serviceAeoTitle}</strong>
            <span>{c.include2}</span>
          </article>
          <article className="mode-card">
            <strong>{c.serviceSeoTitle}</strong>
            <span>{c.include3}</span>
          </article>
          <article className="mode-card">
            <strong>{c.serviceNativeTitle}</strong>
            <span>{c.include4}</span>
          </article>
          <article className="mode-card">
            <strong>{c.serviceReportTitle}</strong>
            <span>{c.include5}</span>
          </article>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '1rem 0 0.75rem' }}>{c.connectIntro}</p>
        <div className="platform-grid">
          {PLATFORMS.map((row) => (
            <article key={row.id} className={`platform-card ${platforms.includes(row.id) ? 'is-live' : ''}`}>
              <div className="platform-card-head">
                <PlatformMark id={row.id} />
                <strong>
                  {row.label}
                  {platforms.includes(row.id) ? <span className="platform-live-tag">{t.connect.connectedBadge}</span> : null}
                </strong>
              </div>
              <span className="platform-card-hint">{row.hint}</span>
            </article>
          ))}
        </div>
        {error ? <p className="error-msg">{error}</p> : null}
        {owned ? (
          <div className="btn-row" style={{ marginTop: '1rem' }}>
            <button type="button" className="btn" onClick={() => { setStarted(true); setStep(1) }}>
              {c.start}
            </button>
          </div>
        ) : (
          <a className="btn gate-acquire" href={acquireUrl} target="_blank" rel="noopener noreferrer">
            <IconCart />
            {c.acquire}
          </a>
        )}
        <p style={{ marginTop: '1rem' }}>
          <a href={generalHref(query.license, host)}>{c.back}</a>
        </p>
      </div>
    )
  }

  return (
    <>
      <div className="card">
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>{c.intro}</p>
        <div className="btn-row" style={{ marginBottom: '0.85rem' }}>
          <span className="badge badge-success">{t.wizard.withOrder.replace('{name}', offer?.sale_order_name || '')}</span>
          <span className="badge badge-muted">{hostLabel(host)}</span>
          <span className={`badge ${creditsBlocked ? 'badge-warn' : 'badge-muted'}`}>{fichaBadge}</span>
        </div>
        <p style={{ marginTop: 0 }}>
          <a href={generalHref(query.license, host)}>{c.back}</a>
        </p>
        <JobProgress
          progress={progress}
          message={c.intro}
          onDownload={downloadReport}
          downloading={pdfBusy}
          canDownload={canDownload}
          kicker={t.progress.kicker}
          hint={c.progressHint}
          downloadLabel={c.download}
          downloadingLabel={c.downloading}
          tasksKicker={t.progress.tasksKicker}
          tasksTitle={t.progress.tasksTitle}
        />
        <ol className="stepper" style={{ marginTop: '1rem' }}>
          {STEPS.map((row) => (
            <li key={row.id} className={step === row.id ? 'active' : step > row.id ? 'done' : ''}>
              <button
                type="button"
                disabled={(row.id > step && !complete[row.id - 1]) || (row.id === 5 && !publishDone)}
                onClick={() => {
                  if (row.id === 5) {
                    if (publishDone) setStep(5)
                    return
                  }
                  if (row.id <= step) setStep(row.id)
                }}
              >
                <span className="step-num">{row.id}</span>
                {row.label}
              </button>
            </li>
          ))}
        </ol>
      </div>

      <Accordion>
        <AccordionPanel
          id="plan-catalogo"
          kicker={t.step.planKicker}
          title={t.step.plan}
          summary={`${offer?.sale_order_name || hostLabel(host)} · ${progress.percent}%`}
          open={openPlan}
          onToggle={() => setOpenPlan((value) => !value)}
        >
          {catalogTree.length ? <TreeList nodes={catalogTree} rootLabel={c.catalogReport} /> : <p>{c.progressHint}</p>}
        </AccordionPanel>
        <AccordionPanel
          id="paso-catalogo"
          kicker={t.step.kicker}
          title={t.step.panel.replace('{n}', String(step)).replace('{title}', STEP_TITLES[step])}
          summary={complete[step] ? t.step.complete : busy ? t.step.running : t.step.pending}
          open={openStep}
          onToggle={() => setOpenStep((value) => !value)}
        >
          {step === 1 && (
            <>
              <div className="form-row">
                <span className="gate-site-label">{t.wizard.orderSite}</span>
                <p className="gate-site-value">{hostLabel(host)}</p>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>{c.connectIntro}</p>
              <div className="platform-grid">
                {PLATFORMS.map((row) => (
                  <button
                    key={row.id}
                    type="button"
                    className={`platform-card ${platform === row.id ? 'active' : ''} ${platforms.includes(row.id) ? 'is-live' : ''}`}
                    onClick={() => setPlatform(row.id)}
                  >
                    <div className="platform-card-head">
                      <PlatformMark id={row.id} />
                      <strong>
                        {row.label}
                        {platforms.includes(row.id) ? <span className="platform-live-tag">{t.connect.connectedBadge}</span> : null}
                      </strong>
                    </div>
                    <span className="platform-card-hint">{row.hint}</span>
                  </button>
                ))}
              </div>
              {connected ? (
                <div className="connect-live">
                  <div className="connect-live-head">
                    <PlatformMark id={selected.id} />
                    <div>
                      <p className="connect-live-kicker">{t.connect.connectedTitle}</p>
                      <strong>{selected.label}</strong>
                    </div>
                  </div>
                  <dl className="connect-facts">
                    <div>
                      <dt>{t.connect.platform}</dt>
                      <dd>{selected.label}</dd>
                    </div>
                    <div>
                      <dt>{c.host}</dt>
                      <dd>{hostLabel(host)}</dd>
                    </div>
                  </dl>
                  <p className="gap-ok">✓ {t.connect.shopOk.replace('{platform}', selected.label)}</p>
                </div>
              ) : (
                <p>{c.needShop}</p>
              )}
            </>
          )}

          {step === 2 && (
            <>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>{c.catalogIntro}</p>
              {needsMoreFichas ? (
                <div className="catalog-buy-panel" style={{ marginBottom: '1rem' }}>
                  <p className="error-msg" style={{ marginBottom: '0.5rem' }}>
                    {(c.buyToFinishHint || c.noCredits)
                      .replace('{processed}', String(used))
                      .replace('{needed}', String(neededQty))}
                  </p>
                  <a
                    className="btn gate-acquire"
                    href={withAcquireParams(offer?.acquire_url || CATALOG_PRODUCT_PAGE_URL, host, neededQty)}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <IconCart />
                    {(c.buyToFinish || c.acquireMore).replace('{qty}', String(neededQty))}
                  </a>
                </div>
              ) : null}
              {run?.total ? (
                <div className="catalog-queue-panel" role="status" aria-live="polite">
                  <p className="catalog-block-caption">
                    {run.caption}
                    {' · '}
                    {c.progressCount.replace('{done}', String(run.done || 0)).replace('{total}', String(run.total || 0))}
                    {' · '}
                    {run.injected || 0} en la tienda
                  </p>
                  <div className="catalog-progress" aria-hidden="true">
                    <span style={{ width: `${run.total ? Math.round(((run.done || 0) / run.total) * 100) : 0}%` }} />
                  </div>
                  <p className="catalog-block-caption">{c.queueOut}</p>
                  <ol className="catalog-queue">
                    {(run.left || []).map((row) => (
                      <li key={`run-out-${row.id}`} className="catalog-queue-item is-analyzed">
                        <span className="catalog-queue-copy">
                          <span>{row.name || row.id}</span>
                          {row.title ? <small>{row.title}</small> : null}
                        </span>
                        <strong>{row.source === 'ollama' ? c.engine : c.analyzed}</strong>
                      </li>
                    ))}
                  </ol>
                  <p className="catalog-block-caption">{c.queueIn}</p>
                  <ol className="catalog-queue">
                    {(run.window || []).map((row) => (
                      <li key={`run-in-${row.id}`} className={`catalog-queue-item is-${row.state}`}>
                        <span>{row.name || row.id}</span>
                        <strong>{stateLabel(row.state, c)}</strong>
                      </li>
                    ))}
                  </ol>
                  <p>{run.done >= run.total ? c.analyzed : c.analyzing}</p>
                </div>
              ) : !session ? (
                <button type="button" className="btn btn-compact" disabled={busy || !connected} onClick={startScan}>
                  <IconSearch />
                  <span>{busy ? c.analyzing : c.analyze}</span>
                </button>
              ) : (
                <div className="catalog-queue-panel" role="status" aria-live="polite">
                  <p className="catalog-block-caption">
                    {session.queue?.caption}
                    {' · '}
                    {c.progressCount
                      .replace('{done}', String(session.analyzed_count || 0))
                      .replace('{total}', String(session.total || 0))}
                  </p>
                  <div className="catalog-progress" aria-hidden="true">
                    <span style={{ width: `${session.total ? Math.round(((session.analyzed_count || 0) / session.total) * 100) : 0}%` }} />
                  </div>
                  <p className="catalog-block-caption">{c.queueOut}</p>
                  <ol className="catalog-queue">
                    {(session.left || []).map((row) => (
                      <li key={`out-${row.id}`} className="catalog-queue-item is-analyzed">
                        <span className="catalog-queue-copy">
                          <span>{row.name || row.id}</span>
                          {row.title ? <small>{row.title}</small> : null}
                        </span>
                        <strong>{row.source === 'ollama' ? c.engine : c.analyzed}</strong>
                      </li>
                    ))}
                  </ol>
                  <p className="catalog-block-caption">{c.queueIn}</p>
                  <ol className="catalog-queue">
                    {windowRows.map((row) => (
                      <li key={row.id} className={`catalog-queue-item is-${row.state}`}>
                        <span>{row.name || row.id}</span>
                        <strong>{stateLabel(row.state, c)}</strong>
                      </li>
                    ))}
                  </ol>
                  {session.done ? <p className="gap-ok">✓ {session.analyzed_count} · {c.analyzed}</p> : <p>{c.analyzing}</p>}
                </div>
              )}
            </>
          )}

          {step === 3 && (
            <>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>{c.aeoIntro}</p>
              {analyzed.length ? (
                <TreeList
                  nodes={analyzed.map((item) => ({
                    label: item.name,
                    value: item.url,
                    children: (item.pack?.faq || []).map((qa) => ({ label: qa.question, value: qa.answer })),
                  }))}
                  rootLabel={c.stepAeo}
                />
              ) : (
                <p>{c.progressHint}</p>
              )}
            </>
          )}

          {step === 4 && (
            <>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>{c.seoIntro}</p>
              {analyzed.length ? (
                <TreeList
                  nodes={analyzed.map((item) => ({
                    label: item.name,
                    value: item.pack?.seo?.title,
                    children: [
                      { label: 'meta_description', value: item.pack?.seo?.meta_description },
                      { label: 'canonical', value: item.pack?.seo?.canonical },
                    ],
                  }))}
                  rootLabel={c.stepSeo}
                />
              ) : (
                <p>{c.progressHint}</p>
              )}
            </>
          )}

          {step === 5 && (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{c.reportIntro}</p>
          )}
        </AccordionPanel>
      </Accordion>

      {error ? <p className="error-msg">{error}</p> : null}

      <div className="wizard-nav">
        <button type="button" className="btn btn-secondary btn-compact" disabled={step === 1 || busy} onClick={() => setStep((n) => Math.max(1, n - 1))}>
          <IconChevronLeft />
          <span>{t.step.back}</span>
        </button>
        {step < 5 ? (
          <button
            type="button"
            className="btn btn-compact"
            disabled={!canContinue || busy || publishing}
            onClick={() => (step === 4 ? publishSheet() : setStep((n) => n + 1))}
          >
            <span>{step === 4 ? (publishing ? c.publishing : c.publishNext) : t.step.continue}</span>
            <IconChevronRight />
          </button>
        ) : (
          <span className="badge badge-muted">{t.step.last}</span>
        )}
      </div>
    </>
  )
}
