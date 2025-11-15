"""
Agent Foundry - Self-Evolving Agent System
Main FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

try:
    from .agents.orchestrator import AgentOrchestrator
    from .routers import agents, evolution, metrics, deployment
    from .config import settings
except ImportError:
    from agents.orchestrator import AgentOrchestrator
    from routers import agents, evolution, metrics, deployment
    from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Agent Foundry...")
    app.state.orchestrator = AgentOrchestrator()
    yield
    logger.info("Shutting down Agent Foundry...")


app = FastAPI(
    title="Agent Foundry",
    description="Self-evolving agents with architect→coder→executor→critic→deployer pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(evolution.router, prefix="/api/evolution", tags=["evolution"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(deployment.router, prefix="/api/deployment", tags=["deployment"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Agent Foundry",
        "version": "1.0.0",
        "description": "The last agent you'll ever need to build"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
