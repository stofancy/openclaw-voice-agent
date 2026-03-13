"""
Text-to-Speech service using Alibaba Cloud sambert-realtime via WebSocket
"""
import asyncio
import json
import base64
import websockets
from typing import Optional
import os


class TTSService:
    """Alibaba Cloud sambert-realtime TTS service via WebSocket"""
    
    def __init__(self, api_key: str, ws_url: str = None):
        self.api_key = api_key
        self.ws_url = ws_url or os.getenv("BAILIAN_TTS_URL", "wss://dashscope.aliyuncs.com/api-ws/v1/realtime")
        self.model = os.getenv("BAILIAN_TTS_MODEL", "sambert-realtime")
        
    async def synthesize(self, text: str, voice: str = "xiaoyun") -> Optional[str]:
        """Synthesize text to speech via WebSocket
        
        Args:
            text: Text to synthesize
            voice: Voice name
            
        Returns:
            Base64 encoded audio data or None if failed
        """
        if not text:
            return None
            
        try:
            # Build WebSocket URL with API key as query param
            ws_url_with_auth = f"{self.ws_url}?api-key={self.api_key}"
            
            audio_chunks = []
            
            async with websockets.connect(ws_url_with_auth) as ws:
                # Send start task message
                start_msg = {
                    "model": self.model,
                    "task": "tts",
                    "input": {
                        "text": text,
                        "voice": voice,
                        "format": "mp3",
                        "sample_rate": 32000
                    },
                    "parameters": {}
                }
                await ws.send(json.dumps(start_msg))
                
                # Receive audio chunks
                async for msg in ws:
                    data = json.loads(msg)
                    if data.get("type") == "audio":
                        if "output" in data and "audio" in data["output"]:
                            audio_chunks.append(data["output"]["audio"])
                    elif data.get("type") == "done":
                        break
                    elif data.get("type") == "error":
                        print(f"TTS error: {data.get('message')}")
                        break
                
                if audio_chunks:
                    return "".join(audio_chunks)
                        
        except Exception as e:
            print(f"TTS WebSocket error: {e}")
            return None
        
        return None
