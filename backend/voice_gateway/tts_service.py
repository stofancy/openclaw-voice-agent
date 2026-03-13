"""
Text-to-Speech service using Alibaba Cloud dashscope SDK
"""
import dashscope
from dashscope.audio.tts import SpeechSynthesizer
from typing import Optional
import os


class TTSService:
    """Alibaba Cloud TTS service using dashscope SDK"""
    
    def __init__(self, api_key: str):
        dashscope.api_key = api_key
        self.model = "tts-199"
        
    async def synthesize(self, text: str, voice: str = "xiaoyun") -> Optional[str]:
        """Synthesize text to speech
        
        Args:
            text: Text to synthesize
            voice: Voice name
            
        Returns:
            Base64 encoded audio data or None if failed
        """
        if not text:
            return None
            
        try:
            # Use synchronous call in async context
            import asyncio
            loop = asyncio.get_event_loop()
            
            result = await loop.run_in_executor(
                None,
                lambda: SpeechSynthesizer.call(
                    model=self.model,
                    text=text,
                    format="mp3",
                    sample_rate=32000,
                    voice=voice
                )
            )
            
            if result.get_audio_data():
                import base64
                return base64.b64encode(result.get_audio_data()).decode('utf-8')
            else:
                print(f"TTS result: {result}")
                return None
                
        except Exception as e:
            print(f"TTS error: {e}")
            return None
        
        return None
