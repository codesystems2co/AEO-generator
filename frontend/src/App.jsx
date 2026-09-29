import React, { useEffect, useState } from 'react'
import Layout from './components/Layout'
import Wizard from './tabs/Wizard'
import CatalogWizard from './tabs/CatalogWizard'
import { copyFor, localeOf } from './i18n/copy'
import './App.css'

function initialLang() {
  try {
    const q = new URLSearchParams(window.location.search).get('lang')
    if (q) return localeOf(q)
  } catch {
    /* ignore */
  }
  return 'es'
}

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="card">
          <p style={{ color: 'var(--text-muted)' }}>
            {String(this.state.error.message || this.state.error)}
          </p>
        </div>
      )
    }
    return this.props.children
  }
}

export default function App() {
  const [lang, setLang] = useState(initialLang)
  const t = copyFor(lang)

  useEffect(() => {
    document.title = t.brand
    document.documentElement.lang = lang
  }, [lang, t.brand])

  const assistant = new URLSearchParams(window.location.search).get('assistant')

  return (
    <Layout brand={t.brand} lang={lang} onLang={(next) => setLang(localeOf(next))}>
      <ErrorBoundary>
        {assistant === 'catalog' ? <CatalogWizard lang={lang} /> : <Wizard lang={lang} />}
      </ErrorBoundary>
    </Layout>
  )
}
