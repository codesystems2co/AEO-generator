import './Layout.css'

export default function Layout({ tabs, activeTab, onTabChange, children }) {
  return (
    <div className="layout">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">◇</span>
            <span>AEO / SEO Generator</span>
          </div>
          <nav className="tabs">
            {tabs.map(({ id, label, icon }) => (
              <button
                key={id}
                type="button"
                className={`tab ${activeTab === id ? 'active' : ''}`}
                onClick={() => onTabChange(id)}
              >
                <span className="tab-icon">{icon}</span>
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>
      <main className="app-content">
        {children}
      </main>
    </div>
  )
}
