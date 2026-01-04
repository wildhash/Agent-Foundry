"""
Agent Foundry - Self-Evolving Agent System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from agents.worker_pool import agent_pool
from agents.infrastructure_agent import infra_agent
from agents.orchestrator import AgentOrchestrator
from routers import cluster, agents, evolution, metrics, deployment

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Agent Foundry...")

    # Initialize orchestrator and attach to app state
    app.state.orchestrator = AgentOrchestrator()

    # Initialize worker pool and infrastructure agent
    await agent_pool.initialize()
    await infra_agent.start()

    logger.info("✅ Agent Foundry online")

    yield

    # Shutdown
    logger.info("🛑 Shutting down...")
    await agent_pool.shutdown()
    await infra_agent.stop()
    logger.info("✅ Graceful shutdown complete")


app = FastAPI(
    title="Agent Foundry",
    description="Self-evolving agent system with reflexion loops and meta-learning",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include ALL routers
app.include_router(cluster.router, prefix="/api/cluster", tags=["Cluster"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(evolution.router, prefix="/api/evolution", tags=["Evolution"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])
app.include_router(deployment.router, prefix="/api/deployment", tags=["Deployment"])


@app.get("/")
async def root():
    """Health check and system overview"""
    return {
        "message": "🤖 Agent Foundry Online",
        "version": "2.0.0",
        "features": [
            "Self-evolving agents",
            "Reflexion loops",
            "Meta-learning",
            "Evolution tree tracking",
        ],
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "worker_pool": agent_pool.is_initialized,
        "infrastructure_agent": infra_agent.is_running,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
