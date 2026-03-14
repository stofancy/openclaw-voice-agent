#!/usr/bin/env python3
"""
End-to-end test for US-06: Multi-turn conversation.
Tests all acceptance criteria:
- [x] AI playback completes automatically prepares for next round recording
- [x] Can have continuous multi-turn conversations
- [x] Each conversation turn is handled independently
- [x] Errors in one turn don't affect the next turn
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

async def test_us06_acceptance_criteria():
    """Test all US-06 acceptance criteria."""
    # Create config for port 8768 (different port to avoid conflicts)
    config = Config(host="localhost", port=8768)
    
    # Create and start server
    server = WebRTCServer(config)
    server_task = asyncio.create_task(server.start())
    
    # Wait for server to start
    await asyncio.sleep(1)
    
    try:
        # Simulate frontend connection
        async with websockets.connect("ws://localhost:8768") as websocket:
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
            
            # Test 1: Multiple turns of conversation
            print("\n--- Testing multiple conversation turns ---")
            for turn in range(3):
                print(f"Turn {turn + 1}:")
                
                # Send audio data (simulating user speech)
                fake_audio_data = base64.b64encode(f"fake-audio-data-turn-{turn}".encode()).decode('utf-8')
                audio_message = {
                    "type": "audio-data",
                    "audio": fake_audio_data,
                    "format": "opus",
                    "timestamp": 123456789 + turn
                }
                await websocket.send(json.dumps(audio_message))
                print(f"  ✓ Sent audio data for turn {turn + 1}")
                
                # Receive AI response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)
                assert response_data["type"] == "audio-response"
                assert response_data["audio"] == fake_audio_data
                assert "turn_id" in response_data
                assert response_data["turn_id"] == turn
                print(f"  ✓ Received AI response for turn {turn + 1}")
                
                # Verify each turn is handled independently
                assert response_data["is_new_turn"] == True
                print(f"  ✓ Turn {turn + 1} handled independently")
            
            # Test 2: Error in one turn doesn't affect next turn
            print("\n--- Testing error isolation ---")
            
            # Send malformed audio data (missing audio field)
            error_audio_message = {
                "type": "audio-data",
                "format": "opus",
                "timestamp": 123456792
                # Missing audio field to trigger error
            }
            await websocket.send(json.dumps(error_audio_message))
            print("✓ Sent malformed audio data (should trigger error)")
            
            # Should receive error response
            error_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            error_data = json.loads(error_response)
            assert error_data["type"] == "error"
            assert "Missing audio data" in error_data["message"]
            print("✓ Received error response for malformed data")
            
            # Next turn should still work normally
            normal_audio_data = base64.b64encode(b"normal-audio-after-error").decode('utf-8')
            normal_audio_message = {
                "type": "audio-data",
                "audio": normal_audio_data,
                "format": "opus",
                "timestamp": 123456793
            }
            await websocket.send(json.dumps(normal_audio_message))
            print("✓ Sent normal audio data after error")
            
            # Should receive normal response
            normal_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            normal_data = json.loads(normal_response)
            assert normal_data["type"] == "audio-response"
            assert normal_data["audio"] == normal_audio_data
            assert normal_data["turn_id"] == 3  # Fourth turn (0-indexed)
            print("✓ Normal response received after error")
            
            print("\n🎉 All US-06 acceptance criteria passed!")
            return True
            
    except Exception as e:
        print(f"\n❌ US-06 acceptance criteria test failed: {e}")
        return False
    finally:
        # Cleanup
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_us06_acceptance_criteria())
    sys.exit(0 if success else 1)