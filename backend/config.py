"""
Configuration settings for Agent Foundry
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Agent Foundry"
    DEBUG: bool = False

    # API Keys - REQUIRED
    ANTHROPIC_API_KEY: str  # Required, no default

    # API Keys - OPTIONAL (for sponsor integrations)
    FASTINO_API_KEY: str = ""
    FREEPIK_API_KEY: str = ""
    FRONTEGG_API_KEY: str = ""
    AIRIA_API_KEY: str = ""
    RAINDROP_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    DATABASE_URL: str = "sqlite:///./agent_foundry.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Agent Configuration
    MAX_REFLEXION_LOOPS: int = 5
    PERFORMANCE_THRESHOLD: float = 0.75
    EVOLUTION_THRESHOLD: float = 0.85

    # Fastino TLM Settings (99x faster inference)
    FASTINO_INFERENCE_SPEED_MULTIPLIER: int = 99
    FASTINO_BATCH_SIZE: int = 32
    FASTINO_MAX_TOKENS: int = 2048

    # LiquidMetal Raindrop Settings (self-healing code)
    RAINDROP_AUTO_HEAL: bool = True
    RAINDROP_MAX_ATTEMPTS: int = 3
    RAINDROP_HEAL_TIMEOUT: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
