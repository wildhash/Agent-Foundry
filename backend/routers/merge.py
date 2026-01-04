"""
Merge Agent API routes
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter()


class MergeTaskCreate(BaseModel):
    """Merge task creation model"""

    description: str
    cleanup_stale_branches: Optional[bool] = False
    merge_criteria: Optional[Dict[str, Any]] = None


class MergeCriteriaUpdate(BaseModel):
    """Merge criteria update model"""

    required_approvals: Optional[int] = None
    require_ci_pass: Optional[bool] = None
    allow_merge_conflicts: Optional[bool] = None
    merge_strategy: Optional[str] = None
    stale_days: Optional[int] = None


class MergeResponse(BaseModel):
    """Merge response model"""

    status: str
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


@router.post("/execute", response_model=MergeResponse)
async def execute_merge_agent(task: MergeTaskCreate, request: Request):
    """
    Execute merge agent to evaluate and merge eligible PRs

    This will:
    - Fetch open pull requests
    - Check mergeability criteria (CI status, approvals, conflicts)
    - Merge eligible PRs
    - Optionally cleanup stale branches
    """
    # Get or create merge agent
    merge_agent = getattr(request.app.state, "merge_agent", None)

    if not merge_agent:
        raise HTTPException(status_code=503, detail="Merge agent not initialized. Configure GitHub credentials.")

    try:
        # Execute agent with reflexion loop
        result = await merge_agent.reflexion_loop(task.dict())

        return MergeResponse(
            status="completed",
            message=f"Merge agent completed. Merged {len(result['result'].get('merged_prs', []))} PRs.",
            result=result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_merge_agent_status(request: Request):
    """Get merge agent status and performance summary"""
    merge_agent = getattr(request.app.state, "merge_agent", None)

    if not merge_agent:
        return {
            "initialized": False,
            "message": "Merge agent not initialized",
        }

    return {
        "initialized": True,
        "agent": merge_agent.to_dict(),
        "performance": merge_agent.get_performance_summary(),
        "merge_criteria": merge_agent.get_merge_criteria(),
    }


@router.get("/criteria")
async def get_merge_criteria(request: Request):
    """Get current merge criteria configuration"""
    merge_agent = getattr(request.app.state, "merge_agent", None)

    if not merge_agent:
        raise HTTPException(status_code=503, detail="Merge agent not initialized")

    return {
        "merge_criteria": merge_agent.get_merge_criteria(),
    }


@router.put("/criteria")
async def update_merge_criteria(criteria: MergeCriteriaUpdate, request: Request):
    """Update merge criteria configuration"""
    merge_agent = getattr(request.app.state, "merge_agent", None)

    if not merge_agent:
        raise HTTPException(status_code=503, detail="Merge agent not initialized")

    # Filter out None values
    criteria_dict = {k: v for k, v in criteria.dict().items() if v is not None}

    if not criteria_dict:
        raise HTTPException(status_code=400, detail="No criteria provided")

    merge_agent.configure_merge_criteria(criteria_dict)

    return {
        "status": "updated",
        "merge_criteria": merge_agent.get_merge_criteria(),
    }


@router.get("/history")
async def get_merge_history(request: Request):
    """Get merge agent execution history"""
    merge_agent = getattr(request.app.state, "merge_agent", None)

    if not merge_agent:
        raise HTTPException(status_code=503, detail="Merge agent not initialized")

    # Return memory/history
    memory_summary = []
    for mem in merge_agent.memory:
        memory_summary.append(
            {
                "task": mem.task,
                "performance_score": mem.performance_score,
                "timestamp": mem.timestamp.isoformat(),
                "merged_prs": len(mem.result.get("merged_prs", [])) if isinstance(mem.result, dict) else 0,
                "skipped_prs": len(mem.result.get("skipped_prs", [])) if isinstance(mem.result, dict) else 0,
            }
        )

    return {
        "history": memory_summary,
        "total_executions": len(memory_summary),
    }
