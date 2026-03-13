"""
Speech-to-Text service using Alibaba Cloud paraformer-realtime via WebSocket
"""
import asyncio
import json
import base64
import websockets
from typing import Optional
import os


class STTService:
    """Alibaba Cloud paraformer-realtime STT service via WebSocket"""
    
    def __init__(self, api_key: str, ws_url: str = None):
        self.api_key = api_key
        self.ws_url = ws_url or os.getenv("BAILIAN_ASR_URL", "wss://dashscope.aliyuncs.com/api-ws/v1/realtime")
        self.model = os.getenv("BAILIAN_STT_MODEL", "paraformer-realtime")
        
    async def transcribe(self, audio_data: str) -> Optional[str]:
        """Transcribe audio data to text via WebSocket
        
        Args:
            audio_data: Base64 encoded audio data
            
        Returns:
            Transcribed text or None if failed
        """
        if not audio_data:
            return None
            
        try:
            # Build authentication header
            auth_header = base64.b64encode(f"api-key:{self.api_key}".encode()).decode()
            
            async with websockets.connect(
                self.ws_url,
                extra_headers={"Authorization": auth_header}
            ) as ws:
                # Send start task message
                start_msg = {
                    "model": self.model,
                    "task": "asr",
                    "input": {
                        "format": "wav",
                        "rate": 16000,
                        "channels": 1
                    },
                    "parameters": {
                        "language_hints": ["zh", "en"]
                    }
                }
                await ws.send(json.dumps(start_msg))
                
                # Decode and send audio
                audio_bytes = base64.b64decode(audio_data)
                
                # Send audio in chunks
                chunk_size = 3200  # 100ms at 16kHz
                for i in range(0, len(audio_bytes), chunk_size):
                    chunk = audio_bytes[i:i+chunk_size]
                    audio_msg = {
                        "task": "asr",
                        "input": {
                            "audio": base64.b64encode(chunk).decode()
                        }
                    }
                    await ws.send(json.dumps(audio_msg))
                    await asyncio.sleep(0.1)
                
                # Send stop message
                stop_msg = {
                    "task": "asr",
                    "input": {}
                }
                await ws.send(json.dumps(stop_msg))
                
                # Receive transcription result
                async for msg in ws:
                    data = json.loads(msg)
                    if data.get("type") == "result":
                        if "output" in data and "text" in data["output"]:
                            return data["output"]["text"]
                    elif data.get("type") == "done":
                        break
                        
        except Exception as e:
            print(f"STT WebSocket error: {e}")
            return None
        
        return None
