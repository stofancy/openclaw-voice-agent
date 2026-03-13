"""
Text-to-Speech service using Alibaba Cloud Qwen3-TTS-Flash-Realtime
Based on official example
"""
import os
import asyncio
import base64
import time
import dashscope
from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime, QwenTtsRealtimeCallback, AudioFormat
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


def add_wav_header(audio_data: bytes, sample_rate: int = 24000, num_channels: int = 1, bits_per_sample: int = 16) -> bytes:
    """Add WAV header to raw PCM data"""
    import struct
    
    data_size = len(audio_data)
    file_size = 36 + data_size
    
    wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF',           # ChunkID
        file_size,         # ChunkSize
        b'WAVE',           # Format
        b'fmt ',           # Subchunk1ID
        16,                # Subchunk1Size (PCM)
        1,                 # AudioFormat (PCM)
        num_channels,      # NumChannels
        sample_rate,       # SampleRate
        sample_rate * num_channels * bits_per_sample // 8,  # ByteRate
        num_channels * bits_per_sample // 8,  # BlockAlign
        bits_per_sample,   # BitsPerSample
        b'data',           # Subchunk2ID
        data_size          # Subchunk2Size
    )
    
    return wav_header + audio_data


class TTSService:
    """Alibaba Cloud Qwen3-TTS-Flash-Realtime TTS service"""
    
    def __init__(self, api_key: str):
        dashscope.api_key = api_key
        self.model = os.getenv("BAILIAN_TTS_MODEL", "qwen3-tts-flash-realtime")
        
    async def synthesize(self, text: str, voice: str = "Cherry") -> Optional[str]:
        """Synthesize text to speech
        
        Args:
            text: Text to synthesize
            voice: Voice name
            
        Returns:
            Base64 encoded audio data (WAV format) or None if failed
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
            
            # Combine audio chunks and convert to WAV
            if callback.audio_chunks:
                audio_data = ''.join(callback.audio_chunks)
                audio_bytes = base64.b64decode(audio_data)
                
                # Add WAV header for browser compatibility
                wav_data = add_wav_header(audio_bytes, 24000, 1, 16)
                return base64.b64encode(wav_data).decode('utf-8')
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
