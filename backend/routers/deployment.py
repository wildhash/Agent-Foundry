"""
Deployment API routes
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional

from integrations import AiriaDeployment

router = APIRouter()


class DeploymentConfig(BaseModel):
    """Deployment configuration model"""

    agent_id: str
    environment: str = "production"
    replicas: int = 3


class ScaleRequest(BaseModel):
    """Scale request model"""

    replicas: int


@router.post("/deploy")
async def deploy_agent(config: DeploymentConfig):
    """
    Deploy an agent using Airia enterprise deployment

    Args:
        config: Deployment configuration

    Returns:
        Deployment information
    """
    airia = AiriaDeployment()

    try:
        result = await airia.deploy_agent(
            agent_config=config.dict(), environment=config.environment
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deployments/{deployment_id}/scale")
async def scale_deployment(deployment_id: str, scale_request: ScaleRequest):
    """Scale a deployment"""
    airia = AiriaDeployment()

    try:
        result = await airia.scale_deployment(deployment_id, scale_request.replicas)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments/{deployment_id}/metrics")
async def get_deployment_metrics(deployment_id: str):
    """Get metrics for a specific deployment"""
    airia = AiriaDeployment()

    try:
        metrics = await airia.get_deployment_metrics(deployment_id)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/deployments/{deployment_id}")
async def stop_deployment(deployment_id: str):
    """Stop a deployment"""
    airia = AiriaDeployment()

    try:
        result = await airia.stop_deployment(deployment_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments")
async def list_deployments():
    """List all deployments"""
    airia = AiriaDeployment()

    try:
        stats = airia.get_stats()
        return {
            "total_deployments": stats["total_deployments"],
            "active_deployments": stats["active_deployments"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
