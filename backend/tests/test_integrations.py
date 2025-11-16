"""
Tests for sponsor integrations
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock


# Test fixtures for API keys
@pytest.fixture
def mock_anthropic_key():
    return "sk-ant-test-key-12345"


# ============================================================================
# Claude Integration Tests (REQUIRED)
# ============================================================================

def test_claude_integration_requires_api_key():
    """Test that Claude integration requires an API key"""
    from integrations.sponsors import ClaudeIntegration
    
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
        ClaudeIntegration(api_key="")


@pytest.mark.asyncio
async def test_claude_integration_think_method(mock_anthropic_key):
    """Test Claude think method with mocked API"""
    # Mock at import time
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test response from Claude")]
    mock_client.messages.create.return_value = mock_response
    
    mock_anthropic_module = MagicMock()
    mock_anthropic_module.Anthropic.return_value = mock_client
    
    with patch.dict('sys.modules', {'anthropic': mock_anthropic_module}):
        from integrations.sponsors import ClaudeIntegration
        
        claude = ClaudeIntegration(api_key=mock_anthropic_key)
        response = await claude.think("Test prompt")
        
        assert response == "Test response from Claude"
        assert mock_client.messages.create.called


@pytest.mark.asyncio
async def test_claude_integration_batch_think(mock_anthropic_key):
    """Test Claude batch think method"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Response")]
    mock_client.messages.create.return_value = mock_response
    
    mock_anthropic_module = MagicMock()
    mock_anthropic_module.Anthropic.return_value = mock_client
    
    with patch.dict('sys.modules', {'anthropic': mock_anthropic_module}):
        from integrations.sponsors import ClaudeIntegration
        
        claude = ClaudeIntegration(api_key=mock_anthropic_key)
        responses = await claude.batch_think(["Prompt 1", "Prompt 2"])
        
        assert len(responses) == 2
        assert all(r == "Response" for r in responses)


# ============================================================================
# Fastino Integration Tests (OPTIONAL)
# ============================================================================

