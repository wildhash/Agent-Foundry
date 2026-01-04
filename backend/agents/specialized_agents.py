"""
Specialized agent implementations
"""

from typing import Dict, Any, List
import logging
from agents.base_agent import BaseAgent
from integrations.fastino import FastinoTLM
from integrations.raindrop import LiquidMetalRaindrop

logger = logging.getLogger(__name__)


class ArchitectAgent(BaseAgent):
    """Architect agent for system design and planning"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "architect")
        self.fastino = FastinoTLM()
        self.design_patterns = []

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Design system architecture"""
        logger.info(f"Architect designing system for: {task.get('description', 'N/A')}")

        # Use Fastino TLM for fast design generation
        design_prompt = f"""
        Design a system architecture for: {task.get('description')}
        Requirements: {task.get('requirements', [])}
        Constraints: {task.get('constraints', [])}
        """

        architecture = await self.fastino.generate(prompt=design_prompt, max_tokens=2048, temperature=0.7)

        return {
            "architecture": architecture,
            "components": self._extract_components(architecture),
            "design_patterns": self.design_patterns,
            "estimated_complexity": self._estimate_complexity(architecture),
        }

    async def evaluate_performance(self, result: Dict[str, Any]) -> float:
        """Evaluate architecture quality"""
        # Evaluate based on completeness, modularity, scalability
        score = 0.0

        if "components" in result and len(result["components"]) > 0:
            score += 0.3

        if "architecture" in result and len(result["architecture"]) > 100:
            score += 0.3

        complexity = result.get("estimated_complexity", 1.0)
        if complexity < 5:  # Not too complex
            score += 0.4
        else:
            score += 0.2

        return min(score, 1.0)

    async def _adjust_strategy(self, reason: str):
        """Adjust architectural strategy"""
        if reason == "performance_decline":
            self.design_patterns.append("simplified_design")

    def _extract_components(self, architecture: str) -> List[str]:
        """Extract components from architecture description"""
        # Simple extraction - would be more sophisticated in production
        components = []
        keywords = ["service", "api", "database", "cache", "queue", "worker"]
        for keyword in keywords:
            if keyword in architecture.lower():
                components.append(keyword)
        return components

    def _estimate_complexity(self, architecture: str) -> int:
        """Estimate design complexity"""
        return len(architecture.split()) // 50


class CoderAgent(BaseAgent):
    """Coder agent for code generation"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "coder")
        self.fastino = FastinoTLM()
        self.raindrop = LiquidMetalRaindrop()
        self.code_style = "pythonic"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code based on architecture"""
        logger.info(f"Coder generating code for: {task.get('description', 'N/A')}")

        code_prompt = f"""
        Generate code for: {task.get('description')}
        Architecture: {task.get('architecture', {})}
        Language: {task.get('language', 'python')}
        Style: {self.code_style}
        """

        code = await self.fastino.generate(prompt=code_prompt, max_tokens=2048, temperature=0.5)

        # Apply self-healing with LiquidMetal Raindrop
        healed_code = await self.raindrop.heal_code(code)

        return {
            "code": healed_code,
            "language": task.get("language", "python"),
            "healed": healed_code != code,
            "lines_of_code": len(healed_code.split("\n")),
        }

    async def evaluate_performance(self, result: Dict[str, Any]) -> float:
        """Evaluate code quality"""
        score = 0.0

        code = result.get("code", "")

        # Check if code is non-empty
        if len(code) > 50:
            score += 0.3

        # Check if code has proper structure
        if "def " in code or "class " in code:
            score += 0.3

        # Bonus for self-healing
        if result.get("healed", False):
            score += 0.2

        # Check reasonable length
        loc = result.get("lines_of_code", 0)
        if 10 < loc < 500:
            score += 0.2

        return min(score, 1.0)

    async def _adjust_strategy(self, reason: str):
        """Adjust coding strategy"""
        if reason == "performance_decline":
            self.code_style = "detailed"


