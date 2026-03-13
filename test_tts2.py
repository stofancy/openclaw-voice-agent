#!/usr/bin/env python3
"""
Test TTS service - 直接使用 SDK
"""
import os
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value

print(f"API Key: {os.environ.get('ALI_BAILIAN_API_KEY', 'NOT SET')[:10]}...")

import dashscope
dashscope.api_key = os.environ.get("ALI_BAILIAN_API_KEY", "")

from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime, QwenTtsRealtimeCallback, AudioFormat
import threading

class TTSCallback(QwenTtsRealtimeCallback):
    def __init__(self):
        self.complete_event = threading.Event()
        self.audio_chunks = []
        
    def on_open(self) -> None:
        print('TTS connection opened')
        
    def on_close(self, close_status_code, close_msg) -> None:
        print(f'TTS connection closed: {close_status_code} - {close_msg}')
        
    def on_event(self, response: str) -> None:
        import json
        try:
            data = json.loads(response) if isinstance(response, str) else response
            event_type = data.get('type', '')
            print(f'TTS event: {event_type}')
            
            if 'response.audio.delta' == event_type:
                audio_b64 = data.get('delta', '')
                if audio_b64:
                    self.audio_chunks.append(audio_b64)
            elif 'session.finished' == event_type:
                print('TTS session finished')
                self.complete_event.set()
        except Exception as e:
            print(f'TTS callback error: {e}')
    
    def wait_for_finished(self, timeout=30):
        return self.complete_event.wait(timeout)

async def test():
    callback = TTSCallback()
    
    tts = QwenTtsRealtime(
        model='qwen3-tts-flash-realtime',
        callback=callback,
    )
    
    try:
        print("Connecting...")
        tts.connect()
        
        print("Updating session...")
        tts.update_session(
            voice='Cherry',
            response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
            mode='server_commit'
        )
        
        print("Sending text...")
        tts.append_text("你好，我是语音助手！")
        tts.finish()
        
        print("Waiting for completion...")
        callback.wait_for_finished(30)
        
        if callback.audio_chunks:
            print(f"Got {len(callback.audio_chunks)} audio chunks")
            # Save to file
            audio_data = ''.join(callback.audio_chunks)
            audio_bytes = base64.b64decode(audio_data)
            with open("test_output.pcm", "wb") as f:
                f.write(audio_bytes)
            print("Saved to test_output.pcm")
        else:
            print("No audio chunks received!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            tts.close()
        except:
            pass

if __name__ == "__main__":
    import asyncio
    import base64
    asyncio.run(test())
