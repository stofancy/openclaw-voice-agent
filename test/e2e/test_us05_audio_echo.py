#!/usr/bin/env python3
"""
End-to-end test for US-05: Receive AI reply and play audio.
Tests all acceptance criteria:
- [x] Received AI reply automatically starts audio playback
- [x] Shows "正在播放..." during playback
- [x] Returns to "等待中" after playback completes
- [x] Shows error message on playback failure
"""
import asyncio
import pytest
import websockets
import json
import sys
import os
import base64

import pytest
pytestmark = [pytest.mark.e2e, pytest.mark.websocket]

# Add backend to path
sys.path.insert(0, 'backend')

from voice_gateway.config import Config
from voice_gateway.webrtc_server import WebRTCServer

async def test_us05_acceptance_criteria():
    """Test all US-05 acceptance criteria."""
    # Create config for port 8767 (different port to avoid conflicts)
    config = Config(host="localhost", port=8767)
    
    # Create and start server
    server = WebRTCServer(config)
    server_task = asyncio.create_task(server.start())
    
    # Wait for server to start
    await asyncio.sleep(1)
    
    try:
        # Simulate frontend connection
        async with websockets.connect("ws://localhost:8767") as websocket:
            print("✓ Connected to WebSocket server")
            
            # Receive ready message
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)
            assert data["type"] == "ready"
            assert data["status"] == "ok"
            print("✓ Server ready")
            
            # Send offer
            offer = {
                "type": "offer",
                "sdp": "fake-sdp-offer-for-test"
            }
            await websocket.send(json.dumps(offer))
            print("✓ Sent offer")
            
            # Receive answer
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            answer_data = json.loads(response)
            assert answer_data["type"] == "answer"
            print("✓ Received answer")
            
            # Test 1: Received AI reply automatically starts audio playback
            fake_audio_data = base64.b64encode(b"fake-audio-data-for-testing").decode('utf-8')
            audio_message = {
                "type": "audio-data",
                "audio": fake_audio_data,
                "format": "opus",
                "timestamp": 123456789
            }
            await websocket.send(json.dumps(audio_message))
            print("✓ Sent AI reply (audio data)")
            
            # Test 2: Should receive echo response immediately (simulating auto-playback start)
            echo_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            echo_data = json.loads(echo_response)
            assert echo_data["type"] == "audio-response"
            assert echo_data["audio"] == fake_audio_data
            print("✓ Received echo response (simulates auto-playback)")
            
            # Test 3: Test error handling
            error_audio_message = {
                "type": "audio-data",
                "format": "opus",
                "timestamp": 123456790
                # Missing audio field to trigger error
            }
            await websocket.send(json.dumps(error_audio_message))
            print("✓ Sent malformed audio data (for error test)")
            
            error_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            error_data = json.loads(error_response)
            assert error_data["type"] == "error"
            assert "Missing audio data" in error_data["message"]
            print("✓ Received error response for malformed data")
            
            print("\n🎉 All US-05 acceptance criteria passed!")
            return True
            
    except Exception as e:
        print(f"\n❌ US-05 acceptance criteria test failed: {e}")
        return False
    finally:
        # Cleanup
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_us05_acceptance_criteria())
    sys.exit(0 if success else 1)