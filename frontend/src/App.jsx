import { useState } from 'react'
import Layout from './components/Layout'
import MetaTags from './tabs/MetaTags'
import Keywords from './tabs/Keywords'
import ContentAnalysis from './tabs/ContentAnalysis'
import AEO from './tabs/AEO'
import SEOScore from './tabs/SEOScore'
import NLP from './tabs/NLP'
import URLAnalyzer from './tabs/URLAnalyzer'
import ExternalSEO from './tabs/ExternalSEO'
import Geo from './tabs/Geo'
import Guide from './tabs/Guide'
import './App.css'

const TABS = [
  { id: 'guide', label: 'Guide', icon: '📖' },
  { id: 'meta', label: 'Meta Tags', icon: '◇' },
  { id: 'keywords', label: 'Keywords', icon: '◆' },
  { id: 'analysis', label: 'Content Analysis', icon: '▣' },
  { id: 'aeo', label: 'AEO Suggest', icon: '◈' },
  { id: 'score', label: 'SEO Score', icon: '★' },
  { id: 'nlp', label: 'NLP', icon: '◉' },
  { id: 'url', label: 'URL Analyze', icon: '🔗' },
  { id: 'external', label: 'External SEO', icon: '⊕' },
  { id: 'geo', label: 'GEO', icon: '🤖' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('guide')

  return (
    <Layout
      tabs={TABS}
      activeTab={activeTab}
      onTabChange={setActiveTab}
    >
      {activeTab === 'guide' && <Guide />}
      {activeTab === 'meta' && <MetaTags />}
      {activeTab === 'keywords' && <Keywords />}
      {activeTab === 'analysis' && <ContentAnalysis />}
      {activeTab === 'aeo' && <AEO />}
      {activeTab === 'score' && <SEOScore />}
      {activeTab === 'nlp' && <NLP />}
      {activeTab === 'url' && <URLAnalyzer />}
      {activeTab === 'external' && <ExternalSEO />}
      {activeTab === 'geo' && <Geo />}
    </Layout>
  )
}
