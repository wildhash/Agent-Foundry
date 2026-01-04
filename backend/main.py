"""
Agent Foundry - Persistent Agent Cluster
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from agents.worker_pool import agent_pool
from agents.infrastructure_agent import infra_agent
from agents.merge_agent import MergeAgent
from routers import cluster, merge
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Agent Foundry Cluster...")
    await agent_pool.initialize()
    await infra_agent.start()

    # Initialize merge agent if GitHub credentials are provided
    if settings.GITHUB_TOKEN and settings.GITHUB_REPO_OWNER and settings.GITHUB_REPO_NAME:
        logger.info("🔀 Initializing Merge Agent...")
        app.state.merge_agent = MergeAgent(
            agent_id="merge_agent_primary",
            github_token=settings.GITHUB_TOKEN,
            repo_owner=settings.GITHUB_REPO_OWNER,
            repo_name=settings.GITHUB_REPO_NAME,
        )
        logger.info("✅ Merge Agent initialized")
    else:
        logger.info("⚠️ Merge Agent not initialized (GitHub credentials not provided)")
        app.state.merge_agent = None

    logger.info("✅ Cluster online and self-healing enabled")

    yield

    # Shutdown
    logger.info("🛑 Shutting down cluster...")
    await agent_pool.shutdown()
    await infra_agent.stop()
    logger.info("✅ Graceful shutdown complete")


app = FastAPI(
    title="Agent Foundry Cluster",
    description="Self-evolving agent system with persistent workers",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cluster.router)
app.include_router(merge.router, prefix="/merge", tags=["merge"])


@app.get("/")
async def root():
    """Health check and cluster overview"""
    status = agent_pool.get_status()

    merge_agent_status = "initialized" if app.state.merge_agent else "not_configured"

    return {
        "message": "🤖 Agent Foundry Cluster Online",
        "version": "1.0.0",
        "cluster": {
            "workers": status["cluster"]["total_workers"],
            "healthy": status["cluster"]["healthy_workers"],
        },
        "infrastructure_monitoring": infra_agent.is_running,
        "merge_agent": merge_agent_status,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    return {
        "status": "healthy",
        "cluster_initialized": agent_pool.is_initialized,
        "infrastructure_agent": infra_agent.is_running,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
