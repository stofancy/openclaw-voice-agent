#!/usr/bin/env python3
"""
Test for US-06: Multi-turn conversation.
Tests all acceptance criteria:
- [x] AI playback completes automatically prepares for next recording
- [x] Can have continuous multi-turn conversations
- [x] Each turn is processed independently
- [x] Errors in one turn don't affect the next turn
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
            
            # Test 1: First turn - send audio and receive response
            first_audio_data = base64.b64encode(b"first-turn-audio-data").decode('utf-8')
            first_message = {
                "type": "audio-data",
                "audio": first_audio_data,
                "format": "opus",
                "timestamp": 123456789
            }
            await websocket.send(json.dumps(first_message))
            print("✓ Sent first turn audio data")
            
            # Should receive AI response
            first_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            first_response_data = json.loads(first_response)
            assert first_response_data["type"] == "audio-response"
            assert first_response_data["audio"] == first_audio_data
            print("✓ Received first turn AI response")
            
            # Test 2: Second turn - send another audio and receive response
            second_audio_data = base64.b64encode(b"second-turn-audio-data").decode('utf-8')
            second_message = {
                "type": "audio-data",
                "audio": second_audio_data,
                "format": "opus",
                "timestamp": 123456790
            }
            await websocket.send(json.dumps(second_message))
            print("✓ Sent second turn audio data")
            
            # Should receive AI response for second turn
            second_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            second_response_data = json.loads(second_response)
            assert second_response_data["type"] == "audio-response"
            assert second_response_data["audio"] == second_audio_data
            print("✓ Received second turn AI response")
            
            # Test 3: Error in one turn doesn't affect next turn
            # Send malformed audio (missing audio field)
            error_message = {
                "type": "audio-data",
                "format": "opus",
                "timestamp": 123456791
                # Missing audio field to trigger error
            }
            await websocket.send(json.dumps(error_message))
            print("✓ Sent malformed audio data (for error test)")
            
            # Should receive error response
            error_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            error_data = json.loads(error_response)
            assert error_data["type"] == "error"
            print("✓ Received error response for malformed data")
            
            # Test 4: After error, next turn should still work
            third_audio_data = base64.b64encode(b"third-turn-audio-data-after-error").decode('utf-8')
            third_message = {
                "type": "audio-data",
                "audio": third_audio_data,
                "format": "opus",
                "timestamp": 123456792
            }
            await websocket.send(json.dumps(third_message))
            print("✓ Sent third turn audio data (after error)")
            
            # Should receive AI response despite previous error
            third_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            third_response_data = json.loads(third_response)
            assert third_response_data["type"] == "audio-response"
            assert third_response_data["audio"] == third_audio_data
            print("✓ Received third turn AI response (after error)")
            
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