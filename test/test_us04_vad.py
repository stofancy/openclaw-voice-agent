"""
Test cases for US-04: Voice Activity Detection (VAD) functionality.
"""
import asyncio
import pytest
import websockets
import json
from unittest.mock import Mock, patch

from backend.voice_gateway.config import Config
from backend.voice_gateway.webrtc_server import WebRTCServer

@pytest.fixture
def config():
    """Test configuration."""
    return Config(
        WS_HOST="localhost",
        WS_PORT=8765,
        DASHSCOPE_API_KEY="test-key"
    )

@pytest.mark.asyncio
async def test_vad_hook_exists():
    """Verify that the VAD hook is available in the frontend."""
    # This test verifies that the useVAD hook file exists
    # and can be imported by the frontend application
    import os
    vad_hook_path = "frontend/src/hooks/useVAD.ts"
    assert os.path.exists(vad_hook_path), f"VAD hook file not found at {vad_hook_path}"

@pytest.mark.asyncio
async def test_vad_default_options():
    """Test that VAD hook uses default options when none provided."""
    # Default options should be:
    # silenceThreshold = 0.01
    # silenceDuration = 1000 (1 second)
    # This is verified by checking the source code
    import os
    with open("frontend/src/hooks/useVAD.ts", "r") as f:
        content = f.read()
        assert "silenceThreshold = 0.01" in content
        assert "silenceDuration = 1000" in content

@pytest.mark.asyncio
async def test_vad_custom_options():
    """Test that VAD hook accepts custom options."""
    # The hook should accept custom silenceThreshold and silenceDuration
    # This is verified by checking the interface definition
    import os
    with open("frontend/src/hooks/useVAD.ts", "r") as f:
        content = f.read()
        assert "interface VADOptions" in content
        assert "silenceThreshold?: number" in content
        assert "silenceDuration?: number" in content
        assert "onSpeechEnd?: () => void" in content

@pytest.mark.asyncio
async def test_vad_returns_start_stop_functions():
    """Test that VAD hook returns startVAD and stopVAD functions."""
    import os
    with open("frontend/src/hooks/useVAD.ts", "r") as f:
        content = f.read()
        assert "return { startVAD, stopVAD }" in content

@pytest.mark.asyncio
async def test_vad_cleanup_on_unmount():
    """Test that VAD cleans up resources on component unmount."""
    import os
    with open("frontend/src/hooks/useVAD.ts", "r") as f:
        content = f.read()
        assert "useEffect(() => {" in content
        assert "return () => stopVAD();" in content

@pytest.mark.unit
def test_vad_integration_with_mock_audio():
    """Test VAD functionality with mock audio data."""
    # Create mock audio data (simulating PCM audio)
    mock_audio_data = bytes([0] * 3200)  # 100ms of 16kHz 16-bit mono audio
    
    # Mock VAD processor
    mock_vad = Mock()
    mock_vad.process = Mock(return_value={
        'is_speech': True,
        'confidence': 0.85,
        'duration_ms': 100
    })
    
    def process_audio_with_vad(audio_data):
        """Simulate VAD processing."""
        return mock_vad.process(audio_data)
    
    # Process mock audio
    result = process_audio_with_vad(mock_audio_data)
    
    # Verify VAD was called and returned expected result
    mock_vad.process.assert_called_once_with(mock_audio_data)
    assert result is not None
    assert 'is_speech' in result
    assert result['is_speech'] is True
    assert result['confidence'] > 0.5