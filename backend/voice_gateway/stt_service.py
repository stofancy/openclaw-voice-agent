"""
Speech-to-Text service using Alibaba Cloud Qwen3-ASR-Flash-Realtime
Based on official example: https://help.aliyun.com/document_detail/2959876.html
"""
import os
import json
import base64
import asyncio
import threading
import websocket as ws_client
from typing import Optional


class STTService:
    """Alibaba Cloud Qwen3-ASR-Flash-Realtime STT service"""
    
    def __init__(self, api_key: str, ws_url: str = None):
        self.api_key = api_key
        self.ws_url = ws_url or os.getenv("BAILIAN_ASR_URL", "wss://dashscope.aliyuncs.com/api-ws/v1/realtime")
        self.model = os.getenv("BAILIAN_STT_MODEL", "qwen3-asr-flash-realtime-2026-02-10")
        
    async def transcribe(self, audio_data: str) -> Optional[str]:
        """Transcribe audio data to text
        
        Args:
            audio_data: Base64 encoded audio data
            
        Returns:
            Transcribed text or None if failed
        """
        if not audio_data:
            return None
            
        # Run in thread since websocket-client is synchronous
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._transcribe_sync, audio_data)
    
    def _transcribe_sync(self, audio_data: str) -> Optional[str]:
        """Synchronous transcription using websocket-client"""
        from queue import Queue
        result_queue = Queue()
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                event_type = data.get("type", "")
                print(f"STT received: {event_type}")
                
                # Check for transcription result in conversation.item events
                if event_type == "conversation.item.input_audio_transcription.text":
                    transcript = data.get("transcript", "")
                    if transcript:
                        result_queue.put(transcript)
                        
                # Also check for done event
                elif event_type == "response.audio_transcript.done":
                    transcript = data.get("transcript", {}).get("text", "")
                    if transcript:
                        result_queue.put(transcript)
                        
            except Exception as e:
                print(f"STT parse error: {e}")
        
        def on_error(ws, error):
            print(f"STT WebSocket error: {error}")
            # Continue waiting for messages even after error
        
        def on_close(ws, close_status_code, close_msg):
            print(f"STT closed: {close_status_code} - {close_msg}")
        
        def on_open(ws):
            print("STT WebSocket opened")
            
            # Send session update with VAD
            session_event = {
                "event_id": "event_session_001",
                "type": "session.update",
                "session": {
                    "modalities": ["text"],
                    "input_audio_format": "pcm",
                    "sample_rate": 16000,
                    "input_audio_transcription": {
                        "language": "zh"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.2,
                        "silence_duration_ms": 800
                    }
                }
            }
            ws.send(json.dumps(session_event))
            
            # Send audio data
            try:
                audio_bytes = base64.b64decode(audio_data)
                
                # Send in chunks (3200 bytes = 100ms at 16kHz)
                chunk_size = 3200
                for i in range(0, len(audio_bytes), chunk_size):
                    chunk = audio_bytes[i:i+chunk_size]
                    encoded = base64.b64encode(chunk).decode('utf-8')
                    
                    audio_event = {
                        "event_id": f"event_audio_{i}",
                        "type": "input_audio_buffer.append",
                        "audio": encoded
                    }
                    ws.send(json.dumps(audio_event))
                
                # Commit the audio buffer
                commit_event = {
                    "event_id": "event_commit_001",
                    "type": "input_audio_buffer.commit"
                }
                ws.send(json.dumps(commit_event))
                
            except Exception as e:
                print(f"STT send error: {e}")
        
        # Create WebSocket app
        url = f"{self.ws_url}?model={self.model}"
        ws = ws_client.WebSocketApp(
            url,
            header=[
                f"Authorization: Bearer {self.api_key}",
                "OpenAI-Beta: realtime=v1"
            ],
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run in background thread
        def run_ws():
            ws.run_forever()
        
        thread = threading.Thread(target=run_ws, daemon=True)
        thread.start()
        
        # Wait for result with timeout
        try:
            result = result_queue.get(timeout=30)
            ws.close()
            return result
        except:
            print("STT timeout")
            ws.close()
            return None
