import { useState } from 'react'
import { api } from '../api'
import '../App.css'

export default function AEO() {
  const [topic, setTopic] = useState('')
  const [context, setContext] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const data = await api.aeo.suggest({
        topic,
        context: context || undefined,
        include_qa: true,
        include_entities: true,
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
        <h3>AEO suggestions</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Get structure and Q&A ideas optimized for answer engines (e.g. ChatGPT, Perplexity).
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Topic *</label>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. how to optimize for AI search"
              required
            />
          </div>
          <div className="form-row">
            <label>Extra context (optional)</label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Audience or angle…"
              rows={2}
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Generating…' : 'Get AEO suggestions'}
          </button>
        </form>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {result && (
        <>
          <div className="card">
            <h3>Suggested title</h3>
            <p style={{ fontSize: '1.1rem', margin: 0 }}>{result.suggested_title}</p>
          </div>
          <div className="card">
            <h3>Summary</h3>
            <p style={{ margin: 0 }}>{result.summary}</p>
          </div>
          {result.key_entities?.length > 0 && (
            <div className="card">
              <h3>Key entities</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {result.key_entities.map((e, i) => (
                  <span key={i} className="badge badge-muted">{e}</span>
                ))}
              </div>
            </div>
          )}
          {result.questions_answers?.length > 0 && (
            <div className="card">
              <h3>Q&A suggestions</h3>
              {result.questions_answers.map((qa, i) => (
                <div key={i} style={{ marginBottom: '1rem' }}>
                  <strong style={{ color: 'var(--accent)' }}>Q: {qa.question}</strong>
                  <p style={{ margin: '0.35rem 0 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    A: {qa.answer}
                  </p>
                </div>
              ))}
            </div>
          )}
          {result.structured_sections?.length > 0 && (
            <div className="card">
              <h3>Suggested sections</h3>
              <ol style={{ margin: 0, paddingLeft: '1.25rem' }}>
                {result.structured_sections.map((s, i) => (
                  <li key={i} style={{ marginBottom: '0.35rem' }}>{s}</li>
                ))}
              </ol>
            </div>
          )}
          {result.tips?.length > 0 && (
            <div className="card">
              <h3>AEO tips</h3>
              <ul className="list-unstyled">
                {result.tips.map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </>
  )
}
