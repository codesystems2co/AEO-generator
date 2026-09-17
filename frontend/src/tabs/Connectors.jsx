import { useEffect, useState } from 'react'
import { api } from '../api'
import '../App.css'

const PLATFORMS = [
  { id: 'odoo', label: 'Odoo', hint: 'website.page / product.template SEO fields' },
  { id: 'prestashop', label: 'PrestaShop', hint: 'meta_title / meta_description / link_rewrite' },
  { id: 'woocommerce', label: 'WooCommerce', hint: 'Yoast / rank math / product or post meta' },
]

export default function Connectors() {
  const [platform, setPlatform] = useState('odoo')
  const [health, setHealth] = useState(null)
  const [url, setUrl] = useState('')
  const [database, setDatabase] = useState('')
  const [username, setUsername] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [target, setTarget] = useState('')
  const [title, setTitle] = useState('')
  const [meta, setMeta] = useState('')
  const [keywords, setKeywords] = useState('')
  const [canonical, setCanonical] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(null)
  const [error, setError] = useState(null)

  async function refreshHealth() {
    try {
      setHealth(await api.connectors.health())
    } catch (err) {
      setHealth({ reachable: false, message: err.message })
    }
  }

  useEffect(() => {
    refreshHealth()
  }, [])

  function payload() {
    return {
      platform,
      target: target || undefined,
      connection: {
        url,
        database: database || undefined,
        username: username || undefined,
        api_key: apiKey || undefined,
      },
      seo: {
        title,
        meta_description: meta,
        keywords: keywords.split(',').map((s) => s.trim()).filter(Boolean),
        canonical: canonical || undefined,
      },
    }
  }

  async function run(action) {
    setError(null)
    setResult(null)
    setLoading(action)
    try {
      const data = action === 'write'
        ? await api.connectors.write(payload())
        : await api.connectors.verify(payload())
      setResult(data)
      if (data.core) setHealth(data.core)
    } catch (err) {
      setError(err.message || 'Core request failed')
    } finally {
      setLoading(null)
    }
  }

  return (
    <>
      <div className="card">
        <h3>Connectors — write / verify via AEO Core</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          This UI only forwards to Core <code>server.py</code> on <strong>:18642</strong>. It does not
          implement Odoo / PrestaShop / WooCommerce writes itself.
        </p>
        {health && (
          <p>
            <span className={`badge ${health.reachable ? 'badge-success' : 'badge-warn'}`}>
              Core {health.reachable ? 'reachable' : 'offline'}
            </span>
            <span className="badge badge-muted" style={{ marginLeft: 8 }}>{health.core_url}</span>
          </p>
        )}
        {health?.message && (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{health.message}</p>
        )}
        <button type="button" className="btn btn-secondary" onClick={refreshHealth} style={{ marginTop: 8 }}>
          Re-probe Core
        </button>
      </div>

      <div className="card">
        <h3>Platform</h3>
        <div className="mode-grid">
          {PLATFORMS.map((p) => (
            <button
              key={p.id}
              type="button"
              className={`mode-card ${platform === p.id ? 'active' : ''}`}
              onClick={() => setPlatform(p.id)}
            >
              <strong>{p.label}</strong>
              <span>{p.hint}</span>
            </button>
          ))}
        </div>
        <div className="form-row">
          <label>Instance URL</label>
          <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://shop.example.com" />
        </div>
        <div className="form-row">
          <label>Database / site (optional)</label>
          <input value={database} onChange={(e) => setDatabase(e.target.value)} placeholder="odoo db or blog id" />
        </div>
        <div className="form-row">
          <label>Username</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </div>
        <div className="form-row">
          <label>API key / password</label>
          <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} autoComplete="off" />
        </div>
        <div className="form-row">
          <label>Target record (optional)</label>
          <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="product id, page id, SKU…" />
        </div>
        <div className="form-row">
          <label>SEO title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div className="form-row">
          <label>Meta description</label>
          <textarea value={meta} onChange={(e) => setMeta(e.target.value)} rows={2} />
        </div>
        <div className="form-row">
          <label>Keywords (comma separated)</label>
          <input value={keywords} onChange={(e) => setKeywords(e.target.value)} />
        </div>
        <div className="form-row">
          <label>Canonical URL</label>
          <input value={canonical} onChange={(e) => setCanonical(e.target.value)} />
        </div>
        <div className="btn-row">
          <button type="button" className="btn" disabled={!!loading} onClick={() => run('write')}>
            {loading === 'write' ? 'Writing…' : 'Write SEO via Core'}
          </button>
          <button type="button" className="btn btn-secondary" disabled={!!loading} onClick={() => run('verify')}>
            {loading === 'verify' ? 'Verifying…' : 'Verify via Core'}
          </button>
        </div>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {result && (
        <div className="card">
          <h3>Core response</h3>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
            <span className={`badge ${result.ok ? 'badge-success' : 'badge-warn'}`}>
              {result.ok ? 'OK' : 'Not applied'}
            </span>
            <span className="badge badge-muted">{result.action || 'proxy'}</span>
            {result.platform && <span className="badge badge-muted">{result.platform}</span>}
            {result.path && <span className="badge badge-muted">{result.path}</span>}
            {result.status_code != null && <span className="badge badge-muted">HTTP {result.status_code}</span>}
          </div>
          {result.message && <p style={{ color: 'var(--text-muted)' }}>{result.message}</p>}
          <div className="output">
            <pre>{JSON.stringify(result.data || result, null, 2)}</pre>
          </div>
        </div>
      )}
    </>
  )
}
