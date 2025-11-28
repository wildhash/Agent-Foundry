"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_anthropic_key():
    """Mock Anthropic API key for testing"""
    return "sk-ant-test-key-123456789"


@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        "ANTHROPIC_API_KEY": "sk-ant-test-key",
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379",
        "MAX_REFLEXION_LOOPS": 3,
        "PERFORMANCE_THRESHOLD": 0.75,
        "EVOLUTION_THRESHOLD": 0.85,
    }


@pytest.fixture
async def mock_claude_response():
    """Mock Claude API response"""
    return {
        "content": [{"text": "Mock Claude response"}],
        "model": "claude-sonnet-4-20250514",
        "role": "assistant",
    }
