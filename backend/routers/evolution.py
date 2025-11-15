"""
Evolution tracking API routes
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, List

router = APIRouter()


@router.get("/tree")
async def get_evolution_tree(request: Request):
    """
    Get the complete evolution tree
    
    Shows agent lineage and performance across generations
    """
    orchestrator = request.app.state.orchestrator
    
    try:
        tree = orchestrator.get_evolution_tree()
        return tree
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tree/stats")
async def get_tree_stats(request: Request):
    """Get evolution tree statistics"""
    orchestrator = request.app.state.orchestrator
    
    try:
        tree = orchestrator.evolution_tree
        return tree.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generation/{generation_num}")
async def get_generation(generation_num: int, request: Request):
    """Get all agents in a specific generation"""
    orchestrator = request.app.state.orchestrator
    
    try:
        tree = orchestrator.evolution_tree
        generation = tree.get_generation(generation_num)
        return {"generation": generation_num, "agents": generation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/best-performers")
async def get_best_performers(top_n: int = 10, request: Request = None):
    """Get top performing agents"""
    orchestrator = request.app.state.orchestrator
    
    try:
        tree = orchestrator.evolution_tree
        performers = tree.get_best_performers(top_n)
        return {"top_performers": performers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lineage/{agent_id}")
async def get_agent_lineage(agent_id: str, request: Request):
    """Get complete lineage of an agent"""
    orchestrator = request.app.state.orchestrator
    
    try:
        tree = orchestrator.evolution_tree
        lineage = tree.get_lineage(agent_id)
        descendants = tree.get_descendants(agent_id)
        
        return {
            "agent_id": agent_id,
            "ancestors": lineage,
            "descendants": descendants
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/improvement/{agent_id}")
async def get_improvement_rate(agent_id: str, request: Request):
    """Get performance improvement rate for an agent's lineage"""
    orchestrator = request.app.state.orchestrator
    
    try:
        tree = orchestrator.evolution_tree
        rate = tree.calculate_improvement_rate(agent_id)
        
        return {
            "agent_id": agent_id,
            "improvement_rate": rate,
            "improvement_percentage": rate * 100
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
