#!/usr/bin/env python3
"""
Test TTS service - 调用阿里百炼 TTS 并保存音频
"""
import os
import sys
import base64

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env
from pathlib import Path
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value

print(f"API Key: {os.environ.get('ALI_BAILIAN_API_KEY', 'NOT SET')[:10]}...")

from voice_gateway.tts_service import TTSService

async def test_tts():
    tts = TTSService(os.environ.get("ALI_BAILIAN_API_KEY", ""))
    
    text = "你好，我是语音助手。很高兴为你服务！"
    print(f"Synthesizing: {text}")
    
    audio_data = await tts.synthesize(text, voice="Cherry")
    
    if audio_data:
        print(f"TTS success! Audio size: {len(audio_data)} bytes")
        
        # Save to file
        audio_bytes = base64.b64decode(audio_data)
        with open("test_output.mp3", "wb") as f:
            f.write(audio_bytes)
        print("Saved to test_output.mp3")
    else:
        print("TTS failed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tts())
