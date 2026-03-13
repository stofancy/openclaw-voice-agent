"""
Text-to-Speech service using Alibaba Cloud qwen-tts
"""
import aiohttp
import base64
import os
from typing import Optional


class TTSService:
    """Alibaba Cloud TTS service"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/generation"
        
    async def synthesize(self, text: str, voice: str = "xiaoyun") -> Optional[str]:
        """Synthesize text to speech
        
        Args:
            text: Text to synthesize
            voice: Voice name (default: xiaoyun)
            
        Returns:
            Base64 encoded audio data or None if failed
        """
        if not text:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "qwen-tts",
                "input": {
                    "text": text
                },
                "parameters": {
                    "voice": voice,
                    "format": "mp3",
                    "sample_rate": 32000
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
                        # Parse the audio data from response
                        if 'output' in result and 'audio' in result['output']:
                            return result['output']['audio']
                        elif 'data' in result:
                            return result['data']
                    else:
                        print(f"TTS API error: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"TTS error: {e}")
            return None
        
        return None
