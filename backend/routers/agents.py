"""
Agent management API routes
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter()


class TaskCreate(BaseModel):
    """Task creation model"""
    description: str
    requirements: Optional[List[str]] = []
    constraints: Optional[List[str]] = []
    language: Optional[str] = "python"


class PipelineResponse(BaseModel):
    """Pipeline response model"""
    pipeline_id: str
    status: str
    message: Optional[str] = None


@router.post("/pipeline", response_model=PipelineResponse)
async def create_pipeline(task: TaskCreate, request: Request):
    """
    Create a new agent pipeline for a task
    
    This spawns architect→coder→executor→critic→deployer agents
    """
    orchestrator = request.app.state.orchestrator
    
    try:
        pipeline_id = await orchestrator.create_pipeline(task.dict())
        
        return PipelineResponse(
            pipeline_id=pipeline_id,
            status="created",
            message="Pipeline created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/{pipeline_id}/execute")
async def execute_pipeline(pipeline_id: str, request: Request):
    """
    Execute an agent pipeline
    
    Runs the full architect→coder→executor→critic→deployer sequence
    """
    orchestrator = request.app.state.orchestrator
    
    try:
        result = await orchestrator.execute_pipeline(pipeline_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str, request: Request):
    """Get status of a pipeline"""
    orchestrator = request.app.state.orchestrator
    
    try:
        status = await orchestrator.get_pipeline_status(pipeline_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipelines")
async def list_pipelines(request: Request):
    """List all pipelines"""
    orchestrator = request.app.state.orchestrator
    
    try:
        pipelines = await orchestrator.list_pipelines()
        return {"pipelines": pipelines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents(request: Request):
    """List all agents"""
    orchestrator = request.app.state.orchestrator
    
    try:
        agents = orchestrator.list_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, request: Request):
    """Get specific agent details"""
    orchestrator = request.app.state.orchestrator
    
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent.to_dict()


@router.get("/agents/{agent_id}/performance")
async def get_agent_performance(agent_id: str, request: Request):
    """Get agent performance summary"""
    orchestrator = request.app.state.orchestrator
    
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent.get_performance_summary()
