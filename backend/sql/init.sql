-- Agent Foundry Database Initialization Script
-- PostgreSQL initialization with UUID support and performance indexes

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types for better type safety
DO $$ BEGIN
    CREATE TYPE pipeline_status AS ENUM ('initialized', 'running', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE agent_type AS ENUM ('architect', 'coder', 'executor', 'critic', 'deployer');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Performance indexes will be created after tables are created by SQLAlchemy
-- These are additional optimizations

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Note: Tables are created by SQLAlchemy, but we add additional indexes here

-- Add indexes after tables exist (run this after initial table creation)
DO $$ 
BEGIN
    -- Pipeline indexes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pipelines') THEN
        CREATE INDEX IF NOT EXISTS idx_pipelines_status ON pipelines(status);
        CREATE INDEX IF NOT EXISTS idx_pipelines_created_at ON pipelines(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_pipelines_score ON pipelines(overall_score DESC) WHERE overall_score IS NOT NULL;
        
        -- Add trigger for updated_at
        DROP TRIGGER IF EXISTS update_pipelines_updated_at ON pipelines;
        CREATE TRIGGER update_pipelines_updated_at 
            BEFORE UPDATE ON pipelines 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- AgentExecution indexes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'agent_executions') THEN
        CREATE INDEX IF NOT EXISTS idx_agent_executions_pipeline ON agent_executions(pipeline_id);
        CREATE INDEX IF NOT EXISTS idx_agent_executions_type ON agent_executions(agent_type);
        CREATE INDEX IF NOT EXISTS idx_agent_executions_score ON agent_executions(performance_score DESC) WHERE performance_score IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_agent_executions_generation ON agent_executions(generation);
    END IF;
    
    -- EvolutionNode indexes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'evolution_nodes') THEN
        CREATE INDEX IF NOT EXISTS idx_evolution_nodes_parent ON evolution_nodes(parent_id) WHERE parent_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_evolution_nodes_generation ON evolution_nodes(generation);
        CREATE INDEX IF NOT EXISTS idx_evolution_nodes_score ON evolution_nodes(performance_score DESC);
        CREATE INDEX IF NOT EXISTS idx_evolution_nodes_spawned ON evolution_nodes(spawned) WHERE spawned = true;
    END IF;
    
    -- HealingAction indexes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'healing_actions') THEN
        CREATE INDEX IF NOT EXISTS idx_healing_actions_execution ON healing_actions(agent_execution_id) WHERE agent_execution_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_healing_actions_type ON healing_actions(issue_type);
        CREATE INDEX IF NOT EXISTS idx_healing_actions_success ON healing_actions(success);
        CREATE INDEX IF NOT EXISTS idx_healing_actions_created_at ON healing_actions(created_at DESC);
    END IF;
END $$;

-- Create view for pipeline statistics
CREATE OR REPLACE VIEW pipeline_stats AS
SELECT 
    p.id,
    p.status,
    p.overall_score,
    COUNT(ae.id) as total_agents,
    AVG(ae.performance_score) as avg_agent_score,
    SUM(ae.reflexion_iterations) as total_reflexion_iterations,
    p.created_at,
    p.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(p.completed_at, NOW()) - p.created_at)) as duration_seconds
FROM pipelines p
LEFT JOIN agent_executions ae ON p.id = ae.pipeline_id
GROUP BY p.id, p.status, p.overall_score, p.created_at, p.completed_at;

-- Create view for evolution statistics
CREATE OR REPLACE VIEW evolution_stats AS
SELECT 
    en.agent_type,
    en.generation,
    COUNT(*) as node_count,
    AVG(en.performance_score) as avg_score,
    MAX(en.performance_score) as max_score,
    MIN(en.performance_score) as min_score,
    COUNT(CASE WHEN en.spawned THEN 1 END) as spawned_count
FROM evolution_nodes en
GROUP BY en.agent_type, en.generation
ORDER BY en.agent_type, en.generation;

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agent;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agent;
