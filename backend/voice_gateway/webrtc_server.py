"""
WebRTC server implementation for Voice Gateway.
"""
import asyncio
import json
import websockets
import os
from typing import Optional, Dict, Set
from .config import Config
from .stt_service import STTService
from .agent_client import AgentClient
from .tts_service import TTSService


class WebRTCServer:
    """WebRTC signaling and media handling."""
    
    def __init__(self, config: Config):
        self.config = config
        self.running = False
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.turn_counter = 0  # Track conversation turns
        
        # Initialize services
        api_key = config.dashscope_api_key or os.getenv("ALI_BAILIAN_API_KEY", "")
        self.stt_service = STTService(api_key)
        self.agent_client = AgentClient()
        self.tts_service = TTSService(api_key)
        
        # Processing lock to prevent concurrent requests
        self._is_processing = False
        
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
        elif message_type == "text-message":
            # Handle text message from client (from Web Speech API)
            await self.handle_text_message(websocket, data)
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
        
        # Parse the offer SDP to understand what media streams are included
        lines = sdp.split('\r\n')
        media_lines = []
        for line in lines:
            if line.startswith('m='):
                media_lines.append(line)
        
        print(f"Offer contains {len(media_lines)} media lines: {media_lines}")
        
        # Build a matching answer SDP based on the offer
        # The answer must have the same number and order of m-lines as the offer
        import os
        
        # Generate proper ICE credentials (22-256 characters)
        ice_ufrag = os.urandom(4).hex()  # 8 characters
        ice_pwd = os.urandom(32).hex()   # 64 characters
        
        # Generate SDES crypto keys (30 bytes = 240 bits for AES-CM)
        sdes_key = os.urandom(30).hex()
        
        answer_lines = [
            "v=0",
            "o=- 1234567890 2 IN IP4 127.0.0.1",
            "s=Voice Gateway Answer",
            "t=0 0",
        ]
        
        # Generate m-lines to match the offer
        for i, mline in enumerate(media_lines):
            if mline.startswith('m=audio'):
                # Audio media line - use DTLS with real certificate
                answer_lines.append("m=audio 9 UDP/TLS/RTP/SAVPF 111")
                answer_lines.append("c=IN IP4 127.0.0.1")
                answer_lines.append("a=rtcp-mux")
                answer_lines.append(f"a=ice-ufrag:{ice_ufrag}")
                answer_lines.append(f"a=ice-pwd:{ice_pwd}")
                answer_lines.append("a=fingerprint:sha-256 36:CC:28:82:6E:95:58:43:48:7B:13:2B:CB:FD:B7:11:7D:C0:F1:69:92:9F:E6:33:4A:21:B3:D3:13:B8:AE:FF")
                answer_lines.append("a=setup:active")
                answer_lines.append(f"a=mid:{i}")
                answer_lines.append("a=sendrecv")
                answer_lines.append("a=rtpmap:111 opus/48000/2")
                answer_lines.append("a=rtcp-fb:111 transport-cc")
                answer_lines.append("a=fmtp:111 minptime=10;useinbandfec=1")
            elif mline.startswith('m=video'):
                # Video media line - reject it by setting port to 0
                # Extract the existing video fmtp and replace port with 0
                parts = mline.split()
                if len(parts) >= 2:
                    video_fmtp = ' '.join(parts[2:]) if len(parts) > 2 else ''
                    answer_lines.append(f"m=video 0 RTP/SAVPF 96")
                    answer_lines.append("c=IN IP4 0.0.0.0")
                    answer_lines.append("a=rtcp-mux")
                    answer_lines.append(f"a=ice-ufrag:{ice_ufrag}")
                    answer_lines.append(f"a=ice-pwd:{ice_pwd}")
                    answer_lines.append("a=setup:active")
                    answer_lines.append(f"a=mid:{i}")
                    answer_lines.append("a=inactive")
                    answer_lines.append("a=rtpmap:96 VP8/90000")
            else:
                # Unknown media type - reject it
                answer_lines.append("m=application 0 UDP/DTLS/SCTP webrtc-datachannel")
                answer_lines.append("c=IN IP4 0.0.0.0")
                answer_lines.append("a=rtcp-mux")
                answer_lines.append(f"a=ice-ufrag:{ice_ufrag}")
                answer_lines.append(f"a=ice-pwd:{ice_pwd}")
                answer_lines.append("a=setup:active")
                answer_lines.append(f"a=mid:{i}")
                answer_lines.append("a=sendrecv")
        
        answer_sdp_str = '\r\n'.join(answer_lines) + '\r\n'
        
        answer_sdp = {
            "type": "answer",
            "sdp": answer_sdp_str
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
        
        # Prevent concurrent processing
        if self._is_processing:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Still processing previous request"
            }))
            return
        
        self._is_processing = True
        current_turn = self.turn_counter
        self.turn_counter += 1
        
        try:
            # Send thinking status
            await websocket.send(json.dumps({
                "type": "status",
                "status": "processing",
                "message": "正在识别..."
            }))
            
            # Step 1: STT - Speech to Text
            transcribed_text = await self.stt_service.transcribe(audio_data)
            
            if not transcribed_text:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "语音识别失败，请重试"
                }))
                return
                
            print(f"[Turn {current_turn}] User said: {transcribed_text}")
            
            # Send thinking status
            await websocket.send(json.dumps({
                "type": "status",
                "status": "thinking",
                "message": "正在思考..."
            }))
            
            # Step 2: Agent - Call travel-agency agent
            agent_response = await self.agent_client.process_message(transcribed_text)
            
            if not agent_response:
                agent_response = "抱歉，我暂时无法处理您的请求。"
                
            print(f"[Turn {current_turn}] Agent response: {agent_response}")
            
            # Send thinking status
            await websocket.send(json.dumps({
                "type": "status",
                "status": "speaking",
                "message": "正在生成语音..."
            }))
            
            # Step 3: TTS - Text to Speech
            audio_response = await self.tts_service.synthesize(agent_response)
            
            if not audio_response:
                # Fallback: send text response
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "语音合成失败"
                }))
                return
                
            # Send the audio response
            response_msg = {
                "type": "audio-response",
                "audio": audio_response,
                "text": agent_response,  # Include text for display
                "timestamp": data.get("timestamp", 0),
                "turn_id": current_turn,
                "is_new_turn": True
            }
            await websocket.send(json.dumps(response_msg))
            
            # Send completion status
            await websocket.send(json.dumps({
                "type": "status",
                "status": "idle",
                "message": ""
            }))
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"处理出错: {str(e)}"
            }))
        finally:
            self._is_processing = False
    
    async def handle_text_message(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        """Handle text message from client (Web Speech API)."""
        text = data.get("text")
        if not text:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Missing text"
            }))
            return
        
        # Prevent concurrent processing
        if self._is_processing:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Still processing previous request"
            }))
            return
        
        self._is_processing = True
        current_turn = self.turn_counter
        self.turn_counter += 1
        
        try:
            print(f"[Turn {current_turn}] User said (text): {text}")
            
            # Send thinking status
            await websocket.send(json.dumps({
                "type": "status",
                "status": "thinking",
                "message": "正在思考..."
            }))
            
            # Call Agent
            agent_response = await self.agent_client.process_message(text)
            
            if not agent_response:
                agent_response = "抱歉，我暂时无法处理您的请求。"
                
            print(f"[Turn {current_turn}] Agent response: {agent_response}")
            
            # Send thinking status
            await websocket.send(json.dumps({
                "type": "status",
                "status": "speaking",
                "message": "正在生成语音..."
            }))
            
            # TTS
            audio_response = await self.tts_service.synthesize(agent_response)
            
            if not audio_response:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "语音合成失败"
                }))
                return
                
            # Send the audio response
            response_msg = {
                "type": "audio-response",
                "audio": audio_response,
                "text": agent_response,
                "timestamp": data.get("timestamp", 0),
                "turn_id": current_turn,
                "is_new_turn": True
            }
            await websocket.send(json.dumps(response_msg))
            
            # Send completion status
            await websocket.send(json.dumps({
                "type": "status",
                "status": "idle",
                "message": ""
            }))
            
        except Exception as e:
            print(f"Error processing text: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"处理出错: {str(e)}"
            }))
        finally:
            self._is_processing = False
    
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