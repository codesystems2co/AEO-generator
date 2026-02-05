import { useState } from 'react'
import { api } from '../api'
import '../App.css'

export default function ExternalSEO() {
  const [mozUrl, setMozUrl] = useState('')
  const [semrushDomain, setSemrushDomain] = useState('')
  const [mozResult, setMozResult] = useState(null)
  const [semrushResult, setSemrushResult] = useState(null)
  const [loading, setLoading] = useState(null)
  const [error, setError] = useState(null)

  async function handleMoz(e) {
    e.preventDefault()
    setError(null)
    setMozResult(null)
    setLoading('moz')
    try {
      const data = await api.external.moz({ url: mozUrl })
      setMozResult(data)
    } catch (err) {
      setError(err.message || 'Request failed')
    } finally {
      setLoading(null)
    }
  }

  async function handleSemrush(e) {
    e.preventDefault()
    setError(null)
    setSemrushResult(null)
    setLoading('semrush')
    try {
      const data = await api.external.semrush({ domain: semrushDomain, database: 'us' })
      setSemrushResult(data)
    } catch (err) {
      setError(err.message || 'Request failed')
    } finally {
      setLoading(null)
    }
  }

  return (
    <>
      <div className="card">
        <h3>External SEO APIs</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Moz (DA/PA) and SEMrush (domain rank). Set MOZ_ACCESS_ID, MOZ_SECRET_KEY, or SEMRUSH_API_KEY to enable.
        </p>
      </div>

      <div className="card">
        <h3>Moz URL metrics</h3>
        <form onSubmit={handleMoz}>
          <div className="form-row">
            <label>URL</label>
            <input
              value={mozUrl}
              onChange={(e) => setMozUrl(e.target.value)}
              placeholder="https://example.com"
              required
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading === 'moz' ? 'Fetching…' : 'Get Moz metrics'}
          </button>
        </form>
        {mozResult && (
          <div style={{ marginTop: '1rem' }}>
            <p><strong>Available:</strong> {mozResult.available ? 'Yes' : 'No'}</p>
            <p>{mozResult.message}</p>
            {mozResult.domain_authority != null && <p>Domain Authority: {mozResult.domain_authority}</p>}
            {mozResult.page_authority != null && <p>Page Authority: {mozResult.page_authority}</p>}
            {mozResult.spam_score != null && <p>Spam Score: {mozResult.spam_score}</p>}
          </div>
        )}
      </div>

      <div className="card">
        <h3>SEMrush domain overview</h3>
        <form onSubmit={handleSemrush}>
          <div className="form-row">
            <label>Domain</label>
            <input
              value={semrushDomain}
              onChange={(e) => setSemrushDomain(e.target.value)}
              placeholder="example.com"
              required
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading === 'semrush' ? 'Fetching…' : 'Get SEMrush data'}
          </button>
        </form>
        {semrushResult && (
          <div style={{ marginTop: '1rem' }}>
            <p><strong>Available:</strong> {semrushResult.available ? 'Yes' : 'No'}</p>
            <p>{semrushResult.message}</p>
            {semrushResult.rank != null && <p>Rank: {semrushResult.rank}</p>}
          </div>
        )}
      </div>

      {error && <p className="error-msg">{error}</p>}
    </>
  )
}
