import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import '../App.css'
import './Guide.css'

export default function Guide() {
  const [markdown, setMarkdown] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/guide.md')
      .then((res) => {
        if (!res.ok) throw new Error('Guide not found')
        return res.text()
      })
      .then(setMarkdown)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="card"><p className="loading">Loading guide…</p></div>
  if (error) return <div className="card"><p className="error-msg">{error}</p></div>
  if (!markdown) return null

  return (
    <div className="card guide-card">
      <article className="guide-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ href, children }) => (
              <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
            ),
            code: ({ className, children, ...props }) => {
              const isBlock = className?.includes('language-')
              return isBlock ? (
                <pre><code className={className} {...props}>{children}</code></pre>
              ) : (
                <code className="guide-inline-code" {...props}>{children}</code>
              )
            },
          }}
        >
          {markdown}
        </ReactMarkdown>
      </article>
    </div>
  )
}
