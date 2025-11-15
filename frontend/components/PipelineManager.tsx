'use client'

import { useState } from 'react'
import axios from 'axios'
import styles from './PipelineManager.module.css'

interface Pipeline {
  pipeline_id: string
  status: string
  created_at: string
  task: string
  overall_score?: number
}

export default function PipelineManager() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [taskDescription, setTaskDescription] = useState('')
  const [requirements, setRequirements] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedPipeline, setSelectedPipeline] = useState<any>(null)

  const createPipeline = async () => {
    if (!taskDescription.trim()) {
      alert('Please enter a task description')
      return
    }

    setLoading(true)
    try {
      const response = await axios.post('/api/agents/pipeline', {
        description: taskDescription,
        requirements: requirements.split('\n').filter(r => r.trim()),
        language: 'python'
      })

      alert(`Pipeline created: ${response.data.pipeline_id}`)
      setTaskDescription('')
      setRequirements('')
      fetchPipelines()
    } catch (error) {
      console.error('Error creating pipeline:', error)
      alert('Failed to create pipeline')
    }
    setLoading(false)
  }

  const executePipeline = async (pipelineId: string) => {
    setLoading(true)
    try {
      const response = await axios.post(`/api/agents/pipeline/${pipelineId}/execute`)
      alert(`Pipeline executed. Score: ${response.data.overall_score?.toFixed(2)}`)
      fetchPipelines()
      setSelectedPipeline(response.data)
    } catch (error) {
      console.error('Error executing pipeline:', error)
      alert('Failed to execute pipeline')
    }
    setLoading(false)
  }

  const fetchPipelines = async () => {
    try {
      const response = await axios.get('/api/agents/pipelines')
      setPipelines(response.data.pipelines)
    } catch (error) {
      console.error('Error fetching pipelines:', error)
    }
  }

  return (
    <div className={styles.container}>
      <h2>Pipeline Manager</h2>
      <p className={styles.subtitle}>
        Create and manage agent pipelines: Architect → Coder → Executor → Critic → Deployer
      </p>

      <div className={styles.createSection}>
        <h3>Create New Pipeline</h3>
        <div className={styles.form}>
          <div className={styles.formGroup}>
            <label>Task Description</label>
            <textarea
              value={taskDescription}
              onChange={(e) => setTaskDescription(e.target.value)}
              placeholder="Describe what you want the agents to build..."
              rows={4}
              className={styles.textarea}
            />
          </div>

          <div className={styles.formGroup}>
            <label>Requirements (one per line)</label>
            <textarea
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder="List requirements, one per line..."
              rows={4}
              className={styles.textarea}
            />
          </div>

          <button
            onClick={createPipeline}
            disabled={loading}
            className={styles.btnPrimary}
          >
            {loading ? 'Creating...' : '🚀 Create Pipeline'}
          </button>
        </div>
      </div>

      <div className={styles.pipelinesSection}>
        <div className={styles.sectionHeader}>
          <h3>Active Pipelines</h3>
          <button onClick={fetchPipelines} className={styles.btnSecondary}>
            🔄 Refresh
          </button>
        </div>

        {pipelines.length === 0 ? (
          <div className={styles.empty}>
            No pipelines yet. Create one to get started!
          </div>
        ) : (
          <div className={styles.pipelineGrid}>
            {pipelines.map((pipeline) => (
              <div key={pipeline.pipeline_id} className={styles.pipelineCard}>
                <div className={styles.pipelineHeader}>
                  <h4>{pipeline.pipeline_id}</h4>
                  <span className={`${styles.badge} ${styles['badge-' + pipeline.status]}`}>
                    {pipeline.status}
                  </span>
                </div>
                
                <p className={styles.pipelineTask}>{pipeline.task}</p>
                
                {pipeline.overall_score !== undefined && (
                  <div className={styles.scoreBar}>
                    <div 
                      className={styles.scoreFill}
                      style={{ width: `${pipeline.overall_score * 100}%` }}
                    />
                    <span className={styles.scoreLabel}>
                      {(pipeline.overall_score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
                
                <div className={styles.pipelineActions}>
                  {pipeline.status === 'created' && (
                    <button
                      onClick={() => executePipeline(pipeline.pipeline_id)}
                      className={styles.btnExecute}
                      disabled={loading}
                    >
                      ▶️ Execute
                    </button>
                  )}
                  <button
                    onClick={() => setSelectedPipeline(pipeline)}
                    className={styles.btnDetails}
                  >
                    📊 Details
                  </button>
                </div>
                
                <p className={styles.pipelineDate}>
                  Created: {new Date(pipeline.created_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedPipeline && (
        <div className={styles.modal} onClick={() => setSelectedPipeline(null)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <h3>Pipeline Details</h3>
            <pre className={styles.jsonDisplay}>
              {JSON.stringify(selectedPipeline, null, 2)}
            </pre>
            <button onClick={() => setSelectedPipeline(null)} className={styles.btnClose}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
