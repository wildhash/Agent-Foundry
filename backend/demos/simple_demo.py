"""
Simple demonstration of Agent Foundry pipeline
Shows the core agent pipeline without requiring full Docker setup
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import AgentOrchestrator


async def run_demo():
    """
    Run a simple demo of the Agent Foundry pipeline
    """
    print("=" * 80)
    print("  Agent Foundry - Simple Demo")
    print("=" * 80)
    print()

    # Create orchestrator
    print("Initializing orchestrator...")
    orchestrator = AgentOrchestrator()
    print("✓ Orchestrator initialized")
    print()

    # Define task
    task = {
        "description": "Build a simple REST API for user management",
        "requirements": [
            "CRUD operations for users",
            "Input validation",
            "Error handling",
            "Basic authentication",
        ],
        "language": "python",
        "constraints": [
            "Keep it simple and maintainable",
            "Use modern Python practices",
        ],
    }

    print("Task:")
    print(f"  {task['description']}")
    print()
    print("Requirements:")
    for req in task["requirements"]:
        print(f"  • {req}")
    print()

    # Create and execute pipeline
    print("Creating pipeline...")
    pipeline_id = await orchestrator.create_pipeline(task)
    print(f"✓ Pipeline created: {pipeline_id}")
    print()

    print("Executing pipeline...")
    print("-" * 80)
    result = await orchestrator.execute_pipeline(pipeline_id)
    print("-" * 80)
    print()

    # Display results
    print("Results:")
    print(f"  Status: {result.get('status')}")
    print(f"  Overall Score: {result.get('overall_score', 0):.2f}")
    print()

    print("Agent Performance:")
    for agent_type, agent_data in result.get("agents", {}).items():
        perf = agent_data.get("performance_summary", {})
        print(
            f"  {agent_type:12} | Best: {perf.get('best_score', 0):.2f} | "
            f"Avg: {perf.get('average_score', 0):.2f} | "
            f"Executions: {perf.get('total_executions', 0)}"
        )
    print()

    # Save results
    output_file = f"/tmp/demo_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        # Remove circular references and non-serializable objects
        serializable_result = {
            "pipeline_id": result.get("pipeline_id"),
            "status": result.get("status"),
            "overall_score": result.get("overall_score"),
            "agents": {
                agent_type: {
                    "agent_id": data.get("agent_id"),
                    "agent_type": data.get("agent_type"),
                    "status": data.get("status"),
                    "generation": data.get("generation"),
                    "performance_summary": data.get("performance_summary"),
                }
                for agent_type, data in result.get("agents", {}).items()
            },
            "timestamp": datetime.now().isoformat(),
        }
        json.dump(serializable_result, f, indent=2)

    print(f"✓ Results saved to: {output_file}")
    print()

    # Evolution tree stats
    tree = orchestrator.get_evolution_tree()
    print("Evolution Tree:")
    print(f"  Total Nodes: {tree.get('total_nodes', 0)}")
    print(f"  Total Generations: {tree.get('total_generations', 0)}")
    print()

    print("=" * 80)
    print("  Demo Complete! 🎉")
    print("=" * 80)
    print()

    return result


if __name__ == "__main__":
    # Note: This demo uses mock integrations from existing files
    # For full functionality, set ANTHROPIC_API_KEY environment variable

    print()
    print("Note: This demo uses the existing mock integrations.")
    print("For full Claude integration, set ANTHROPIC_API_KEY environment variable.")
    print()

    asyncio.run(run_demo())
