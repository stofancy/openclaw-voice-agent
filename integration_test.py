#!/usr/bin/env python3
"""
Integration test to verify end-to-end functionality.
"""
import asyncio
import websockets
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from voice_gateway.config import Config
from voice_gateway.webrtc_server import WebRTCServer

async def test_end_to_end():
    """Test end-to-end WebSocket connection and signaling."""
    # Create config for port 8765 (matching frontend)
    config = Config(host="localhost", port=8765)
    
    # Create and start server
    server = WebRTCServer(config)
    server_task = asyncio.create_task(server.start())
    
    # Wait for server to start
    await asyncio.sleep(1)
    
    try:
        # Simulate frontend connection
        async with websockets.connect("ws://localhost:8765") as websocket:
            print("✓ Connected to WebSocket server")
            
            # Receive ready message
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)
            print(f"✓ Received ready message: {data}")
            assert data["type"] == "ready"
            assert data["status"] == "ok"
            
            # Send offer (simulating frontend)
            offer = {
                "type": "offer",
                "sdp": "fake-sdp-offer-for-test"
            }
            await websocket.send(json.dumps(offer))
            print("✓ Sent offer")
            
            # Receive answer
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            answer_data = json.loads(response)
            print(f"✓ Received answer: {answer_data['type']}")
            assert answer_data["type"] == "answer"
            assert "sdp" in answer_data
            
            # Send ICE candidate
            ice_candidate = {
                "type": "ice-candidate",
                "candidate": "fake-candidate",
                "sdpMid": "0",
                "sdpMLineIndex": 0
            }
            await websocket.send(json.dumps(ice_candidate))
            print("✓ Sent ICE candidate")
            
            # Receive ICE candidate acknowledgment
            ice_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            ice_data = json.loads(ice_response)
            print(f"✓ Received ICE response: {ice_data['type']}")
            assert ice_data["type"] == "ice-candidate-received"
            
            print("\n🎉 All integration tests passed!")
            return True
            
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        return False
    finally:
        # Cleanup
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_end_to_end())
    sys.exit(0 if success else 1)