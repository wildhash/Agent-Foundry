'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import styles from './Dashboard.module.css'

interface SystemMetrics {
  total_agents: number
  active_pipelines: number
  completed_pipelines: number
  evolution_tree: {
    total_nodes: number
    total_generations: number
    average_performance: number
    best_performance: number
  }
}

interface PerformanceMetrics {
  average_score: number
  best_score: number
  worst_score: number
  total_executions: number
  agents_tracked: number
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchMetrics = async () => {
    try {
      const [metricsRes, perfRes] = await Promise.all([
        axios.get('/api/metrics/system'),
        axios.get('/api/metrics/performance')
      ])
      setMetrics(metricsRes.data)
      setPerformance(perfRes.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching metrics:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className={styles.loading}>Loading dashboard...</div>
  }

  return (
    <div className={styles.dashboard}>
      <h2>System Overview</h2>
      
      <div className={styles.grid}>
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <span className={styles.icon}>🤖</span>
            <h3>Active Agents</h3>
          </div>
          <div className={styles.cardValue}>{metrics?.total_agents || 0}</div>
          <p className={styles.cardLabel}>Total agents spawned</p>
        </div>

        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <span className={styles.icon}>⚡</span>
            <h3>Active Pipelines</h3>
          </div>
          <div className={styles.cardValue}>{metrics?.active_pipelines || 0}</div>
          <p className={styles.cardLabel}>Currently running</p>
        </div>

        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <span className={styles.icon}>✅</span>
            <h3>Completed</h3>
          </div>
          <div className={styles.cardValue}>{metrics?.completed_pipelines || 0}</div>
          <p className={styles.cardLabel}>Successfully completed</p>
        </div>

        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <span className={styles.icon}>🌳</span>
            <h3>Generations</h3>
          </div>
          <div className={styles.cardValue}>{metrics?.evolution_tree.total_generations || 0}</div>
          <p className={styles.cardLabel}>Evolution generations</p>
        </div>
      </div>

      <h2>Performance Metrics</h2>
      
      <div className={styles.grid}>
        <div className={styles.card}>
          <h3>Average Performance</h3>
          <div className={styles.performanceBar}>
            <div 
              className={styles.performanceFill}
              style={{ width: `${(performance?.average_score || 0) * 100}%` }}
            />
          </div>
          <div className={styles.cardValue}>
            {((performance?.average_score || 0) * 100).toFixed(1)}%
          </div>
        </div>

        <div className={styles.card}>
          <h3>Best Performance</h3>
          <div className={styles.performanceBar}>
            <div 
              className={styles.performanceFill}
              style={{ width: `${(performance?.best_score || 0) * 100}%` }}
            />
          </div>
          <div className={styles.cardValue}>
            {((performance?.best_score || 0) * 100).toFixed(1)}%
          </div>
        </div>

        <div className={styles.card}>
          <h3>Total Executions</h3>
          <div className={styles.cardValue}>{performance?.total_executions || 0}</div>
          <p className={styles.cardLabel}>{performance?.agents_tracked || 0} agents tracked</p>
        </div>
      </div>

      <div className={styles.features}>
        <h2>Integrated Technologies</h2>
        <div className={styles.featureGrid}>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>⚡</span>
            <h4>Fastino TLMs</h4>
            <p>99x faster inference</p>
          </div>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>🔧</span>
            <h4>LiquidMetal Raindrop</h4>
            <p>Self-healing code</p>
          </div>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>🎨</span>
            <h4>Freepik API</h4>
            <p>AI-generated visuals</p>
          </div>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>🔐</span>
            <h4>Frontegg</h4>
            <p>Multi-tenant auth</p>
          </div>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>🚀</span>
            <h4>Airia</h4>
            <p>Enterprise deployment</p>
          </div>
          <div className={styles.feature}>
            <span className={styles.featureIcon}>🔥</span>
            <h4>Campfire</h4>
            <p>Agent orchestration</p>
          </div>
        </div>
      </div>
    </div>
  )
}