@pytest.mark.asyncio
async def test_fastino_graceful_degradation_without_key():
    """Test Fastino degrades gracefully without API key"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Claude fallback response")]
    mock_client.messages.create.return_value = mock_response
    
    mock_anthropic_module = MagicMock()
    mock_anthropic_module.Anthropic.return_value = mock_client
    
    with patch.dict('sys.modules', {'anthropic': mock_anthropic_module}):
        from integrations.sponsors import ClaudeIntegration, FastinoIntegration
        
        claude = ClaudeIntegration(api_key="sk-test")
        fastino = FastinoIntegration(api_key="", fallback=claude)
        
        assert not fastino.available
        
        # Should fall back to Claude
        response = await fastino.generate("Test prompt")
        assert response == "Claude fallback response"


@pytest.mark.asyncio
async def test_fastino_with_api_key():
    """Test Fastino integration when API key is provided"""
    from integrations.sponsors import FastinoIntegration
    
    fastino = FastinoIntegration(api_key="fastino_key_123")
    
    assert fastino.available
    
    # Mock implementation returns simplified response
    response = await fastino.generate("Test prompt")
    assert "[Fastino]" in response


# ============================================================================
# LiquidMetal Integration Tests (OPTIONAL)
# ============================================================================

@pytest.mark.asyncio
async def test_liquidmetal_docker_fallback():
    """Test LiquidMetal falls back to Docker when unavailable"""
    from integrations.sponsors import LiquidMetalIntegration
    
    liquidmetal = LiquidMetalIntegration(api_key="")
    
    assert not liquidmetal.available
    
    # Mock Docker execution
    mock_container = MagicMock()
    mock_container.logs.return_value = b"Hello, World!"
    mock_container.wait.return_value = None
    
    mock_client = MagicMock()
    mock_client.containers.run.return_value = mock_container
    
    mock_docker_module = MagicMock()
    mock_docker_module.from_env.return_value = mock_client
    
    with patch.dict('sys.modules', {'docker': mock_docker_module}):
        result = await liquidmetal.execute_code("print('Hello, World!')")
        
        assert result["success"] is True
        assert result["method"] == "docker_fallback"


@pytest.mark.asyncio
async def test_liquidmetal_without_docker():
    """Test LiquidMetal handles missing Docker gracefully"""
    from integrations.sponsors import LiquidMetalIntegration
    
    liquidmetal = LiquidMetalIntegration(api_key="")
    
    # Mock Docker not being available
    with patch.dict('sys.modules', {'docker': None}):
        result = await liquidmetal.execute_code("print('test')")
        
        # Should handle missing Docker gracefully
        assert result["success"] is False


# ============================================================================
# Freepik Integration Tests (OPTIONAL)
# ============================================================================

@pytest.mark.asyncio
async def test_freepik_without_api_key():
    """Test Freepik returns None without API key"""
    from integrations.sponsors import FreepikIntegration
    
    freepik = FreepikIntegration(api_key="")
    
    assert not freepik.available
    
    result = await freepik.generate_image("A beautiful sunset")
    assert result is None


@pytest.mark.asyncio
async def test_freepik_with_api_key():
    """Test Freepik generates image URL with API key"""
    from integrations.sponsors import FreepikIntegration
    
    freepik = FreepikIntegration(api_key="freepik_key_123")
    
    assert freepik.available
    
    result = await freepik.generate_image("A beautiful sunset")
    assert result is not None
    assert "freepik.ai" in result


# ============================================================================
# Integration Factory Tests
# ============================================================================

def test_create_integrations_requires_claude(mock_anthropic_key):
    """Test that create_integrations requires Claude"""
    from integrations.sponsors import create_integrations
    
    mock_config = Mock()
    mock_config.ANTHROPIC_API_KEY = ""
    mock_config.FASTINO_API_KEY = ""
    mock_config.RAINDROP_API_KEY = ""
    mock_config.FREEPIK_API_KEY = ""
    mock_config.FRONTEGG_API_KEY = ""
    mock_config.AIRIA_API_KEY = ""
    
    with pytest.raises(ValueError):
        create_integrations(mock_config)


def test_create_integrations_with_claude_only(mock_anthropic_key):
    """Test creating integrations with only Claude (minimum requirement)"""
    mock_client = MagicMock()
    mock_anthropic_module = MagicMock()
    mock_anthropic_module.Anthropic.return_value = mock_client
    
    with patch.dict('sys.modules', {'anthropic': mock_anthropic_module}):
        from integrations.sponsors import create_integrations
        
        mock_config = Mock()
        mock_config.ANTHROPIC_API_KEY = mock_anthropic_key
        mock_config.FASTINO_API_KEY = ""
        mock_config.RAINDROP_API_KEY = ""
        mock_config.FREEPIK_API_KEY = ""
        mock_config.FRONTEGG_API_KEY = ""
        mock_config.AIRIA_API_KEY = ""
        
        integrations = create_integrations(mock_config)
        
        assert 'claude' in integrations
        assert integrations['claude'] is not None


def test_create_integrations_all_optional(mock_anthropic_key):
    """Test creating integrations with all optional integrations"""
    mock_client = MagicMock()
    mock_anthropic_module = MagicMock()
    mock_anthropic_module.Anthropic.return_value = mock_client
    
    with patch.dict('sys.modules', {'anthropic': mock_anthropic_module}):
        from integrations.sponsors import create_integrations
        
        mock_config = Mock()
        mock_config.ANTHROPIC_API_KEY = mock_anthropic_key
        mock_config.FASTINO_API_KEY = "fastino_key"
        mock_config.RAINDROP_API_KEY = "raindrop_key"
        mock_config.FREEPIK_API_KEY = "freepik_key"
        mock_config.FRONTEGG_API_KEY = "frontegg_key"
        mock_config.AIRIA_API_KEY = "airia_key"
        
        integrations = create_integrations(mock_config)
        
        # All integrations should be present
        assert 'claude' in integrations
        assert 'fastino' in integrations
        assert 'liquidmetal' in integrations
        assert 'freepik' in integrations
        assert 'frontegg' in integrations
        assert 'airia' in integrations
        
        # Check availability
        assert integrations['fastino'].available
        assert integrations['liquidmetal'].available
        assert integrations['freepik'].available
