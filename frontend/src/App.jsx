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

const PLATFORM_PILLS = [
  {
    key: 'odoo',
    label: 'Odoo',
    logo: '/brand/odoo-mark.svg',
  },
  {
    key: 'prestashop',
    label: 'PrestaShop',
    logo: '/brand/prestashop-favicon.svg',
  },
  {
    key: 'woocommerce',
    label: 'WooCommerce',
    logo: '/brand/woocommerce-logo.png',
  },
]

const PROMO = {
  es: {
    badge: 'AEO · PACK DE CATÁLOGO',
    title: 'Tu catálogo completo: productos y servicios',
    subtitle: '1 por producto o servicio. La cantidad es el número de ítems del catálogo.',
    tiles: [
      {
        key: 'catalog',
        label: 'Catálogo completo',
        text: 'Recorre productos y servicios de la tienda conectada.',
      },
      {
        key: 'aeo',
        label: 'Pack AEO',
        text: 'Añade FAQ y bloques al final de cada descripción.',
      },
      {
        key: 'seo',
        label: 'Pack SEO',
        text: 'Rellena meta título, descripción y palabras clave.',
      },
      {
        key: 'inject',
        label: 'Inyección',
        text: 'Escribe en cada producto y servicio del catálogo.',
      },
    ],
    footer: 'Cantidad = productos y servicios. Precio unitario × cantidad.',
    cta: 'Analizar mi catálogo',
    close: 'Cerrar',
  },
  en: {
    badge: 'AEO · CATALOG PACK',
    title: 'Your whole catalog: products and services',
    subtitle: '1 per product or service. Quantity is the number of catalog items.',
    tiles: [
      {
        key: 'catalog',
        label: 'Full catalog',
        text: 'Walks the products and services of the connected store.',
      },
      {
        key: 'aeo',
        label: 'AEO pack',
        text: 'Appends FAQ and blocks at the end of each description.',
      },
      {
        key: 'seo',
        label: 'SEO pack',
        text: 'Fills meta title, description and keywords only.',
      },
      {
        key: 'inject',
        label: 'Injection',
        text: 'Writes into each product and service in the catalog.',
      },
    ],
    footer: 'Quantity = products and services. Unit price × quantity.',
    cta: 'Analyze my catalog',
    close: 'Close',
  },
}

function GiftIcon() {
  return (
    <svg
      className="catalog-promo-gift"
      viewBox="0 0 24 24"
      width="14"
      height="14"
      aria-hidden="true"
      focusable="false"
    >
      <path
        fill="currentColor"
        d="M20 7h-2.18A3 3 0 0 0 13 4a3 3 0 0 0-4.82 3H6a2 2 0 0 0-2 2v2h16V9a2 2 0 0 0-2-2ZM12 4a1 1 0 1 1 0 2 1 1 0 0 1 0-2Zm-3 2a1 1 0 1 1 0-2 1 1 0 0 1 0 2Zm-5 6v7a2 2 0 0 0 2 2h4v-9H4Zm10 9h4a2 2 0 0 0 2-2v-7h-6v9Z"
      />
    </svg>
  )
}

function TileIcon({ name }) {
  const common = {
    className: 'catalog-promo-tile-icon',
    viewBox: '0 0 24 24',
    width: '18',
    height: '18',
    'aria-hidden': 'true',
    focusable: 'false',
  }
  if (name === 'catalog') {
    return (
      <svg {...common}>
        <path
          fill="currentColor"
          d="M4 4h7v7H4V4Zm9 0h7v7h-7V4ZM4 13h7v7H4v-7Zm9 0h7v7h-7v-7Z"
        />
      </svg>
    )
  }
  if (name === 'aeo') {
    return (
      <svg {...common}>
        <path
          fill="currentColor"
          d="M4 4h12a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H9l-4 3v-3H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Zm2 4h8v2H6V8Zm0 4h5v2H6v-2Z"
        />
      </svg>
    )
  }
  if (name === 'seo') {
    return (
      <svg {...common}>
        <path
          fill="currentColor"
          d="M4 19h16v2H4v-2Zm2-3 4-5 3 3 5-7 1.5 1.2-6.5 9-3-3-2.5 3.1L6 16Z"
        />
      </svg>
    )
  }
  return (
    <svg {...common}>
      <path
        fill="currentColor"
        d="M12 2C7.58 2 4 3.79 4 6v12c0 2.21 3.58 4 8 4s8-1.79 8-4V6c0-2.21-3.58-4-8-4Zm0 2c3.31 0 6 1.12 6 2.5S15.31 9 12 9 6 7.88 6 6.5 8.69 4 12 4Zm0 16c-3.31 0-6-1.12-6-2.5V15c1.4 1.15 3.6 1.85 6 1.85s4.6-.7 6-1.85v2.5c0 1.38-2.69 2.5-6 2.5Zm0-5.15c-3.31 0-6-1.12-6-2.5V9.85C7.4 11 9.6 11.7 12 11.7s4.6-.7 6-1.85V12.35c0 1.38-2.69 2.5-6 2.5Z"
      />
    </svg>
  )
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

function catalogAssistantHref() {
  try {
    const { license, site } = readOrderQuery()
    const params = new URLSearchParams()
    if (license) params.set('license', license)
    if (site) params.set('site', site)
    params.set('assistant', 'catalog')
    const qs = params.toString()
    return `${window.location.pathname}?${qs}${window.location.hash || ''}`
  } catch {
    return `${window.location.pathname}?assistant=catalog`
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
        <div className="catalog-promo-banner">
          <span className="catalog-promo-badge">
            <GiftIcon />
            {copy.badge}
          </span>
          <h2 id="catalog-promo-title" className="catalog-promo-banner-title">
            {copy.title}
          </h2>
          <p className="catalog-promo-banner-subtitle">{copy.subtitle}</p>
          <div className="catalog-promo-tiles">
            {copy.tiles.map((tile) => (
              <div key={tile.key} className="catalog-promo-tile">
                <TileIcon name={tile.key} />
                <div className="catalog-promo-tile-copy">
                  <strong>{tile.label}</strong>
                  <span>{tile.text}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="catalog-promo-pills">
            {PLATFORM_PILLS.map((pill) => (
              <span key={pill.key} className="catalog-promo-pill">
                <img
                  className="catalog-promo-pill-logo"
                  src={pill.logo}
                  alt=""
                  width="18"
                  height="18"
                  aria-hidden="true"
                />
                {pill.label}
              </span>
            ))}
          </div>
          <p className="catalog-promo-footer">{copy.footer}</p>
        </div>
        <div className="catalog-promo-actions">
          <a className="btn" href={catalogAssistantHref()}>
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
      return shouldShowCatalogPromo(window.sessionStorage)
    } catch {
      return true
    }
  })

  // Record after open so StrictMode's double initializer cannot hide the dialog,
  // while a later reload in the same visit still stays dismissed.
  useEffect(() => {
    if (!promoOpen) return
    try {
      dismissCatalogPromo(window.sessionStorage)
    } catch {
      /* ignore */
    }
  }, [promoOpen])

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

  function openPromoFromHover() {
    setPromoOpen((open) => (open ? open : true))
  }

  return (
    <Layout
      brand={t.brand}
      lang={lang}
      onLang={(next) => setLang(localeOf(next))}
      onCatalogHover={openPromoFromHover}
    >
      <ErrorBoundary>
        {isCatalogAssistant ? <CatalogWizard lang={lang} /> : <Wizard lang={lang} />}
      </ErrorBoundary>
      {promoOpen ? (
        <CatalogPromoDialog lang={lang} onClose={closePromo} />
      ) : null}
    </Layout>
  )
}
