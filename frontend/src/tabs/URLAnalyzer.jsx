import { useState } from 'react'
import { api } from '../api'
import '../App.css'

export default function URLAnalyzer() {
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
      const data = await api.url.analyze({ url })
      setResult(data)
    } catch (err) {
      setError(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="card">
        <h3>URL analyzer</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Fetch a URL and extract meta tags, headings, and word count.
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>URL *</label>
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/page"
              required
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Fetching…' : 'Analyze URL'}
          </button>
        </form>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {result && (
        <div className="card">
          <h3>Result: {result.url}</h3>
          {result.error && <p className="error-msg">{result.error}</p>}
          {result.status_code != null && <p><strong>Status:</strong> {result.status_code}</p>}
          {result.title != null && <p><strong>Title:</strong> {result.title}</p>}
          {result.meta_description != null && <p><strong>Meta description:</strong> {result.meta_description}</p>}
          {result.og_title != null && <p><strong>OG title:</strong> {result.og_title}</p>}
          {result.h1_list?.length > 0 && (
            <>
              <h3 style={{ marginTop: '1rem' }}>H1</h3>
              <ul className="list-unstyled">{result.h1_list.map((h, i) => <li key={i}>{h}</li>)}</ul>
            </>
          )}
          {result.headings?.length > 0 && (
            <>
              <h3 style={{ marginTop: '1rem' }}>Headings</h3>
              <ul className="list-unstyled">{result.headings.slice(0, 20).map((h, i) => <li key={i}>{h}</li>)}</ul>
            </>
          )}
          <p style={{ marginTop: '1rem' }}><strong>Word count:</strong> {result.word_count}</p>
        </div>
      )}
    </>
  )
}
