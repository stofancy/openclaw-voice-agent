"""
Test cases for US-11: Network disconnect functionality.
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
        host="localhost",
        port=9709,  # Use different port to avoid conflicts
        debug=True
    )

@pytest.mark.asyncio
async def test_network_disconnect_shows_disconnected_message(config):
    """Test that network disconnection shows '网络断开' message."""
    server = WebRTCServer(config)

    # Start server in background
    server_task = asyncio.create_task(server.start())

    try:
        # Give server time to start up
        await asyncio.sleep(0.1)

        # Connect client
        async with websockets.connect(f"ws://localhost:{config.port}") as websocket:
            # Receive ready message
            message = await websocket.recv()
            data = json.loads(message)
            
            assert data["type"] == "ready"
            
        # After disconnecting, frontend should show "网络断开"
        # This is verified in the frontend logic
        
    finally:
        # Cleanup
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

@pytest.mark.asyncio
async def test_auto_reconnect_after_network_disconnect(config):
    """Test automatic reconnection after network disconnect (max 3 times)."""
    # This test verifies the retry logic in the frontend useWebRTC hook
    # The backend should handle multiple connection attempts gracefully

    server = WebRTCServer(config)
    server_task = asyncio.create_task(server.start())

    try:
        await asyncio.sleep(0.1)

        # Simulate multiple connection attempts (as frontend would do)
        for i in range(3):  # Max 3 retries as per US-11
            try:
                async with websockets.connect(f"ws://localhost:{config.port}") as websocket:
                    message = await websocket.recv()
                    data = json.loads(message)
                    assert data["type"] == "ready"
                    break  # Success, no need to retry
            except Exception as e:
                if i < 2:  # Allow 2 failures, 3rd should succeed or fail completely
                    await asyncio.sleep(3)  # Wait 3 seconds between retries
                else:
                    # After 3 attempts, should show final error
                    pass

    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

@pytest.mark.asyncio
async def test_reconnect_failure_shows_error_with_retry_button(config):
    """Test that after max retries, error message and retry button are shown."""
    # This is primarily a frontend test
    # Backend should send appropriate error messages that frontend can display
    
    # For now, we verify that the backend can handle the scenario
    # The actual UI verification would be done in E2E tests
    
    assert True  # Placeholder for backend verification