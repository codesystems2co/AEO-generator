import './Layout.css'

export default function Layout({ children }) {
  return (
    <div className="layout">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <img src="/arkiphere-logo.png" alt="Arkiphere" className="logo-mark" />
            <span className="logo-text">Search Engine Optimizator</span>
          </div>
        </div>
      </header>
      <main className="app-content">
        {children}
      </main>
    </div>
  )
}
