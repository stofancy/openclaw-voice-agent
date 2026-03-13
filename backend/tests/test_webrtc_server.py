"""
Test WebRTC server functionality.
"""
import asyncio
import pytest
import websockets
from unittest.mock import Mock, AsyncMock, patch
from voice_gateway.config import Config
from voice_gateway.webrtc_server import WebRTCServer

@pytest.fixture
def config():
    """Create test configuration."""
    config = Config()
    config.host = "127.0.0.1"
    config.port = 8765
    return config

@pytest.fixture
def webrtc_server(config):
    """Create WebRTC server instance."""
    return WebRTCServer(config)

@pytest.mark.asyncio
async def test_server_startup_shutdown(webrtc_server):
    """Test server startup and shutdown."""
    # Start server
    await webrtc_server.start()
    assert webrtc_server.running is True
    
    # Stop server
    await webrtc_server.stop()
    assert webrtc_server.running is False

@pytest.mark.asyncio
async def test_websocket_connection(config):
    """Test WebSocket connection handling."""
    server = WebRTCServer(config)
    
    # Start server
    await server.start()
    
    try:
        # Connect client - the server automatically sends a ready message
        async with websockets.connect(f"ws://localhost:{config.port}") as websocket:
            # Receive ready message (sent automatically by server)
            response = await websocket.recv()
            import json
            data = json.loads(response)
            
            assert data["type"] == "ready"
            assert data["status"] == "ok"
            
    finally:
        await server.stop()

@pytest.mark.asyncio
async def test_sdp_offer_answer_exchange(config):
    """Test SDP offer/answer exchange."""
    server = WebRTCServer(config)
    
    # Start server
    await server.start()
    
    try:
        async with websockets.connect(f"ws://localhost:{config.port}") as websocket:
            # Receive initial ready message
            ready_msg = await websocket.recv()
            
            # Send offer as proper JSON
            import json
            offer = {
                "type": "offer",
                "sdp": "fake-sdp-offer"
            }
            await websocket.send(json.dumps(offer))
            
            # Should receive answer
            response = await websocket.recv()
            data = json.loads(response)
            
            assert data["type"] == "answer"
            assert "sdp" in data
            
    finally:
        await server.stop()

@pytest.mark.asyncio
async def test_ice_candidate_exchange(config):
    """Test ICE candidate exchange."""
    server = WebRTCServer(config)
    
    # Start server
    await server.start()
    
    try:
        async with websockets.connect(f"ws://localhost:{config.port}") as websocket:
            # Receive initial ready message
            ready_msg = await websocket.recv()
            
            # Send ICE candidate as proper JSON
            import json
            candidate = {
                "type": "ice-candidate",
                "candidate": "fake-candidate",
                "sdpMid": "0",
                "sdpMLineIndex": 0
            }
            await websocket.send(json.dumps(candidate))
            
            # Should receive acknowledgment
            response = await websocket.recv()
            data = json.loads(response)
            
            assert data["type"] == "ice-candidate-received"
            assert data["candidate"] == "fake-candidate"
            
    finally:
        await server.stop()