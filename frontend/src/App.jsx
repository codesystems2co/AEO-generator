import React, { useEffect, useState } from 'react'
import Layout from './components/Layout'
import Wizard from './tabs/Wizard'
import CatalogWizard from './tabs/CatalogWizard'
import { copyFor, localeOf } from './i18n/copy'
import { readOrderQuery } from './wizard/orderContext'
import {
  dismissCatalogPromo,
  shouldShowCatalogPromo,
} from './promo/catalogPromo'
import './App.css'

const CATALOG_PRODUCT_URL =
  'https://arkiphere.cloud/shop/product-catalog-aeo-and-seo-pack-with-ia-110'

const PROMO = {
  es: {
    title: 'Pack de catálogo AEO y SEO',
    body:
      'Analiza e inyecta el catálogo completo de la tienda conectada. Precio nativo: 1 unidad de moneda por cada ficha de producto o servicio.',
    cta: 'Ver ficha del producto',
    close: 'Cerrar',
  },
  en: {
    title: 'Catalog AEO and SEO pack',
    body:
      'Analyze and inject the whole connected shop catalog. Native price: 1 currency unit per product or service record.',
    cta: 'View product page',
    close: 'Close',
  },
}

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

function CatalogPromoDialog({ lang, onClose }) {
  const copy = PROMO[lang === 'en' ? 'en' : 'es']

  useEffect(() => {
    function onKey(event) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div
      className="catalog-promo-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="catalog-promo-title"
    >
      <div className="catalog-promo-card">
        <h2 id="catalog-promo-title" className="catalog-promo-title">
          {copy.title}
        </h2>
        <p className="catalog-promo-body">{copy.body}</p>
        <div className="catalog-promo-actions">
          <a
            className="btn"
            href={CATALOG_PRODUCT_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            {copy.cta}
          </a>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            {copy.close}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [lang, setLang] = useState(initialLang)
  const t = copyFor(lang)
  const assistant = readOrderQuery().assistant
  const isCatalogAssistant = assistant === 'catalog'
  const [promoOpen, setPromoOpen] = useState(() => {
    if (isCatalogAssistant) return false
    try {
      const show = shouldShowCatalogPromo(window.sessionStorage)
      // Record on show so a reload in the same visit does not open it again.
      if (show) dismissCatalogPromo(window.sessionStorage)
      return show
    } catch {
      return true
    }
  })

  useEffect(() => {
    document.title = t.brand
    document.documentElement.lang = lang
  }, [lang, t.brand])

  function closePromo() {
    try {
      dismissCatalogPromo(window.sessionStorage)
    } catch {
      /* ignore */
    }
    setPromoOpen(false)
  }

  return (
    <Layout brand={t.brand} lang={lang} onLang={(next) => setLang(localeOf(next))}>
      <ErrorBoundary>
        {isCatalogAssistant ? <CatalogWizard lang={lang} /> : <Wizard lang={lang} />}
      </ErrorBoundary>
      {!isCatalogAssistant && promoOpen ? (
        <CatalogPromoDialog lang={lang} onClose={closePromo} />
      ) : null}
    </Layout>
  )
}
