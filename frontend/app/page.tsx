'use client'

import { useEffect, useState } from 'react'
import styles from './page.module.css'
import Dashboard from '@/components/Dashboard'
import PipelineManager from '@/components/PipelineManager'
import EvolutionTree from '@/components/EvolutionTree'
import MetricsPanel from '@/components/MetricsPanel'

export default function Home() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1>🔮 Agent Foundry</h1>
          <p className={styles.subtitle}>The last agent you'll ever need to build</p>
        </div>
        <nav className={styles.nav}>
          <button
            className={activeTab === 'dashboard' ? styles.navActive : ''}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={activeTab === 'pipeline' ? styles.navActive : ''}
            onClick={() => setActiveTab('pipeline')}
          >
            Pipelines
          </button>
          <button
            className={activeTab === 'evolution' ? styles.navActive : ''}
            onClick={() => setActiveTab('evolution')}
          >
            Evolution Tree
          </button>
          <button
            className={activeTab === 'metrics' ? styles.navActive : ''}
            onClick={() => setActiveTab('metrics')}
          >
            Metrics
          </button>
        </nav>
      </header>

      <div className={styles.content}>
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'pipeline' && <PipelineManager />}
        {activeTab === 'evolution' && <EvolutionTree />}
        {activeTab === 'metrics' && <MetricsPanel />}
      </div>

      <footer className={styles.footer}>
        <p>
          Powered by Fastino TLMs (99x faster) • LiquidMetal Raindrop • 
          Freepik AI • Frontegg • Airia
        </p>
      </footer>
    </main>
  )
}
