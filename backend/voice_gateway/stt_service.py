"""
Speech-to-Text service using Alibaba Cloud paraformer
"""
import dashscope
from dashscope.audio.asr import Transcription
import base64
import io
from typing import Optional
import os


class STTService:
    """Alibaba Cloud paraformer STT service"""
    
    def __init__(self, api_key: str):
        dashscope.api_key = api_key
        self.model = "paraformer-v1"
        
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
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Save to temporary file (required by dashscope API)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(audio_bytes)
                temp_file = f.name
            
            # Note: The transcription API requires file URLs, not local files
            # For a simple demo, we'll return a placeholder
            # In production, you'd upload to OSS and use the URL
            
            # Clean up temp file
            os.unlink(temp_file)
            
            # For now, return a placeholder since we can't easily get a file URL
            print("STT: Audio received, but file URL required for transcription API")
            return None
            
        except Exception as e:
            print(f"STT error: {e}")
            return None
        
        return None
