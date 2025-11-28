"""
Metrics and monitoring API routes
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

router = APIRouter()


@router.get("/system")
async def get_system_metrics(request: Request):
    """Get overall system metrics"""
    orchestrator = request.app.state.orchestrator

    try:
        metrics = {
            "total_agents": len(orchestrator.agents),
            "active_pipelines": len(
                [
                    p
                    for p in orchestrator.active_pipelines.values()
                    if p["status"] == "running"
                ]
            ),
            "completed_pipelines": len(
                [
                    p
                    for p in orchestrator.active_pipelines.values()
                    if p["status"] == "completed"
                ]
            ),
            "evolution_tree": orchestrator.evolution_tree.get_stats(),
        }

        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations")
async def get_integration_metrics():
    """Get metrics for external integrations"""
    from integrations.fastino import FastinoTLM
    from integrations.raindrop import LiquidMetalRaindrop
    from integrations import FreepikAPI, FronteggAuth, AiriaDeployment

    try:
        fastino = FastinoTLM()
        raindrop = LiquidMetalRaindrop()
        freepik = FreepikAPI()
        frontegg = FronteggAuth()
        airia = AiriaDeployment()

        return {
            "fastino_tlm": fastino.get_stats(),
            "liquidmetal_raindrop": raindrop.get_stats(),
            "freepik_api": freepik.get_stats(),
            "frontegg_auth": frontegg.get_stats(),
            "airia_deployment": airia.get_stats(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_metrics(request: Request):
    """Get aggregated performance metrics"""
    orchestrator = request.app.state.orchestrator

    try:
        all_scores = []
        for agent in orchestrator.agents.values():
            all_scores.extend(agent.performance_scores)

        if not all_scores:
            return {
                "average_score": 0.0,
                "best_score": 0.0,
                "worst_score": 0.0,
                "total_executions": 0,
            }

        return {
            "average_score": sum(all_scores) / len(all_scores),
            "best_score": max(all_scores),
            "worst_score": min(all_scores),
            "total_executions": len(all_scores),
            "agents_tracked": len(orchestrator.agents),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reflexion")
async def get_reflexion_metrics(request: Request):
    """Get metrics about reflexion loops"""
    orchestrator = request.app.state.orchestrator

    try:
        total_loops = 0
        total_improvements = 0

        for pipeline in orchestrator.active_pipelines.values():
            results = pipeline.get("results", {})
            for stage_result in results.values():
                loops = stage_result.get("loops_executed", 0)
                total_loops += loops
                if loops > 1:
                    total_improvements += 1

        return {
            "total_reflexion_loops": total_loops,
            "total_improvements": total_improvements,
            "pipelines_with_reflexion": len(
                [
                    p
                    for p in orchestrator.active_pipelines.values()
                    if any(
                        r.get("loops_executed", 0) > 1
                        for r in p.get("results", {}).values()
                    )
                ]
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
