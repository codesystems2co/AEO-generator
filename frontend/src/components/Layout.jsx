import './Layout.css'

const UI = {
  es: {
    catalog: 'Catálogo',
    catalogAria:
      'Abrir análisis e inyección de catálogo para cada ficha de producto',
    esLabel: 'Español',
    enLabel: 'English',
  },
  en: {
    catalog: 'Catalog',
    catalogAria:
      'Open catalog analysis and injection for every product record',
    esLabel: 'Español',
    enLabel: 'English',
  },
}

function catalogAssistantHref() {
  try {
    const params = new URLSearchParams(window.location.search)
    params.set('assistant', 'catalog')
    const qs = params.toString()
    return `${window.location.pathname}?${qs}${window.location.hash || ''}`
  } catch {
    return '?assistant=catalog'
  }
}

export default function Layout({ brand, lang, onLang, onCatalogHover, children }) {
  const ui = UI[lang === 'en' ? 'en' : 'es']

  return (
    <div className="layout">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <img src="/arkiphere-logo.png" alt="Arkiphere" className="logo-mark" />
            <span className="logo-text">{brand}</span>
          </div>
          <div className="header-actions" role="group" aria-label="Language">
            <a
              className="catalog-nav-link"
              href={catalogAssistantHref()}
              aria-label={ui.catalogAria}
              onMouseEnter={() => onCatalogHover?.()}
            >
              {ui.catalog}
            </a>
            <div className="lang-switch" role="group" aria-label="Language">
              <button
                type="button"
                className={lang === 'es' ? 'lang-btn is-active' : 'lang-btn'}
                onClick={() => onLang?.('es')}
                aria-label={ui.esLabel}
                title={ui.esLabel}
              >
                <span className="lang-flag" aria-hidden="true">🇪🇸</span>
              </button>
              <button
                type="button"
                className={lang === 'en' ? 'lang-btn is-active' : 'lang-btn'}
                onClick={() => onLang?.('en')}
                aria-label={ui.enLabel}
                title={ui.enLabel}
              >
                <span className="lang-flag" aria-hidden="true">🇬🇧</span>
              </button>
            </div>
          </div>
        </div>
      </header>
      <main className="app-content">
        {children}
      </main>
    </div>
  )
}
