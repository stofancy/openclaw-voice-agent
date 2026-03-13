import asyncio
import websockets

async def test_websocket():
    try:
        async with websockets.connect('ws://localhost:8080') as websocket:
            print("✅ Successfully connected to WebSocket server!")
            # Send a test message
            await websocket.send('{"type": "test"}')
            # Wait for response
            response = await websocket.recv()
            print(f"Received response: {response}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())