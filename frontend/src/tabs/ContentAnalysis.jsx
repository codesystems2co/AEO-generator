import { useState } from 'react'
import { api } from '../api'
import '../App.css'

export default function ContentAnalysis() {
  const [text, setText] = useState('')
  const [targetKeyword, setTargetKeyword] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const data = await api.analysis.content({
        text,
        target_keyword: targetKeyword || undefined,
      })
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
        <h3>Analyze content</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Content *</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste your article or page content…"
              rows={10}
              required
            />
          </div>
          <div className="form-row">
            <label>Target keyword (optional)</label>
            <input
              value={targetKeyword}
              onChange={(e) => setTargetKeyword(e.target.value)}
              placeholder="e.g. SEO tips"
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
        </form>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {result && (
        <div className="card">
          <h3>Metrics</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
            <span className="badge badge-muted">Words: {result.word_count}</span>
            <span className="badge badge-muted">Reading: ~{result.reading_time_minutes} min</span>
            <span className="badge badge-muted">Sentences: {result.sentence_count}</span>
            <span className="badge badge-muted">Paragraphs: {result.paragraph_count}</span>
            {result.keyword_density != null && (
              <span className="badge badge-muted">Keyword density: {result.keyword_density}%</span>
            )}
          </div>
          {result.readability && (
            <>
              <h3>Readability (NLP)</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <span className="badge badge-muted">Flesch: {result.readability.flesch_reading_ease}</span>
                <span className="badge badge-muted">Flesch–Kincaid: {result.readability.flesch_kincaid_grade}</span>
                <span className="badge badge-muted">SMOG: {result.readability.smog_index}</span>
                <span className="badge badge-muted">ARI: {result.readability.automated_readability_index}</span>
              </div>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>{result.readability.interpretation}</p>
            </>
          )}
          {result.headings?.length > 0 && (
            <>
              <h3>Headings</h3>
              <ul className="list-unstyled">
                {result.headings.map((h, i) => (
                  <li key={i}>{h}</li>
                ))}
              </ul>
            </>
          )}
          {result.recommendations?.length > 0 && (
            <>
              <h3>Recommendations</h3>
              <ul className="list-unstyled">
                {result.recommendations.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </>
  )
}
