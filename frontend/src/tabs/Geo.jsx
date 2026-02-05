import { useState } from 'react'
import { api } from '../api'
import '../App.css'

export default function Geo() {
  const [activeTab, setActiveTab] = useState('analyze')

  return (
    <>
      <div className="card">
        <h3>GEO (Generative Engine Optimization)</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Optimize content for AI-powered search engines like ChatGPT, Perplexity, and Google AI Overviews.
        </p>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
          <button
            className={`btn ${activeTab === 'analyze' ? '' : 'btn-secondary'}`}
            onClick={() => setActiveTab('analyze')}
          >
            Analyze Content
          </button>
          <button
            className={`btn ${activeTab === 'optimize' ? '' : 'btn-secondary'}`}
            onClick={() => setActiveTab('optimize')}
          >
            Get Suggestions
          </button>
          <button
            className={`btn ${activeTab === 'citations' ? '' : 'btn-secondary'}`}
            onClick={() => setActiveTab('citations')}
          >
            Enhance Citations
          </button>
        </div>
      </div>

      {activeTab === 'analyze' && <GEOAnalyze />}
      {activeTab === 'optimize' && <GEOOptimize />}
      {activeTab === 'citations' && <GEOCitations />}
    </>
  )
}

function GEOAnalyze() {
  const [content, setContent] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const data = await api.geo.analyze({ content })
      setResult(data)
    } catch (err) {
      setError(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  const gradeColor = result?.grade === 'A' ? 'badge-success' : 
                     result?.grade === 'B' ? 'badge-success' : 
                     result?.grade === 'C' ? 'badge-warn' : 'badge-muted'

  return (
    <>
      <div className="card">
        <h4>Analyze Content for GEO</h4>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
          Check if your content is optimized for AI citation: statistics, sources, quotable definitions, and structure.
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Content *</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste your content here (at least 50 characters)..."
              rows={8}
              required
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Analyzing…' : 'Analyze for GEO'}
          </button>
        </form>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {result && (
        <>
          <div className="card">
            <h4>GEO Score</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <span className="badge" style={{ fontSize: '1.5rem', padding: '0.4rem 0.75rem' }}>
                {result.geo_score} / {result.max_score}
              </span>
              <span className={`badge ${gradeColor}`}>Grade: {result.grade}</span>
              <span className="badge badge-muted">{result.word_count} words</span>
            </div>
          </div>

          <div className="card">
            <h4>GEO Checks</h4>
            <ul className="list-unstyled">
              {result.checks.map((c, i) => (
                <li key={i} style={{ marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
                    <span className={`badge ${c.passed ? 'badge-success' : 'badge-warn'}`}>
                      {c.score}/{c.max_score}
                    </span>
                    <strong>{c.name}</strong>
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{c.message}</div>
                  {c.examples && c.examples.length > 0 && (
                    <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {c.examples.slice(0, 5).map((ex, j) => (
                        <span key={j} className="badge" style={{ fontSize: '0.8rem' }}>{ex}</span>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h4>Structure Summary</h4>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <span className="badge">{result.structure_summary.heading_count} headings</span>
              <span className="badge">{result.structure_summary.list_item_count} list items</span>
              <span className="badge">{result.structure_summary.paragraph_count} paragraphs</span>
              <span className="badge">{result.structure_summary.question_count} questions</span>
              <span className={`badge ${result.structure_summary.short_paragraph_ratio >= 0.5 ? 'badge-success' : 'badge-warn'}`}>
                {Math.round(result.structure_summary.short_paragraph_ratio * 100)}% short paragraphs
              </span>
            </div>
          </div>

          {result.recommendations.length > 0 && (
            <div className="card">
              <h4>Recommendations</h4>
              <ul className="list-unstyled">
                {result.recommendations.map((r, i) => (
                  <li key={i} style={{ marginBottom: '0.5rem' }}>💡 {r}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </>
  )
}

function GEOOptimize() {
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
      const data = await api.geo.optimize({
        topic,
        context: context || undefined,
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
        <h4>Get GEO Optimization Suggestions</h4>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
          Get templates and structure suggestions to make your content more likely to be cited by AI.
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Topic *</label>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., content marketing, machine learning, sustainable energy"
              required
            />
          </div>
          <div className="form-row">
            <label>Context (optional)</label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Any additional context about your content..."
              rows={2}
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Generating…' : 'Get Suggestions'}
          </button>
        </form>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {result && (
        <>
          <div className="card">
            <h4>Suggested Definition</h4>
            <p style={{ fontStyle: 'italic', background: 'var(--bg-dark)', padding: '1rem', borderRadius: '8px' }}>
              {result.suggested_definition}
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Start your content with a clear, quotable definition like this.
            </p>
          </div>

          <div className="card">
            <h4>Q&A Pairs for AI Queries</h4>
            <ul className="list-unstyled">
              {result.qa_pairs.map((qa, i) => (
                <li key={i} style={{ marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
                  <strong style={{ color: 'var(--accent)' }}>Q: {qa.question}</strong>
                  <p style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)' }}>A: {qa.answer}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h4>Citation Templates</h4>
            <ul className="list-unstyled">
              {result.citation_templates.map((t, i) => (
                <li key={i} style={{ marginBottom: '0.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>
                  {t}
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h4>Statistic Templates</h4>
            <ul className="list-unstyled">
              {result.statistic_templates.map((t, i) => (
                <li key={i} style={{ marginBottom: '0.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>
                  {t}
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h4>Suggested Content Structure</h4>
            <pre style={{ background: 'var(--bg-dark)', padding: '1rem', borderRadius: '8px', overflow: 'auto', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>
              {result.suggested_structure}
            </pre>
          </div>

          <div className="card">
            <h4>GEO Best Practices</h4>
            <ul className="list-unstyled">
              {result.tips.map((tip, i) => (
                <li key={i} style={{ marginBottom: '0.5rem' }}>✓ {tip}</li>
              ))}
            </ul>
          </div>
        </>
      )}
    </>
  )
}

function GEOCitations() {
  const [content, setContent] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const data = await api.geo.citations({ content })
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
        <h4>Enhance Citations & Statistics</h4>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
          Find sentences that need citations or specific data, and get suggestions for improvement.
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Content *</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste your content here..."
              rows={8}
              required
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Analyzing…' : 'Find Enhancement Opportunities'}
          </button>
        </form>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {result && (
        <>
          <div className="card">
            <h4>Current Status</h4>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <span className={`badge ${result.current_citation_count >= 2 ? 'badge-success' : 'badge-warn'}`}>
                {result.current_citation_count} citations found
              </span>
              <span className={`badge ${result.current_statistic_count >= 2 ? 'badge-success' : 'badge-warn'}`}>
                {result.current_statistic_count} statistics found
              </span>
            </div>
          </div>

          {result.citation_enhancements.length > 0 && (
            <div className="card">
              <h4>Sentences That Need Citations</h4>
              <ul className="list-unstyled">
                {result.citation_enhancements.map((item, i) => (
                  <li key={i} style={{ marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <span className="badge badge-warn">{item.type}</span>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <strong>Original:</strong> <span style={{ color: 'var(--text-muted)' }}>{item.original}</span>
                    </div>
                    <div>
                      <strong>Suggestion:</strong> <span style={{ color: 'var(--accent)' }}>{item.suggestion}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.statistic_opportunities.length > 0 && (
            <div className="card">
              <h4>Opportunities to Add Statistics</h4>
              <ul className="list-unstyled">
                {result.statistic_opportunities.map((item, i) => (
                  <li key={i} style={{ marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <span className="badge badge-warn">{item.type}</span>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <strong>Original:</strong> <span style={{ color: 'var(--text-muted)' }}>{item.original}</span>
                    </div>
                    <div>
                      <strong>Tip:</strong> <span style={{ color: 'var(--accent)' }}>{item.suggestion}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.citation_enhancements.length === 0 && result.statistic_opportunities.length === 0 && (
            <div className="card">
              <p style={{ color: 'var(--text-muted)' }}>
                ✓ Your content already has good citation and statistic coverage!
              </p>
            </div>
          )}
        </>
      )}
    </>
  )
}
