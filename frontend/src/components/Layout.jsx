import './Layout.css'

export default function Layout({ brand, lang, onLang, children }) {
  return (
    <div className="layout">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <img src="/arkiphere-logo.png" alt="Arkiphere" className="logo-mark" />
            <span className="logo-text">{brand}</span>
          </div>
          <div className="header-actions lang-switch" role="group" aria-label="Language">
            <button
              type="button"
              className={lang === 'es' ? 'lang-btn is-active' : 'lang-btn'}
              onClick={() => onLang?.('es')}
            >
              ES
            </button>
            <button
              type="button"
              className={lang === 'en' ? 'lang-btn is-active' : 'lang-btn'}
              onClick={() => onLang?.('en')}
            >
              EN
            </button>
          </div>
        </div>
      </header>
      <main className="app-content">
        {children}
      </main>
    </div>
  )
}
