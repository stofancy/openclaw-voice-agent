#!/usr/bin/env python3
"""
Test script to verify WebSocket server functionality.
"""
import asyncio
import websockets
import json

async def test_websocket():
    """Test basic WebSocket connection."""
    try:
        async with websockets.connect('ws://localhost:8080') as websocket:
            print("Connected to WebSocket server")
            
            # Send a test message
            await websocket.send(json.dumps({"type": "test"}))
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Test signaling messages
            offer_msg = {
                "type": "offer",
                "sdp": "test-sdp-offer"
            }
            await websocket.send(json.dumps(offer_msg))
            response = await websocket.recv()
            print(f"Offer response: {response}")
            
            return True
    except Exception as e:
        print(f"WebSocket test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_websocket())
    if success:
        print("WebSocket test passed!")
    else:
        print("WebSocket test failed!")