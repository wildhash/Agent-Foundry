'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import styles from './MetricsPanel.module.css'

export default function MetricsPanel() {
  const [integrationMetrics, setIntegrationMetrics] = useState<any>(null)
  const [reflexionMetrics, setReflexionMetrics] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchMetrics = async () => {
    try {
      const [intRes, refRes] = await Promise.all([
        axios.get('/api/metrics/integrations'),
        axios.get('/api/metrics/reflexion')
      ])
      
      setIntegrationMetrics(intRes.data)
      setReflexionMetrics(refRes.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching metrics:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className={styles.loading}>Loading metrics...</div>
  }

  return (
    <div className={styles.container}>
      <h2>System Metrics</h2>
      <p className={styles.subtitle}>
        Monitor integrations, reflexion loops, and system health
      </p>

      <div className={styles.section}>
        <h3>⚡ Fastino TLM (99x Faster Inference)</h3>
        <div className={styles.metricsGrid}>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Cache Size</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.fastino_tlm?.cache_size || 0}
            </div>
          </div>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Speed Multiplier</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.fastino_tlm?.speed_multiplier || 0}x
            </div>
          </div>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Batch Size</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.fastino_tlm?.batch_size || 0}
            </div>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3>🔧 LiquidMetal Raindrop (Self-Healing)</h3>
        <div className={styles.metricsGrid}>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Healing Sessions</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.liquidmetal_raindrop?.total_sessions || 0}
            </div>
          </div>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Issues Fixed</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.liquidmetal_raindrop?.total_issues_fixed || 0}
            </div>
          </div>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Avg Issues/Session</div>
            <div className={styles.metricValue}>
              {(integrationMetrics?.liquidmetal_raindrop?.average_issues_per_session || 0).toFixed(1)}
            </div>
          </div>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Auto-Heal</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.liquidmetal_raindrop?.auto_heal_enabled ? '✅' : '❌'}
            </div>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3>🎨 Freepik API (AI Visuals)</h3>
        <div className={styles.metricsGrid}>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Cache Size</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.freepik_api?.cache_size || 0}
            </div>
          </div>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>API Status</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.freepik_api?.api_key_configured ? '✅' : '⚠️'}
            </div>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3>🔐 Frontegg (Multi-tenant Auth)</h3>
        <div className={styles.metricsGrid}>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Active Sessions</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.frontegg_auth?.active_sessions || 0}
            </div>
          </div>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>API Status</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.frontegg_auth?.api_key_configured ? '✅' : '⚠️'}
            </div>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3>🚀 Airia (Enterprise Deployment)</h3>
        <div className={styles.metricsGrid}>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Total Deployments</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.airia_deployment?.total_deployments || 0}
            </div>
          </div>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Active Deployments</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.airia_deployment?.active_deployments || 0}
            </div>
          </div>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>API Status</div>
            <div className={styles.metricValue}>
              {integrationMetrics?.airia_deployment?.api_key_configured ? '✅' : '⚠️'}
            </div>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3>🔄 Reflexion Loops (Self-Improvement)</h3>
        <div className={styles.metricsGrid}>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Total Loops</div>
            <div className={styles.metricValue}>
              {reflexionMetrics?.total_reflexion_loops || 0}
            </div>
          </div>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Improvements Made</div>
            <div className={styles.metricValue}>
              {reflexionMetrics?.total_improvements || 0}
            </div>
          </div>
          <div className={styles.metric}>
            <div className={styles.metricLabel}>Pipelines with Reflexion</div>
            <div className={styles.metricValue}>
              {reflexionMetrics?.pipelines_with_reflexion || 0}
            </div>
          </div>
        </div>
      </div>

      <div className={styles.refreshSection}>
        <button onClick={fetchMetrics} className={styles.btnRefresh}>
          🔄 Refresh Metrics
        </button>
      </div>
    </div>
  )
}
