"""
Base Agent class with reflexion loops and performance tracking
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status"""

    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentMemory:
    """Memory structure for agent experiences"""

    task: str
    action: str
    result: Any
    performance_score: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReflexionResult:
    """Result of a reflexion loop"""

    improved: bool
    new_strategy: str
    performance_delta: float
    insights: List[str]


class BaseAgent(ABC):
    """Base class for all agents with reflexion capabilities"""

    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = AgentStatus.IDLE
        self.memory: List[AgentMemory] = []
        self.performance_scores: List[float] = []
        self.generation = 0
        self.parent_id: Optional[str] = None
        self.children_ids: List[str] = []

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's primary task"""
        pass

    @abstractmethod
    async def evaluate_performance(self, result: Dict[str, Any]) -> float:
        """Evaluate the performance of the execution"""
        pass

    async def reflexion_loop(self, task: Dict[str, Any], max_loops: int = 5) -> Dict[str, Any]:
        """
        Perform reflexion loop: execute → evaluate → reflect → improve
        """
        best_result = None
        best_score = 0.0

        for loop in range(max_loops):
            logger.info(f"{self.agent_type} {self.agent_id} - Reflexion loop {loop + 1}/{max_loops}")

            self.status = AgentStatus.EXECUTING
            result = await self.execute(task)

            self.status = AgentStatus.REFLECTING
            score = await self.evaluate_performance(result)
            self.performance_scores.append(score)

            # Store in memory
            memory = AgentMemory(
                task=str(task),
                action=self.agent_type,
                result=result,
                performance_score=score,
                timestamp=datetime.now(),
            )
            self.memory.append(memory)

            # Keep best result
            if score > best_score:
                best_score = score
                best_result = result

            # If performance is good enough, stop
            if score >= 0.85:
                logger.info(f"Excellent performance ({score:.2f}), stopping reflexion")
                break

            # Reflect and adjust strategy
            if loop < max_loops - 1:
                await self.reflect_and_adjust(result, score)

        self.status = AgentStatus.COMPLETED
        return {
            "result": best_result,
            "score": best_score,
            "loops_executed": loop + 1,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
        }

    async def reflect_and_adjust(self, result: Dict[str, Any], score: float):
        """Reflect on performance and adjust strategy"""
        # Analyze recent performance trend
        if len(self.performance_scores) >= 2:
            trend = self.performance_scores[-1] - self.performance_scores[-2]
            if trend < 0:
                logger.info(f"Performance declining ({trend:.2f}), adjusting strategy")
                await self._adjust_strategy("performance_decline")
            elif trend > 0:
                logger.info(f"Performance improving ({trend:.2f}), continuing strategy")

        # Learn from past experiences
        await self.meta_learn()

    async def meta_learn(self):
        """Learn from past experiences to improve future performance"""
        if len(self.memory) < 2:
            return

        # Analyze patterns in successful vs unsuccessful attempts
        successful = [m for m in self.memory if m.performance_score >= 0.75]
        unsuccessful = [m for m in self.memory if m.performance_score < 0.75]

        if successful:
            logger.info(f"Learning from {len(successful)} successful experiences")
            # Extract common patterns from successful attempts
            # This would involve more sophisticated learning in production

    @abstractmethod
    async def _adjust_strategy(self, reason: str):
        """Adjust internal strategy based on reflection"""
        pass

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of agent performance"""
        if not self.performance_scores:
            return {
                "average_score": 0.0,
                "best_score": 0.0,
                "worst_score": 0.0,
                "total_executions": 0,
            }

        return {
            "average_score": sum(self.performance_scores) / len(self.performance_scores),
            "best_score": max(self.performance_scores),
            "worst_score": min(self.performance_scores),
            "total_executions": len(self.performance_scores),
            "current_generation": self.generation,
        }

    def spawn_child(self) -> str:
        """Spawn a new generation child agent"""
        child_id = f"{self.agent_id}_gen{self.generation + 1}"
        self.children_ids.append(child_id)
        return child_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "generation": self.generation,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "performance_summary": self.get_performance_summary(),
            "memory_size": len(self.memory),
        }
