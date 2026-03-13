"""
Speech-to-Text service using Alibaba Cloud paraformer-realtime-v2
"""
import asyncio
import base64
import aiohttp
from typing import Optional
import os


class STTService:
    """Alibaba Cloud paraformer-realtime-v2 STT service"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
        
    async def transcribe(self, audio_data: str) -> Optional[str]:
        """Transcribe audio data to text
        
        Args:
            audio_data: Base64 encoded audio data
            
        Returns:
            Transcribed text or None if failed
        """
        if not audio_data:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "paraformer-realtime-v2",
                "input": {
                    "audio": audio_data
                },
                "parameters": {
                    "language_hints": ["zh", "en"]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url, 
                    headers=headers, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Parse the transcription result
                        if 'output' in result and 'text' in result['output']:
                            return result['output']['text']
                        elif 'output' in result and 'transcription' in result['output']:
                            return result['output']['transcription']
                    else:
                        print(f"STT API error: {response.status}")
                        return None
        except Exception as e:
            print(f"STT error: {e}")
            return None
        
        return None
