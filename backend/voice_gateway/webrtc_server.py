"""
WebRTC server implementation for Voice Gateway.
"""
import asyncio
import json
import websockets
from typing import Optional, Dict, Set
from .config import Config


class WebRTCServer:
    """WebRTC signaling and media handling."""
    
    def __init__(self, config: Config):
        self.config = config
        self.running = False
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.turn_counter = 0  # Track conversation turns
        
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        """Handle individual client connections."""
        # Get the path from the websocket
        path = getattr(websocket, 'path', '/')
        self.clients.add(websocket)
        try:
            # Reset turn counter for new client
            self.turn_counter = 0
            
            # Send ready message to client
            await websocket.send(json.dumps({"type": "ready", "status": "ok"}))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                except Exception as e:
                    print(f"Error handling message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": f"Server error: {str(e)}"
                    }))
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        finally:
            self.clients.discard(websocket)
    
    async def handle_message(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        """Handle different types of signaling messages."""
        message_type = data.get("type")
        
        if message_type == "offer":
            # Handle SDP offer from client
            await self.handle_offer(websocket, data)
        elif message_type == "answer":
            # Handle SDP answer from client (not typically needed for this use case)
            await self.handle_answer(websocket, data)
        elif message_type == "ice-candidate":
            # Handle ICE candidate from client
            await self.handle_ice_candidate(websocket, data)
        elif message_type == "audio-data":
            # Handle audio data from client (for Echo functionality)
            await self.handle_audio_data(websocket, data)
        elif message_type == "ping":
            # Simple ping-pong for connection health
            await websocket.send(json.dumps({"type": "pong"}))
        else:
            print(f"Unknown message type: {message_type}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }))
    
    async def handle_offer(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        """Handle SDP offer from client and send back answer."""
        sdp = data.get("sdp")
        if not sdp:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Missing SDP in offer"
            }))
            return
        
        # In a real implementation, we would create an actual WebRTC peer connection
        # For this demo, we'll simulate a successful answer
        answer_sdp = {
            "type": "answer",
            "sdp": "v=0\r\n" +
                   "o=- 1234567890 2 IN IP4 127.0.0.1\r\n" +
                   "s=Voice Gateway Answer\r\n" +
                   "t=0 0\r\n" +
                   "m=audio 9 UDP/TLS/RTP/SAVPF 111\r\n" +
                   "c=IN IP4 127.0.0.1\r\n" +
                   "a=rtcp:9 IN IP4 127.0.0.1\r\n" +
                   "a=ice-ufrag:answer\r\n" +
                   "a=ice-pwd:answerpassword\r\n" +
                   "a=fingerprint:sha-256 AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA\r\n" +
                   "a=setup:active\r\n" +
                   "a=mid:0\r\n" +
                   "a=sendrecv\r\n" +
                   "a=rtpmap:111 opus/48000/2\r\n" +
                   "a=rtcp-fb:111 transport-cc\r\n" +
                   "a=fmtp:111 minptime=10;useinbandfec=1\r\n"
        }
        await websocket.send(json.dumps(answer_sdp))
    
    async def handle_answer(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        """Handle SDP answer from client."""
        # For this use case, we don't expect answers from clients
        # since the server is the answering party
        pass
    
    async def handle_ice_candidate(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        """Handle ICE candidate from client."""
        candidate = data.get("candidate")
        sdp_mid = data.get("sdpMid")
        sdp_mline_index = data.get("sdpMLineIndex")
        
        if not candidate:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Missing candidate in ICE candidate message"
            }))
            return
        
        # In a real implementation, we would add this candidate to our peer connection
        # For this demo, we'll just acknowledge receipt
        await websocket.send(json.dumps({
            "type": "ice-candidate-received",
            "candidate": candidate,
            "sdpMid": sdp_mid,
            "sdpMLineIndex": sdp_mline_index
        }))
    
    async def handle_audio_data(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        """Handle audio data from client and process for multi-turn dialogue."""
        audio_data = data.get("audio")
        if not audio_data:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Missing audio data"
            }))
            return
        
        # Increment turn counter for each audio message
        current_turn = self.turn_counter
        self.turn_counter += 1
        
        # Echo the audio data back to the client (simulating AI response)
        echo_response = {
            "type": "audio-response",
            "audio": audio_data,
            "timestamp": data.get("timestamp", 0),
            "turn_id": current_turn,
            "is_new_turn": True
        }
        await websocket.send(json.dumps(echo_response))
    
    async def start(self):
        """Start the WebRTC server."""
        self.running = True
        host = self.config.host
        port = self.config.port
        
        print(f"WebRTC signaling server starting on {host}:{port}")
        
        # Start WebSocket server
        self.websocket_server = await websockets.serve(
            self.handle_client,
            host,
            port,
            ping_interval=20,
            ping_timeout=10
        )
        
        print(f"WebRTC signaling server started on ws://{host}:{port}")
        
    async def stop(self):
        """Stop the WebRTC server."""
        self.running = False
        if hasattr(self, 'websocket_server'):
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        print("WebRTC signaling server stopped")