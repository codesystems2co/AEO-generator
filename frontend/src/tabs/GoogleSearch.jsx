import { useEffect, useState } from 'react'
import { api } from '../api'
import '../App.css'

export default function GoogleSearch() {
  const [siteUrl, setSiteUrl] = useState('https://arkiphere.cloud')
  const [mode, setMode] = useState('oauth')
  const [status, setStatus] = useState(null)
  const [result, setResult] = useState(null)
  const [sites, setSites] = useState(null)
  const [saJson, setSaJson] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [info, setInfo] = useState(null)

  async function refreshStatus() {
    try {
      const data = await api.google.status()
      setStatus(data)
      if (data?.mode && data.mode !== 'unset') setMode(data.mode)
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    refreshStatus()
  }, [])

  async function runReadiness(e) {
    e?.preventDefault()
    setError(null)
    setInfo(null)
    setLoading(true)
    try {
      const data = await api.google.readiness({ site_url: siteUrl, mode })
      setResult(data)
    } catch (err) {
      setError(err.message || 'Readiness check failed')
    } finally {
      setLoading(false)
    }
  }

  async function startConsent() {
    setError(null)
    setInfo(null)
    setLoading(true)
    try {
      const data = await api.google.oauthStart()
      if (data.auth_url) {
        window.location.href = data.auth_url
        return
      }
      setError('No consent URL returned')
    } catch (err) {
      setError(err.message || 'OAuth start failed')
    } finally {
      setLoading(false)
    }
  }

  async function loadSites() {
    setError(null)
    try {
      const data = await api.google.sites()
      setSites(data)
    } catch (err) {
      setError(err.message)
    }
  }

  async function saveSa(e) {
    e.preventDefault()
    setError(null)
    setInfo(null)
    try {
      const data = await api.google.saSession({ json_key: saJson })
      if (data.ok) {
        setInfo(data.message)
        setMode('service_account')
        await refreshStatus()
      } else {
        setError(data.error || 'Invalid service account JSON')
      }
    } catch (err) {
      setError(err.message)
    }
  }

  const oauth = status?.modes?.oauth || {}
  const sa = status?.modes?.service_account || {}

  return (
    <>
      <div className="card">
        <h3>Google Search readiness</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Public crawl checks plus Search Console auth. Choose <strong>OAuth</strong> (client consent)
          or <strong>Service Account</strong>. The generator never replaces AEO Core.
        </p>
        <div className="mode-grid">
          <button
            type="button"
            className={`mode-card ${mode === 'oauth' ? 'active' : ''}`}
            onClick={() => setMode('oauth')}
          >
            <strong>OAuth — client consent</strong>
            <span>
              {oauth.configured
                ? oauth.connected
                  ? 'Client ID set · consent granted'
                  : 'Client ID set · waiting for consent'
                : 'Set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET on the API'}
            </span>
          </button>
          <button
            type="button"
            className={`mode-card ${mode === 'service_account' ? 'active' : ''}`}
            onClick={() => setMode('service_account')}
          >
            <strong>Service Account</strong>
            <span>
              {sa.valid_json || sa.configured
                ? `Key present${sa.client_email ? ` · ${sa.client_email}` : ''}`
                : 'Paste a JSON key or set GOOGLE_SA_JSON'}
            </span>
          </button>
        </div>
        <form onSubmit={runReadiness}>
          <div className="form-row">
            <label>Site URL *</label>
            <input
              value={siteUrl}
              onChange={(e) => setSiteUrl(e.target.value)}
              placeholder="https://example.com"
              required
            />
          </div>
          <div className="btn-row">
            <button type="submit" className="btn" disabled={loading}>
              {loading ? 'Checking…' : 'Run readiness'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={startConsent} disabled={loading}>
              Start Google consent
            </button>
            <button type="button" className="btn btn-secondary" onClick={loadSites}>
              List GSC properties
            </button>
          </div>
        </form>
        {info && <p className="ok-msg">{info}</p>}
        {error && <p className="error-msg">{error}</p>}
      </div>

      {mode === 'service_account' && (
        <div className="card">
          <h3>Service account (session only)</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
            JSON is kept in API memory for this process. It is not written to disk. Share the GSC
            property with the service account email.
          </p>
          <form onSubmit={saveSa}>
            <div className="form-row">
              <label>Google SA JSON key</label>
              <textarea
                value={saJson}
                onChange={(e) => setSaJson(e.target.value)}
                placeholder='{"type":"service_account","client_email":"...","private_key":"..."}'
                rows={5}
              />
            </div>
            <button type="submit" className="btn btn-secondary" disabled={!saJson.trim()}>
              Store SA for this session
            </button>
          </form>
        </div>
      )}

      {result && (
        <div className="card">
          <h3>Checklist</h3>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
            <span className={`badge ${result.ready ? 'badge-success' : 'badge-warn'}`}>
              {result.ready ? 'Ready' : 'Needs work'}
            </span>
            <span className="badge badge-muted">{result.passed}/{result.total} passed</span>
            <span className="badge badge-muted">Mode: {result.mode}</span>
          </div>
          <ul className="list-unstyled">
            {(result.checks || []).map((c, i) => (
              <li key={i} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                <span className={`badge ${c.passed ? 'badge-success' : 'badge-warn'}`}>
                  {c.passed ? 'OK' : 'NO'}
                </span>
                <span>
                  <strong>{c.name}</strong>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{c.message}</div>
                </span>
              </li>
            ))}
          </ul>
          {result.next && <p style={{ margin: '0.75rem 0 0', color: 'var(--text-muted)' }}>{result.next}</p>}
        </div>
      )}

      {sites && (
        <div className="card">
          <h3>Search Console properties</h3>
          {sites.ok === false && <p className="error-msg">{sites.error}</p>}
          {(sites.sites || []).length === 0 && sites.ok && (
            <p style={{ color: 'var(--text-muted)' }}>No properties returned for this account.</p>
          )}
          <ul className="list-unstyled">
            {(sites.sites || []).map((s, i) => (
              <li key={i}>
                {s.siteUrl || s.site_url || JSON.stringify(s)}
                {s.permissionLevel ? ` · ${s.permissionLevel}` : ''}
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  )
}
