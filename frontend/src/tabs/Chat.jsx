import { useState, useRef, useEffect } from 'react'
import { api } from '../api'
import '../App.css'

const STARTERS = [
  'Optimizar Arkiphere Cloud',
  'Tengo un negocio nuevo',
  'Mejorar mi landing',
]

const WELCOME =
  '¡Hola! Soy tu coach AEO. Puedo ayudarte a optimizar Arkiphere Cloud (https://arkiphere.cloud) / AnyApp PaaS o tu propio negocio. ¿Sobre qué quieres trabajar?'

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: WELCOME },
  ])
  const [input, setInput] = useState('')
  const [businessName, setBusinessName] = useState('Arkiphere Cloud')
  const [url, setUrl] = useState('https://arkiphere.cloud')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [suggestions, setSuggestions] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, suggestions, loading])

  async function send(text) {
    const content = (text ?? input).trim()
    if (!content || loading) return
    setError(null)
    setSuggestions(null)
    const next = [...messages, { role: 'user', content }]
    setMessages(next)
    setInput('')
    setLoading(true)
    try {
      const data = await api.chat.send({
        messages: next.filter((m) => m.role === 'user' || m.role === 'assistant'),
        business_name: businessName || undefined,
        url: url || undefined,
        locale: 'es',
      })
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply || '(sin respuesta)' }])
      if (data.suggestions) setSuggestions(data.suggestions)
    } catch (err) {
      setError(err.message || 'Error al contactar el chat')
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    send()
  }

  return (
    <>
      <div className="card">
        <h3>Chat IA — Coach AEO</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Conversación en español para proponer títulos, meta, keywords, H2 y FAQ orientados a motores de respuesta.
        </p>
        <div className="form-row">
          <label>Negocio (opcional)</label>
          <input
            value={businessName}
            onChange={(e) => setBusinessName(e.target.value)}
            placeholder="Arkiphere Cloud"
          />
        </div>
        <div className="form-row">
          <label>URL (opcional)</label>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://arkiphere.cloud"
          />
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
          {STARTERS.map((s) => (
            <button
              key={s}
              type="button"
              className="btn btn-secondary"
              disabled={loading}
              onClick={() => send(s)}
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
            >
              {s}
            </button>
          ))}
        </div>

        <div
          className="output"
          style={{
            maxHeight: 360,
            overflowY: 'auto',
            background: 'var(--bg)',
            border: '1px solid var(--border)',
            borderRadius: 6,
            padding: '0.75rem',
            marginBottom: '1rem',
          }}
        >
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                marginBottom: '0.75rem',
                textAlign: m.role === 'user' ? 'right' : 'left',
              }}
            >
              <div
                style={{
                  display: 'inline-block',
                  maxWidth: '90%',
                  padding: '0.6rem 0.85rem',
                  borderRadius: 8,
                  background: m.role === 'user' ? 'var(--accent-glow)' : 'var(--surface-hover)',
                  border: '1px solid var(--border)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontSize: '0.95rem',
                }}
              >
                <strong style={{ color: 'var(--accent)', fontSize: '0.75rem' }}>
                  {m.role === 'user' ? 'Tú' : 'Coach AEO'}
                </strong>
                <div style={{ marginTop: 4 }}>{m.content}</div>
              </div>
            </div>
          ))}
          {loading && (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Pensando…</p>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <label>Tu mensaje</label>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ej: Quiero optimizar Arkiphere Cloud para que ChatGPT recomiende el PaaS…"
              rows={3}
              disabled={loading}
            />
          </div>
          <button type="submit" className="btn" disabled={loading || !input.trim()}>
            {loading ? 'Enviando…' : 'Enviar'}
          </button>
        </form>
        {error && <p className="error-msg">{error}</p>}
      </div>

      {suggestions && (
        <>
          {suggestions.suggested_title && (
            <div className="card">
              <h3>Título sugerido (AEO)</h3>
              <p style={{ fontSize: '1.1rem', margin: 0 }}>{suggestions.suggested_title}</p>
            </div>
          )}
          {suggestions.summary && (
            <div className="card">
              <h3>Resumen</h3>
              <p style={{ margin: 0 }}>{suggestions.summary}</p>
            </div>
          )}
          {suggestions.key_entities?.length > 0 && (
            <div className="card">
              <h3>Entidades / keywords</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {suggestions.key_entities.map((e, i) => (
                  <span key={i} className="badge badge-muted">{e}</span>
                ))}
              </div>
            </div>
          )}
          {suggestions.questions_answers?.length > 0 && (
            <div className="card">
              <h3>FAQ sugeridas</h3>
              {suggestions.questions_answers.map((qa, i) => (
                <div key={i} style={{ marginBottom: '1rem' }}>
                  <strong style={{ color: 'var(--accent)' }}>P: {qa.question}</strong>
                  <p style={{ margin: '0.35rem 0 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    R: {qa.answer}
                  </p>
                </div>
              ))}
            </div>
          )}
          {suggestions.structured_sections?.length > 0 && (
            <div className="card">
              <h3>Esquema H2</h3>
              <ol style={{ margin: 0, paddingLeft: '1.25rem' }}>
                {suggestions.structured_sections.map((s, i) => (
                  <li key={i} style={{ marginBottom: '0.35rem' }}>{s}</li>
                ))}
              </ol>
            </div>
          )}
        </>
      )}
    </>
  )
}
