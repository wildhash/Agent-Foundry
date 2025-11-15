'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import styles from './EvolutionTree.module.css'

interface TreeNode {
  id: string
  generation: number
  performance_score: number
  metadata: any
  created_at: string
}

interface TreeEdge {
  parent: string
  child: string
}

interface TreeData {
  nodes: TreeNode[]
  edges: TreeEdge[]
  total_generations: number
  total_nodes: number
}

export default function EvolutionTree() {
  const [treeData, setTreeData] = useState<TreeData | null>(null)
  const [bestPerformers, setBestPerformers] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTreeData()
  }, [])

  const fetchTreeData = async () => {
    try {
      const [treeRes, performersRes, statsRes] = await Promise.all([
        axios.get('/api/evolution/tree'),
        axios.get('/api/evolution/best-performers?top_n=5'),
        axios.get('/api/evolution/tree/stats')
      ])
      
      setTreeData(treeRes.data)
      setBestPerformers(performersRes.data.top_performers)
      setStats(statsRes.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching tree data:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className={styles.loading}>Loading evolution tree...</div>
  }

  return (
    <div className={styles.container}>
      <h2>Evolution Tree</h2>
      <p className={styles.subtitle}>
        Track agent lineage and performance across generations
      </p>

      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statValue}>{stats?.total_nodes || 0}</div>
          <div className={styles.statLabel}>Total Nodes</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statValue}>{stats?.total_generations || 0}</div>
          <div className={styles.statLabel}>Generations</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statValue}>
            {((stats?.average_performance || 0) * 100).toFixed(1)}%
          </div>
          <div className={styles.statLabel}>Avg Performance</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statValue}>
            {((stats?.best_performance || 0) * 100).toFixed(1)}%
          </div>
          <div className={styles.statLabel}>Best Performance</div>
        </div>
      </div>

      <div className={styles.section}>
        <h3>🏆 Top Performers</h3>
        {bestPerformers.length === 0 ? (
          <div className={styles.empty}>No performers yet</div>
        ) : (
          <div className={styles.performersList}>
            {bestPerformers.map((performer, index) => (
              <div key={performer.node_id} className={styles.performerCard}>
                <div className={styles.performerRank}>#{index + 1}</div>
                <div className={styles.performerInfo}>
                  <h4>{performer.node_id}</h4>
                  <p>Generation {performer.generation}</p>
                </div>
                <div className={styles.performerScore}>
                  <div className={styles.scoreCircle}>
                    {(performer.performance_score * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className={styles.section}>
        <h3>🌳 Tree Visualization</h3>
        {treeData && treeData.nodes.length > 0 ? (
          <div className={styles.treeViz}>
            <svg width="100%" height="400" className={styles.svg}>
              {/* Simple tree visualization */}
              {treeData.nodes.map((node, index) => {
                const x = 50 + (index % 10) * 100
                const y = 50 + node.generation * 80
                const color = node.performance_score > 0.8 ? '#10b981' : 
                             node.performance_score > 0.6 ? '#6366f1' : '#f59e0b'
                
                return (
                  <g key={node.id}>
                    <circle
                      cx={x}
                      cy={y}
                      r={20}
                      fill={color}
                      stroke="#334155"
                      strokeWidth={2}
                    />
                    <text
                      x={x}
                      y={y + 5}
                      textAnchor="middle"
                      fill="white"
                      fontSize="12"
                    >
                      {(node.performance_score * 100).toFixed(0)}
                    </text>
                  </g>
                )
              })}
              
              {/* Draw edges */}
              {treeData.edges.map((edge, index) => {
                const parentNode = treeData.nodes.find(n => n.id === edge.parent)
                const childNode = treeData.nodes.find(n => n.id === edge.child)
                
                if (parentNode && childNode) {
                  const parentIndex = treeData.nodes.indexOf(parentNode)
                  const childIndex = treeData.nodes.indexOf(childNode)
                  
                  const x1 = 50 + (parentIndex % 10) * 100
                  const y1 = 50 + parentNode.generation * 80
                  const x2 = 50 + (childIndex % 10) * 100
                  const y2 = 50 + childNode.generation * 80
                  
                  return (
                    <line
                      key={index}
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke="#475569"
                      strokeWidth={2}
                    />
                  )
                }
                return null
              })}
            </svg>
            
            <div className={styles.legend}>
              <div className={styles.legendItem}>
                <span className={styles.legendDot} style={{background: '#10b981'}}></span>
                <span>Excellent (80%+)</span>
              </div>
              <div className={styles.legendItem}>
                <span className={styles.legendDot} style={{background: '#6366f1'}}></span>
                <span>Good (60-80%)</span>
              </div>
              <div className={styles.legendItem}>
                <span className={styles.legendDot} style={{background: '#f59e0b'}}></span>
                <span>Needs Improvement (&lt;60%)</span>
              </div>
            </div>
          </div>
        ) : (
          <div className={styles.empty}>
            No evolution tree data yet. Run some pipelines to see evolution!
          </div>
        )}
      </div>

      <div className={styles.refreshSection}>
        <button onClick={fetchTreeData} className={styles.btnRefresh}>
          🔄 Refresh Tree Data
        </button>
      </div>
    </div>
  )
}
