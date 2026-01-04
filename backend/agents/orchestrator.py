"""
Agent Orchestrator - Implements Campfire patterns for agent coordination
Manages the architect→coder→executor→critic→deployer pipeline
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime
import networkx as nx

from agents.specialized_agents import (
    ArchitectAgent,
    CoderAgent,
    ExecutorAgent,
    CriticAgent,
    DeployerAgent,
)
from models.evolution import EvolutionTree

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates agent pipeline using Campfire patterns
    Manages agent spawning, coordination, and evolution
    """

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.evolution_tree = EvolutionTree()
        self.active_pipelines: Dict[str, Dict[str, Any]] = {}
        self.pipeline_counter = 0

    async def create_pipeline(self, task: Dict[str, Any]) -> str:
        """Create a new agent pipeline for a task"""
        pipeline_id = f"pipeline_{self.pipeline_counter}"
        self.pipeline_counter += 1

        logger.info(f"Creating pipeline {pipeline_id} for task: {task.get('description', 'N/A')}")

        # Spawn agents for this pipeline
        agents = {
            "architect": ArchitectAgent(f"{pipeline_id}_architect"),
            "coder": CoderAgent(f"{pipeline_id}_coder"),
            "executor": ExecutorAgent(f"{pipeline_id}_executor"),
            "critic": CriticAgent(f"{pipeline_id}_critic"),
            "deployer": DeployerAgent(f"{pipeline_id}_deployer"),
        }

        # Register agents
        for agent_id, agent in agents.items():
            self.agents[agent.agent_id] = agent

        self.active_pipelines[pipeline_id] = {
            "agents": agents,
            "task": task,
            "status": "initialized",
            "created_at": datetime.now(),
            "results": {},
        }

        return pipeline_id

    async def execute_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Execute the full agent pipeline
        architect→coder→executor→critic→deployer
        """
        if pipeline_id not in self.active_pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        pipeline = self.active_pipelines[pipeline_id]
        agents = pipeline["agents"]
        task = pipeline["task"]

        logger.info(f"Executing pipeline {pipeline_id}")
        pipeline["status"] = "running"

        try:
            # Phase 1: Architecture design
            logger.info("Phase 1: Architecture")
            architect_result = await agents["architect"].reflexion_loop(task)
            pipeline["results"]["architect"] = architect_result

            # Phase 2: Code generation
            logger.info("Phase 2: Coding")
            coder_task = {**task, "architecture": architect_result["result"]}
            coder_result = await agents["coder"].reflexion_loop(coder_task)
            pipeline["results"]["coder"] = coder_result

            # Phase 3: Execution
            logger.info("Phase 3: Execution")
            executor_task = {**task, "code": coder_result["result"].get("code", "")}
            executor_result = await agents["executor"].reflexion_loop(executor_task)
            pipeline["results"]["executor"] = executor_result

            # Phase 4: Critique
            logger.info("Phase 4: Critique")
            critic_task = {
                **task,
                "architecture": architect_result["result"],
                "code": coder_result["result"].get("code", ""),
                "execution_result": executor_result["result"],
            }
            critic_result = await agents["critic"].reflexion_loop(critic_task)
            pipeline["results"]["critic"] = critic_result

            # Phase 5: Deployment (if critique passed)
            if critic_result["result"].get("passed", False):
                logger.info("Phase 5: Deployment")
                deployer_task = {**task, "code": coder_result["result"].get("code", "")}
                deployer_result = await agents["deployer"].reflexion_loop(deployer_task)
                pipeline["results"]["deployer"] = deployer_result
            else:
                logger.info("Critique failed, skipping deployment")
                pipeline["results"]["deployer"] = {
                    "result": {"deployed": False, "reason": "critique_failed"},
                    "score": 0.0,
                }

            # Calculate overall pipeline performance
            overall_score = self._calculate_pipeline_score(pipeline["results"])

            pipeline["status"] = "completed"
            pipeline["overall_score"] = overall_score

            # Update evolution tree
            self._update_evolution_tree(pipeline_id, pipeline)

            # Check if we should evolve agents
            if overall_score >= 0.85:
                await self._evolve_agents(pipeline_id, agents)

            return {
                "pipeline_id": pipeline_id,
                "status": "completed",
                "overall_score": overall_score,
                "results": pipeline["results"],
                "agents": {k: v.to_dict() for k, v in agents.items()},
            }

        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} failed: {str(e)}")
            pipeline["status"] = "failed"
            pipeline["error"] = str(e)
            return {"pipeline_id": pipeline_id, "status": "failed", "error": str(e)}

    def _calculate_pipeline_score(self, results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall pipeline performance score"""
        scores = []
        for stage, result in results.items():
            if "score" in result:
                scores.append(result["score"])

        return sum(scores) / len(scores) if scores else 0.0

    def _update_evolution_tree(self, pipeline_id: str, pipeline: Dict[str, Any]):
        """Update the evolution tree with pipeline results"""
        self.evolution_tree.add_node(
            node_id=pipeline_id,
            generation=0,
            performance_score=pipeline.get("overall_score", 0.0),
            metadata={
                "created_at": pipeline["created_at"].isoformat(),
                "task": pipeline["task"].get("description", "N/A"),
            },
        )

    async def _evolve_agents(self, pipeline_id: str, agents: Dict[str, Any]):
        """Evolve agents to next generation based on performance"""
        logger.info(f"Evolving agents from pipeline {pipeline_id}")

        for agent_type, agent in agents.items():
            # Spawn child agent with improved capabilities
            child_id = agent.spawn_child()
            logger.info(f"Spawned child agent: {child_id}")

            # Add to evolution tree
            self.evolution_tree.add_edge(agent.agent_id, child_id)

    async def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """Get status of a pipeline"""
        if pipeline_id not in self.active_pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        pipeline = self.active_pipelines[pipeline_id]
        return {
            "pipeline_id": pipeline_id,
            "status": pipeline["status"],
            "created_at": pipeline["created_at"].isoformat(),
            "agents": {agent_type: agent.to_dict() for agent_type, agent in pipeline["agents"].items()},
            "results": pipeline.get("results", {}),
        }

    async def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all pipelines"""
        return [
            {
                "pipeline_id": pid,
                "status": pipeline["status"],
                "created_at": pipeline["created_at"].isoformat(),
                "task": pipeline["task"].get("description", "N/A"),
                "overall_score": pipeline.get("overall_score"),
            }
            for pid, pipeline in self.active_pipelines.items()
        ]

    def get_evolution_tree(self) -> Dict[str, Any]:
        """Get the evolution tree structure"""
        return self.evolution_tree.to_dict()

    def get_agent(self, agent_id: str) -> Optional[Any]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [agent.to_dict() for agent in self.agents.values()]
