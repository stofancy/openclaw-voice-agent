"""
Audio processor for handling audio streams and Echo functionality.
"""
import asyncio
import json
from typing import Dict, Optional
import websockets


class AudioProcessor:
    """Handles audio processing and Echo functionality."""
    
    def __init__(self):
        self.audio_buffers: Dict[str, bytearray] = {}
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        
    async def handle_audio_data(self, client_id: str, audio_data: bytes, websocket: websockets.WebSocketServerProtocol):
        """Handle incoming audio data and echo it back."""
        try:
            # Store client reference
            self.clients[client_id] = websocket
            
            # For Echo functionality, send the audio data back to the client
            # In a real implementation, this would be processed by an AI agent
            # For testing, we just echo it back with a small delay
            await asyncio.sleep(0.1)  # Small delay to simulate processing
            
            # Send audio data back as Echo
            if websocket.open:
                await websocket.send(audio_data)
                
        except Exception as e:
            print(f"Error processing audio data: {e}")
            if websocket.open:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Audio processing error: {str(e)}"
                }))
    
    def cleanup_client(self, client_id: str):
        """Clean up client resources."""
        if client_id in self.audio_buffers:
            del self.audio_buffers[client_id]
        if client_id in self.clients:
            del self.clients[client_id]