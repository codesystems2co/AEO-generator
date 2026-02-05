import { useState } from 'react'
import { api } from '../api'
import '../App.css'

export default function Keywords() {
  const [text, setText] = useState('')
  const [maxKeywords, setMaxKeywords] = useState(10)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const data = await api.keywords.extract({ text, max_keywords: maxKeywords })
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
        <h3>Extract keywords</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Content *</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste your article or page content…"
              rows={8}
              required
            />
          </div>
          <div className="form-row">
            <label>Max keywords</label>
            <input
              type="number"
              min={1}
              max={50}
              value={maxKeywords}
              onChange={(e) => setMaxKeywords(Number(e.target.value))}
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Extracting…' : 'Extract keywords'}
          </button>
        </form>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {result && (
        <div className="card">
          <h3>Keywords (word count: {result.word_count})</h3>
          <ul className="list-unstyled">
            {result.keywords.map(({ keyword, count, density }) => (
              <li key={keyword}>
                <strong>{keyword}</strong> — {count} × ({density}%)
              </li>
            ))}
          </ul>
          {result.suggestions?.length > 0 && (
            <>
              <h3 style={{ marginTop: '1rem' }}>Suggestions</h3>
              <ul className="list-unstyled">
                {result.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </>
  )
}