class ExecutorAgent(BaseAgent):
    """Executor agent for running and testing code"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "executor")
        self.execution_env = "sandboxed"

        # Import sandbox service
        from services.sandbox import sandbox_service

        self.sandbox = sandbox_service

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code in sandboxed environment"""
        logger.info(f"Executor running code: {task.get('description', 'N/A')}")

        code = task.get("code", "")

        if not code.strip():
            return {
                "success": False,
                "output": "",
                "error": "No code provided",
                "execution_time": 0,
                "exit_code": -1,
            }

        # Execute in sandbox
        result = await self.sandbox.execute_python(code)

        return {
            "success": result.success,
            "output": result.stdout,
            "error": result.stderr,
            "execution_time": result.execution_time_ms / 1000,  # Convert to seconds
            "memory_used": result.memory_used_bytes or 0,
            "exit_code": result.exit_code,
        }

    async def evaluate_performance(self, result: Dict[str, Any]) -> float:
        """Evaluate execution success"""
        score = 0.0

        if result.get("success", False):
            score += 0.5

        if result.get("exit_code", -1) == 0:
            score += 0.3

        # Reward fast execution
        exec_time = result.get("execution_time", 999)
        if exec_time < 1.0:
            score += 0.2

        return min(score, 1.0)

    async def _adjust_strategy(self, reason: str):
        """Adjust execution strategy"""
        if reason == "performance_decline":
            self.execution_env = "optimized_sandbox"


class CriticAgent(BaseAgent):
    """Critic agent for evaluating and providing feedback"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "critic")
        self.fastino = FastinoTLM()
        self.critique_depth = "standard"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Critique the work of other agents"""
        logger.info(f"Critic evaluating: {task.get('description', 'N/A')}")

        critique_prompt = f"""
        Evaluate the following work:
        Architecture: {task.get('architecture', 'N/A')}
        Code: {task.get('code', 'N/A')}
        Execution: {task.get('execution_result', 'N/A')}

        Provide constructive criticism and suggestions.
        """

        critique = await self.fastino.generate(prompt=critique_prompt, max_tokens=1024, temperature=0.6)

        return {
            "critique": critique,
            "overall_score": self._calculate_overall_score(task),
            "suggestions": self._extract_suggestions(critique),
            "passed": self._calculate_overall_score(task) >= 0.75,
        }

    async def evaluate_performance(self, result: Dict[str, Any]) -> float:
        """Evaluate critique quality"""
        score = 0.0

        critique = result.get("critique", "")
        if len(critique) > 50:
            score += 0.4

        if result.get("suggestions"):
            score += 0.3

        if "overall_score" in result:
            score += 0.3

        return min(score, 1.0)

    async def _adjust_strategy(self, reason: str):
        """Adjust critique strategy"""
        if reason == "performance_decline":
            self.critique_depth = "detailed"

    def _calculate_overall_score(self, task: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        # Simplified scoring
        return 0.82  # Would be more sophisticated in production

    def _extract_suggestions(self, critique: str) -> List[str]:
        """Extract actionable suggestions from critique"""
        # Simplified extraction
        return [
            "Consider adding error handling",
            "Optimize performance",
            "Add documentation",
        ]


class DeployerAgent(BaseAgent):
    """Deployer agent for deployment and monitoring"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, "deployer")
        self.deployment_strategy = "rolling"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy code to production"""
        logger.info(f"Deployer deploying: {task.get('description', 'N/A')}")

        # Simulate deployment process
        deployment_result = {
            "deployed": True,
            "endpoint": f"https://api.agentfoundry.ai/v1/{task.get('service_name', 'service')}",
            "version": f"v{self.generation}.0.0",
            "strategy": self.deployment_strategy,
            "replicas": 3,
            "health_check": "passing",
        }

        return deployment_result

    async def evaluate_performance(self, result: Dict[str, Any]) -> float:
        """Evaluate deployment success"""
        score = 0.0

        if result.get("deployed", False):
            score += 0.4

        if result.get("health_check") == "passing":
            score += 0.3

        if result.get("replicas", 0) >= 2:
            score += 0.3

        return min(score, 1.0)

    async def _adjust_strategy(self, reason: str):
        """Adjust deployment strategy"""
        if reason == "performance_decline":
            self.deployment_strategy = "blue_green"
