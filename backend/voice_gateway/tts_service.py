"""
Text-to-Speech service using Alibaba Cloud Qwen3-TTS-Flash-Realtime
Based on official example
"""
import os
import asyncio
import base64
import time
import dashscope
from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime, QwenTtsRealtimeCallback
from typing import Optional
import threading


class TTSCallback(QwenTtsRealtimeCallback):
    """Callback for TTS events"""
    
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
            
            if 'response.audio.delta' == event_type:
                # Audio chunk received
                audio_b64 = data.get('delta', '')
                if audio_b64:
                    self.audio_chunks.append(audio_b64)
                    
            elif 'response.done' == event_type:
                print(f'TTS response done')
                
            elif 'session.finished' == event_type:
                print('TTS session finished')
                self.complete_event.set()
                
        except Exception as e:
            print(f'TTS callback error: {e}')
    
    def wait_for_finished(self, timeout=30):
        return self.complete_event.wait(timeout)


class TTSService:
    """Alibaba Cloud Qwen3-TTS-Flash-Realtime TTS service"""
    
    def __init__(self, api_key: str):
        dashscope.api_key = api_key
        self.model = os.getenv("BAILIAN_TTS_MODEL", "Qwen3-TTS-Flash-Realtime")
        
    async def synthesize(self, text: str, voice: str = "Cherry") -> Optional[str]:
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
            # Run in executor since TTS SDK is sync
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._synthesize_sync, text, voice)
            
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    def _synthesize_sync(self, text: str, voice: str) -> Optional[str]:
        """Synchronous TTS synthesis"""
        from dashscope.audio.qwen_tts_realtime import AudioFormat
        
        callback = TTSCallback()
        
        tts = QwenTtsRealtime(
            model=self.model,
            callback=callback,
        )
        
        try:
            # Connect
            tts.connect()
            
            # Update session
            tts.update_session(
                voice=voice,
                response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
                mode='server_commit'
            )
            
            # Append text and finish
            tts.append_text(text)
            tts.finish()
            
            # Wait for completion
            callback.wait_for_finished(30)
            
            # Combine audio chunks
            if callback.audio_chunks:
                return ''.join(callback.audio_chunks)
            else:
                print("No audio chunks received")
                return None
                
        except Exception as e:
            print(f"TTS synthesis error: {e}")
            return None
        finally:
            try:
                tts.close()
            except:
                pass
