"""
Tests for database models and initialization
"""

import pytest
from datetime import datetime
from sqlalchemy import inspect
from models.database import Pipeline, AgentExecution, EvolutionNode, HealingAction, Base
from models.init_db import create_test_engine, get_test_db


@pytest.fixture
def test_engine():
    """Create test database engine"""
    return create_test_engine()


@pytest.fixture
def test_db(test_engine):
    """Create test database session"""
    session_gen = get_test_db(test_engine)
    session = next(session_gen)
    yield session
    session.close()


def test_database_tables_created(test_engine):
    """Test that all tables are created"""
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    
    assert "pipelines" in tables
    assert "agent_executions" in tables
    assert "evolution_nodes" in tables
    assert "healing_actions" in tables


def test_pipeline_creation(test_db):
    """Test creating a pipeline record"""
    pipeline = Pipeline(
        task_description="Test task",
        status="initialized"
    )
    test_db.add(pipeline)
    test_db.commit()
    
    assert pipeline.id is not None
    assert pipeline.id.startswith("pipeline_")
    assert pipeline.status == "initialized"
    assert pipeline.created_at is not None
    assert isinstance(pipeline.created_at, datetime)


def test_pipeline_with_agent_executions(test_db):
    """Test pipeline with related agent executions"""
    # Create pipeline
    pipeline = Pipeline(
        task_description="Build API",
        status="running"
    )
    test_db.add(pipeline)
    test_db.flush()
    
    # Create agent executions
    architect = AgentExecution(
        pipeline_id=pipeline.id,
        agent_id="arch_001",
        agent_type="architect",
        performance_score=0.85,
        loops_executed=3
    )
    coder = AgentExecution(
        pipeline_id=pipeline.id,
        agent_id="coder_001",
        agent_type="coder",
        performance_score=0.78,
        loops_executed=2
    )
    
    test_db.add_all([architect, coder])
    test_db.commit()
    
    # Verify relationships
    retrieved_pipeline = test_db.query(Pipeline).filter_by(id=pipeline.id).first()
    assert len(retrieved_pipeline.agent_executions) == 2
    assert retrieved_pipeline.agent_executions[0].agent_type in ["architect", "coder"]


def test_agent_execution_reflexion_tracking(test_db):
    """Test agent execution reflexion data"""
    pipeline = Pipeline(task_description="Test")
    test_db.add(pipeline)
    test_db.flush()
    
    execution = AgentExecution(
        pipeline_id=pipeline.id,
        agent_id="agent_001",
        agent_type="architect",
        performance_score=0.90,
        reflexion_iterations=3,
        improvement_delta=0.15,
        final_strategy="simplified_design"
    )
    test_db.add(execution)
    test_db.commit()
    
    retrieved = test_db.query(AgentExecution).filter_by(id=execution.id).first()
    assert retrieved.reflexion_iterations == 3
    assert retrieved.improvement_delta == 0.15
    assert retrieved.final_strategy == "simplified_design"


def test_evolution_node_creation_and_queries(test_db):
    """Test evolution node creation and parent-child linkage"""
    # Create parent node
    parent = EvolutionNode(
        id="agent_gen0",
        agent_type="architect",
        generation=0,
        performance_score=0.75
    )
    test_db.add(parent)
    test_db.flush()
    
    # Create child nodes
    child1 = EvolutionNode(
        id="agent_gen1_a",
        parent_id=parent.id,
        agent_type="architect",
        generation=1,
        performance_score=0.82,
        improvement_rate=0.093
    )
    child2 = EvolutionNode(
        id="agent_gen1_b",
        parent_id=parent.id,
        agent_type="architect",
        generation=1,
        performance_score=0.88,
        improvement_rate=0.173
    )
    test_db.add_all([child1, child2])
    test_db.commit()
    
    # Verify records exist and parent_id is set correctly
    retrieved_child = test_db.query(EvolutionNode).filter_by(id=child1.id).first()
    assert retrieved_child.parent_id == parent.id
    
    # Verify we can query by parent_id
    children = test_db.query(EvolutionNode).filter_by(parent_id=parent.id).all()
    assert len(children) == 2


def test_evolution_node_spawning(test_db):
    """Test evolution node spawning tracking"""
    node = EvolutionNode(
        id="agent_spawned",
        agent_type="coder",
        generation=2,
        performance_score=0.90,
        spawned=True,
        spawn_reason="exceeded_evolution_threshold",
        mutations={"strategy": "optimized", "complexity": "reduced"}
    )
    test_db.add(node)
    test_db.commit()
    
    retrieved = test_db.query(EvolutionNode).filter_by(spawned=True).first()
    assert retrieved is not None
    assert retrieved.spawn_reason == "exceeded_evolution_threshold"
    assert "strategy" in retrieved.mutations


def test_healing_action_tracking(test_db):
    """Test healing action logging"""
    # Create pipeline and execution
    pipeline = Pipeline(task_description="Test")
    test_db.add(pipeline)
    test_db.flush()
    
    execution = AgentExecution(
        pipeline_id=pipeline.id,
        agent_id="coder_001",
        agent_type="coder"
    )
    test_db.add(execution)
    test_db.flush()
    
    # Create healing action
    healing = HealingAction(
        agent_execution_id=execution.id,
        issue_type="missing_import",
        issue_description="Missing typing imports",
        healing_strategy="add_imports",
        success=True,
        changes_made={"added": ["from typing import Dict, Any"]},
        healing_time_ms=120
    )
    test_db.add(healing)
    test_db.commit()
    
    retrieved = test_db.query(HealingAction).filter_by(id=healing.id).first()
    assert retrieved.success is True
    assert retrieved.issue_type == "missing_import"
    assert "added" in retrieved.changes_made


def test_pipeline_cascade_delete(test_db):
    """Test that deleting pipeline cascades to agent executions"""
    # Create pipeline with executions
    pipeline = Pipeline(task_description="Test cascade")
    test_db.add(pipeline)
    test_db.flush()
    
    execution = AgentExecution(
        pipeline_id=pipeline.id,
        agent_id="test_agent",
        agent_type="architect"
    )
    test_db.add(execution)
    test_db.commit()
    
    pipeline_id = pipeline.id
    execution_id = execution.id
    
    # Delete pipeline
    test_db.delete(pipeline)
    test_db.commit()
    
    # Verify cascade
    assert test_db.query(Pipeline).filter_by(id=pipeline_id).first() is None
    assert test_db.query(AgentExecution).filter_by(id=execution_id).first() is None


def test_pipeline_status_enum(test_db):
    """Test pipeline status values"""
    valid_statuses = ["initialized", "running", "completed", "failed"]
    
    for status in valid_statuses:
        pipeline = Pipeline(
            task_description=f"Test {status}",
            status=status
        )
        test_db.add(pipeline)
    
    test_db.commit()
    
    pipelines = test_db.query(Pipeline).all()
    assert len(pipelines) >= len(valid_statuses)


def test_query_performance_filtering(test_db):
    """Test querying by performance score"""
    # Create pipelines with different scores
    high_score = Pipeline(
        task_description="High performer",
        status="completed",
        overall_score=0.95
    )
    low_score = Pipeline(
        task_description="Low performer",
        status="completed",
        overall_score=0.65
    )
    test_db.add_all([high_score, low_score])
    test_db.commit()
    
    # Query high performers
    high_performers = test_db.query(Pipeline).filter(
        Pipeline.overall_score >= 0.85
    ).all()
    
    assert len(high_performers) >= 1
    assert all(p.overall_score >= 0.85 for p in high_performers)
