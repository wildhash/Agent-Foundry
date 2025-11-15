"""
Database models for Agent Foundry
SQLAlchemy models for tracking pipelines, agents, and evolution
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Pipeline(Base):
    """
    Agent pipeline execution tracking
    Stores information about complete pipeline runs
    """
    __tablename__ = "pipelines"
    
    id = Column(String(100), primary_key=True, default=lambda: f"pipeline_{uuid.uuid4().hex[:8]}")
    task_description = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="initialized")  # initialized, running, completed, failed
    overall_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    
    # Relationships
    agent_executions = relationship("AgentExecution", back_populates="pipeline", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Pipeline(id={self.id}, status={self.status}, score={self.overall_score})>"


class AgentExecution(Base):
    """
    Individual agent execution tracking
    Stores results from each agent in the pipeline with reflexion data
    """
    __tablename__ = "agent_executions"
    
    id = Column(String(100), primary_key=True, default=lambda: f"exec_{uuid.uuid4().hex[:8]}")
    pipeline_id = Column(String(100), ForeignKey("pipelines.id"), nullable=False)
    agent_id = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)  # architect, coder, executor, critic, deployer
    generation = Column(Integer, default=0, nullable=False)
    
    # Execution results
    result = Column(JSON, nullable=True)
    performance_score = Column(Float, nullable=True)
    loops_executed = Column(Integer, default=1, nullable=False)
    
    # Reflexion data
    reflexion_iterations = Column(Integer, default=0, nullable=False)
    improvement_delta = Column(Float, default=0.0, nullable=False)
    final_strategy = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    pipeline = relationship("Pipeline", back_populates="agent_executions")
    
    def __repr__(self):
        return f"<AgentExecution(id={self.id}, type={self.agent_type}, score={self.performance_score})>"


class EvolutionNode(Base):
    """
    Evolution tree node tracking
    Tracks agent lineage and performance improvements across generations
    """
    __tablename__ = "evolution_nodes"
    
    id = Column(String(100), primary_key=True)
    parent_id = Column(String(100), ForeignKey("evolution_nodes.id"), nullable=True)
    agent_type = Column(String(50), nullable=False)
    generation = Column(Integer, default=0, nullable=False)
    
    # Performance metrics
    performance_score = Column(Float, nullable=False)
    improvement_rate = Column(Float, default=0.0, nullable=False)
    
    # Evolution metadata
    spawned = Column(Boolean, default=False, nullable=False)
    spawn_reason = Column(String(200), nullable=True)
    mutations = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    extra_data = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    
    def __repr__(self):
        return f"<EvolutionNode(id={self.id}, gen={self.generation}, score={self.performance_score})>"


# Define relationship outside of class to avoid variable scoping issues
EvolutionNode.children = relationship(
    "EvolutionNode",
    foreign_keys=[EvolutionNode.parent_id],
    backref="parent",
    remote_side=[EvolutionNode.id]
)


class HealingAction(Base):
    """
    Infrastructure self-healing log
    Tracks code healing actions performed by LiquidMetal or fallback systems
    """
    __tablename__ = "healing_actions"
    
    id = Column(String(100), primary_key=True, default=lambda: f"heal_{uuid.uuid4().hex[:8]}")
    agent_execution_id = Column(String(100), ForeignKey("agent_executions.id"), nullable=True)
    
    # Healing details
    issue_type = Column(String(100), nullable=False)
    issue_description = Column(Text, nullable=False)
    healing_strategy = Column(String(100), nullable=False)
    success = Column(Boolean, default=False, nullable=False)
    
    # Code details
    original_code_hash = Column(String(64), nullable=True)
    healed_code_hash = Column(String(64), nullable=True)
    changes_made = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    healing_time_ms = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<HealingAction(id={self.id}, type={self.issue_type}, success={self.success})>"
