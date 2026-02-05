import { useState } from 'react'
import { api } from '../api'
import '../App.css'

export default function SEOScore() {
  const [title, setTitle] = useState('')
  const [metaDescription, setMetaDescription] = useState('')
  const [content, setContent] = useState('')
  const [url, setUrl] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const data = await api.score.calculate({
        title,
        meta_description: metaDescription,
        content,
        url: url || undefined,
      })
      setResult(data)
    } catch (err) {
      setError(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  const gradeClass = result?.grade === 'A' ? 'badge-success' : result?.grade === 'B' ? 'badge-success' : result?.grade === 'C' ? 'badge-warn' : 'badge-muted'

  return (
    <>
      <div className="card">
        <h3>SEO score</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Get a quick score and checklist for title, meta description, and content.
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Title * <span style={{ color: 'var(--text-muted)', fontWeight: 'normal', fontSize: '0.85rem' }}>({title.length}/120 chars)</span></label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Page title (max 120 characters)"
              required
              maxLength={120}
            />
          </div>
          <div className="form-row">
            <label>Meta description * <span style={{ color: 'var(--text-muted)', fontWeight: 'normal', fontSize: '0.85rem' }}>({metaDescription.length}/320 chars)</span></label>
            <textarea
              value={metaDescription}
              onChange={(e) => setMetaDescription(e.target.value)}
              placeholder="Meta description (recommended 120–160 chars, max 320)"
              rows={2}
              required
              maxLength={320}
            />
          </div>
          <div className="form-row">
            <label>Content * <span style={{ color: 'var(--text-muted)', fontWeight: 'normal', fontSize: '0.85rem' }}>({content.length} chars, min 50)</span></label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Full page content (minimum 50 characters)"
              rows={6}
              required
            />
          </div>
          <div className="form-row">
            <label>URL (optional)</label>
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/page"
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Calculating…' : 'Calculate score'}
          </button>
        </form>
        {error && (
          <div className="error-msg" style={{ whiteSpace: 'pre-line' }}>
            <strong>Validation Error:</strong>
            <ul style={{ margin: '0.5rem 0 0 1.25rem', padding: 0 }}>
              {error.split('\n').map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {result && (
        <>
          <div className="card">
            <h3>Score</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <span className="badge" style={{ fontSize: '1.5rem', padding: '0.4rem 0.75rem' }}>
                {result.overall_score} / {result.max_score}
              </span>
              <span className={`badge ${gradeClass}`}>Grade: {result.grade}</span>
            </div>
          </div>
          <div className="card">
            <h3>Checks</h3>
            <ul className="list-unstyled">
              {result.checks.map((c, i) => (
                <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <span className={c.passed ? 'badge badge-success' : 'badge badge-warn'}>
                    {c.score}/{c.max_score}
                  </span>
                  <span>{c.name}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{c.message}</span>
                </li>
              ))}
            </ul>
          </div>
          {result.recommendations?.length > 0 && (
            <div className="card">
              <h3>Recommendations</h3>
              <ul className="list-unstyled">
                {result.recommendations.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </>
  )
}
