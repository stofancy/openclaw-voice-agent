"""
Test configuration module.
"""
import os
import pytest
from voice_gateway.config import Config

def test_config_defaults():
    """Test default configuration values."""
    config = Config()
    assert config.host == "0.0.0.0"
    assert config.port == 8080
    assert config.debug is False

def test_config_from_env():
    """Test configuration from environment variables."""
    os.environ["DEBUG"] = "true"
    os.environ["HOST"] = "127.0.0.1"
    os.environ["PORT"] = "9090"
    
    config = Config()
    assert config.debug is True
    assert config.host == "127.0.0.1"
    assert config.port == 9090
    
    # Clean up
    del os.environ["DEBUG"]
    del os.environ["HOST"]
    del os.environ["PORT"]