"""
Integration test for US-01: Auto-connect functionality.
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import websockets
from backend.voice_gateway.config import Config
from backend.voice_gateway.webrtc_server import WebRTCServer

async def test_backend_server():
    """Test that the backend WebSocket server can be started and accepts connections."""
    # Create test configuration
    config = Config(
        WS_HOST="localhost",
        WS_PORT=8766,  # Use different port to avoid conflicts
        DASHSCOPE_API_KEY="test-key"
    )
    
    # Create and start server
    server = WebRTCServer(config)
    
    # Start server in background
    server_task = asyncio.create_task(server.start())
    
    # Give server time to start
    await asyncio.sleep(1)
    
    try:
        # Connect client
        async with websockets.connect("ws://localhost:8766") as websocket:
            # Receive ready message
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"Received message: {message}")
            
            # Parse JSON
            import json
            data = json.loads(message)
            
            assert data["type"] == "ready"
            print("✓ Backend server test passed")
            
    except Exception as e:
        print(f"✗ Backend server test failed: {e}")
        raise
    finally:
        # Cleanup
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(test_backend_server())