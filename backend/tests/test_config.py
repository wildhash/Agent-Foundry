"""
Tests for configuration module  
"""

import pytest
import os


def test_config_loads_with_anthropic_key(mock_anthropic_key, monkeypatch):
    """Test configuration loads successfully with ANTHROPIC_API_KEY"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", mock_anthropic_key)
    
    # Need to reload to pick up new env var
    import sys
    if 'config' in sys.modules:
        del sys.modules['config']
    
    from config import settings, Settings
    
    assert settings.ANTHROPIC_API_KEY == mock_anthropic_key
    assert settings.APP_NAME == "Agent Foundry"
    assert settings.MAX_REFLEXION_LOOPS == 5
    assert settings.PERFORMANCE_THRESHOLD == 0.75
    assert settings.EVOLUTION_THRESHOLD == 0.85
    
    # Verify Settings class structure
    assert hasattr(Settings, '__annotations__')
    assert 'ANTHROPIC_API_KEY' in Settings.__annotations__


def test_optional_keys_default_empty(mock_anthropic_key, monkeypatch):
    """Test that optional API keys default to empty strings"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", mock_anthropic_key)
    # Clear optional keys
    for key in ["FASTINO_API_KEY", "FREEPIK_API_KEY", "FRONTEGG_API_KEY", "AIRIA_API_KEY", "RAINDROP_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    
    # Need to reload
    import sys
    if 'config' in sys.modules:
        del sys.modules['config']
    
    from config import settings
    
    assert settings.FASTINO_API_KEY == ""
    assert settings.FREEPIK_API_KEY == ""
    assert settings.FRONTEGG_API_KEY == ""
    assert settings.AIRIA_API_KEY == ""
    assert settings.RAINDROP_API_KEY == ""


def test_config_reflexion_settings(mock_anthropic_key, monkeypatch):
    """Test reflexion loop configuration"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", mock_anthropic_key)
    
    # Need to reload
    import sys
    if 'config' in sys.modules:
        del sys.modules['config']
    
    from config import settings
    
    assert isinstance(settings.MAX_REFLEXION_LOOPS, int)
    assert settings.MAX_REFLEXION_LOOPS > 0
    assert 0.0 < settings.PERFORMANCE_THRESHOLD < 1.0
    assert 0.0 < settings.EVOLUTION_THRESHOLD < 1.0


def test_config_database_and_redis_urls(mock_anthropic_key, monkeypatch):
    """Test database and Redis configuration"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", mock_anthropic_key)
    
    import sys
    if 'config' in sys.modules:
        del sys.modules['config']
    
    from config import settings
    
    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None
    assert "redis://" in settings.REDIS_URL
