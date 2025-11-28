"""
Cluster management and observability endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import psutil
from agents.worker_pool import agent_pool
from agents.infrastructure_agent import infra_agent

router = APIRouter(prefix="/api/cluster", tags=["cluster"])


@router.get("/status")
async def get_cluster_status() -> Dict[str, Any]:
    """
    Get complete cluster status including:
    - Worker health
    - System metrics
    - Infrastructure agent status
    """
    status = agent_pool.get_status()

    # Add infrastructure agent info
    status["infrastructure"] = {
        "monitoring_active": infra_agent.is_running,
        "healing_actions_count": len(infra_agent.healing_actions_taken),
        "permissions": infra_agent.can_configure_host(),
    }

    return status


@router.get("/agents/live")
async def get_live_agents():
    """Stream of live agent activity - optimized for frontend polling"""
    status = agent_pool.get_status()

    agents = []
    for worker_id, worker_data in status["workers"].items():
        health_emoji = "🟢" if worker_data["healthy"] else "🔴"
        agents.append(
            {
                "id": worker_id,
                "type": worker_data["type"],
                "status": f"{health_emoji} {worker_data['status']}",
                "pid": worker_data["pid"],
                "tasks_completed": worker_data.get("task_count", 0),
                "errors": worker_data.get("error_count", 0),
                "uptime": worker_data.get("started_at", "unknown"),
            }
        )

    return {
        "agents": agents,
        "summary": {
            "total": status["cluster"]["total_workers"],
            "healthy": status["cluster"]["healthy_workers"],
            "unhealthy": status["cluster"]["unhealthy_workers"],
        },
    }


@router.post("/heal")
async def trigger_manual_heal():
    """Manually trigger cluster self-heal"""
    healed = []

    for worker_id, worker in agent_pool.workers.items():
        if not worker.is_healthy():
            worker.restart()
            healed.append(worker_id)

    return {
        "healed_workers": healed,
        "count": len(healed),
        "message": f"♻️ Self-healed {len(healed)} workers",
    }


@router.post("/task/submit")
async def submit_task(agent_type: str, description: str):
    """Submit a task to the agent pool"""
    if agent_type not in ["architect", "coder", "executor", "critic", "deployer"]:
        raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")

    task_data = {"description": description, "submitted_by": "api"}

    task_id = await agent_pool.submit_task(agent_type, task_data)

    return {"task_id": task_id, "agent_type": agent_type, "status": "submitted"}


@router.get("/task/{task_id}")
async def get_task_result(task_id: str):
    """Get result of submitted task"""
    result = await agent_pool.get_result(task_id, timeout=5)

    if not result:
        return {"task_id": task_id, "status": "pending", "result": None}

    return {"task_id": task_id, "status": "completed", "result": result}


@router.get("/infrastructure/healing-history")
async def get_healing_history():
    """Get infrastructure agent healing history"""
    return {
        "history": infra_agent.get_healing_history(),
        "is_monitoring": infra_agent.is_running,
    }


@router.get("/metrics")
async def get_cluster_metrics():
    """Detailed cluster metrics for monitoring"""
    import redis

    try:
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        redis_info = r.info()
        redis_connected = True
    except:
        redis_info = {}
        redis_connected = False

    return {
        "timestamp": psutil.time.time(),
        "system": {
            "cpu": {
                "percent": psutil.cpu_percent(interval=0.1),
                "count": psutil.cpu_count(),
            },
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "available_mb": psutil.virtual_memory().available / 1024 / 1024,
            },
            "disk": {
                "percent": psutil.disk_usage("/").percent,
                "free_gb": psutil.disk_usage("/").free / 1024 / 1024 / 1024,
            },
        },
        "redis": {
            "connected": redis_connected,
            "used_memory_mb": (
                redis_info.get("used_memory", 0) / 1024 / 1024 if redis_connected else 0
            ),
        },
        "agents": agent_pool.get_status()["cluster"],
    }
