import { useState } from 'react'
import { api } from '../api'
import '../App.css'

export default function MetaTags() {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [url, setUrl] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [siteName, setSiteName] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const data = await api.meta.generate({
        title,
        description,
        url: url || undefined,
        image_url: imageUrl || undefined,
        site_name: siteName || undefined,
      })
      setResult(data)
    } catch (err) {
      setError(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  function copyHtml() {
    if (!result) return
    const lines = [
      result.title_tag,
      result.meta_description,
      ...Object.entries(result.og_tags).map(([k, v]) => `<meta property="${k}" content="${v}">`),
      ...Object.entries(result.twitter_card).map(([k, v]) => `<meta name="${k}" content="${v}">`),
    ]
    if (result.canonical) lines.push(`<link rel="canonical" href="${result.canonical}">`)
    navigator.clipboard.writeText(lines.join('\n'))
  }

  return (
    <>
      <div className="card">
        <h3>Generate meta tags</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Title *</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Page title (30–60 chars ideal)"
              required
            />
          </div>
          <div className="form-row">
            <label>Meta description *</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Short description (120–160 chars ideal)"
              rows={2}
              required
            />
          </div>
          <div className="form-row">
            <label>URL (canonical)</label>
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/page"
            />
          </div>
          <div className="form-row">
            <label>Image URL (OG/Twitter)</label>
            <input
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://example.com/og-image.jpg"
            />
          </div>
          <div className="form-row">
            <label>Site name</label>
            <input
              value={siteName}
              onChange={(e) => setSiteName(e.target.value)}
              placeholder="My Site"
            />
          </div>
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Generating…' : 'Generate meta tags'}
          </button>
        </form>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {result && (
        <div className="card">
          <h3>Output</h3>
          <button type="button" className="btn btn-secondary" onClick={copyHtml} style={{ marginBottom: '1rem' }}>
            Copy HTML
          </button>
          <div className="output">
            <pre>{result.title_tag}</pre>
            <pre>{result.meta_description}</pre>
            {Object.entries(result.og_tags).map(([k, v]) => (
              <pre key={k}>{`<meta property="${k}" content="${v}">`}</pre>
            ))}
            {Object.entries(result.twitter_card).map(([k, v]) => (
              <pre key={k}>{`<meta name="${k}" content="${v}">`}</pre>
            ))}
            {result.canonical && <pre>{`<link rel="canonical" href="${result.canonical}">`}</pre>}
          </div>
        </div>
      )}
    </>
  )
}
