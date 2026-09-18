import { useEffect, useState } from 'react'
import { api } from '../api'
import TreeList from '../components/TreeList'
import '../App.css'

export default function Packs() {
  const [topic, setTopic] = useState('Arkiphere Cloud')
  const [url, setUrl] = useState('https://arkiphere.cloud')
  const [businessName, setBusinessName] = useState('Arkiphere Cloud')
  const [context, setContext] = useState('Odoo PaaS, Community and Enterprise, free trial, AI billing.')
  const [health, setHealth] = useState(null)
  const [pack, setPack] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.packs.health().then(setHealth).catch((err) => setHealth({ status: 'error', error: err.message }))
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await api.packs.generate({
        topic,
        url: url || undefined,
        business_name: businessName || undefined,
        context: context || undefined,
        locale: 'en',
      })
      setPack(data)
    } catch (err) {
      setError(err.message || 'Pack generation failed')
    } finally {
      setLoading(false)
    }
  }

  function copyResume() {
    if (pack?.resume) navigator.clipboard.writeText(pack.resume)
  }

  return (
    <>
      <div className="card">
        <h3>AEO + SEO pack</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Generate a publish pack and a human-readable tree resume for your site.
        </p>
        {health && (
          <p style={{ marginBottom: '1rem' }}>
            <span className={`badge ${health.status === 'ok' ? 'badge-success' : 'badge-warn'}`}>
              Pack service {health.status}
            </span>
            
          </p>
        )}
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Topic / brand *</label>
            <input value={topic} onChange={(e) => setTopic(e.target.value)} required />
          </div>
          <div className="form-row">
            <label>Business name</label>
            <input value={businessName} onChange={(e) => setBusinessName(e.target.value)} />
          </div>
          <div className="form-row">
            <label>URL</label>
            <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://" />
          </div>
          <div className="form-row">
            <label>Facts / context</label>
            <textarea value={context} onChange={(e) => setContext(e.target.value)} rows={3} />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Generating pack…' : 'Generate AEO + SEO pack'}
          </button>
        </form>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {pack && (
        <>
          <div className="card">
            <h3>Tree list resume</h3>
            <div className="btn-row" style={{ marginBottom: '0.75rem' }}>
              <span className="badge badge-muted">pack ready</span>
              
              <button type="button" className="btn btn-secondary" onClick={copyResume}>Copy resume</button>
            </div>
            <TreeList nodes={pack.tree} rootLabel={pack.topic} />
            <pre className="resume-pre">{pack.resume}</pre>
          </div>
          {pack.aeo && (
            <div className="card">
              <h3>AEO</h3>
              <p style={{ fontSize: '1.05rem' }}>{pack.aeo.suggested_title}</p>
              <p style={{ color: 'var(--text-muted)' }}>{pack.aeo.summary}</p>
            </div>
          )}
          {pack.seo && (
            <div className="card">
              <h3>SEO</h3>
              <p><strong>Title:</strong> {pack.seo.title}</p>
              <p><strong>Meta:</strong> {pack.seo.meta_description}</p>
              {pack.seo.score && (
                <p>
                  <span className="badge badge-success">
                    Score {pack.seo.score.overall_score}/{pack.seo.score.max_score} · {pack.seo.score.grade}
                  </span>
                </p>
              )}
            </div>
          )}
        </>
      )}
    </>
  )
}
