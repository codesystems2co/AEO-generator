import { useState } from 'react'
import { api } from '../api'
import '../App.css'

export default function NLP() {
  const [text, setText] = useState('')
  const [mode, setMode] = useState('readability')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      if (mode === 'readability') {
        const data = await api.nlp.readability({ text })
        setResult(data)
      } else {
        const data = await api.nlp.keywords({ text, method: 'rake', max_keywords: 15 })
        setResult(data)
      }
    } catch (err) {
      setError(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="card">
        <h3>NLP: Readability & RAKE keywords</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Readability (Flesch, SMOG, ARI) and RAKE keyword extraction.
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Content *</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste text for analysis…"
              rows={8}
              required
            />
          </div>
          <div className="form-row">
            <label>Mode</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              style={{ padding: '0.6rem', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)' }}
            >
              <option value="readability">Readability</option>
              <option value="rake">RAKE keywords</option>
            </select>
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
        </form>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {result && mode === 'readability' && (
        <div className="card">
          <h3>Readability</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
            <span className="badge badge-muted">Flesch: {result.flesch_reading_ease}</span>
            <span className="badge badge-muted">Flesch–Kincaid grade: {result.flesch_kincaid_grade}</span>
            <span className="badge badge-muted">SMOG: {result.smog_index}</span>
            <span className="badge badge-muted">ARI: {result.automated_readability_index}</span>
            <span className="badge badge-muted">Sentences: {result.sentence_count}</span>
            <span className="badge badge-muted">Words: {result.word_count}</span>
          </div>
          <p style={{ margin: 0 }}>{result.interpretation}</p>
        </div>
      )}

      {result && mode === 'rake' && (
        <div className="card">
          <h3>RAKE keywords (method: {result.method})</h3>
          <ul className="list-unstyled">
            {(result.keywords || []).map((kw, i) => (
              <li key={i}>{typeof kw === 'string' ? kw : kw.phrase}</li>
            ))}
          </ul>
          {result.word_count != null && <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>Word count: {result.word_count}</p>}
        </div>
      )}
    </>
  )
}
