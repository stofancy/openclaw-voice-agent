#!/usr/bin/env python3
"""
Test for US-05: Receive AI reply and play audio.
"""
import asyncio
import websockets
import json
import sys
import os
import base64

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from voice_gateway.config import Config
from voice_gateway.webrtc_server import WebRTCServer

async def test_audio_echo():
    """Test audio echo functionality."""
    # Create config for port 8765 (matching frontend)
    config = Config(host="localhost", port=8766)  # Use different port to avoid conflict
    
    # Create and start server
    server = WebRTCServer(config)
    server_task = asyncio.create_task(server.start())
    
    # Wait for server to start
    await asyncio.sleep(1)
    
    try:
        # Simulate frontend connection
        async with websockets.connect("ws://localhost:8766") as websocket:
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
            
            # Test audio echo
            fake_audio_data = base64.b64encode(b"fake-audio-data-for-testing").decode('utf-8')
            audio_message = {
                "type": "audio-data",
                "audio": fake_audio_data,
                "format": "opus"
            }
            await websocket.send(json.dumps(audio_message))
            print("✓ Sent audio data")
            
            # Receive echoed audio
            echo_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            echo_data = json.loads(echo_response)
            print(f"✓ Received echo response: {echo_data['type']}")
            assert echo_data["type"] == "audio-response"
            assert "audio" in echo_data
            assert echo_data["audio"] == fake_audio_data
            
            print("\n🎉 US-05 Audio Echo test passed!")
            return True
            
    except Exception as e:
        print(f"\n❌ US-05 Audio Echo test failed: {e}")
        return False
    finally:
        # Cleanup
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_audio_echo())
    sys.exit(0 if success else 1)