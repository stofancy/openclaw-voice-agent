#!/usr/bin/env python3
"""
Streaming Audio Receiver for WSL2 - Optimized for <300ms latency
- Receives audio stream from Windows
- Streams to Minimax/Alibaba for STT+LLM+TTS
- Plays TTS response with minimal buffering
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import websockets
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
CONFIG = {
    "listen_port": int(os.getenv("AUDIO_PROXY_PORT", 8765)),
    "minimax_api_key": os.getenv("MINIMAX_API_KEY", ""),
    "minimax_group_id": os.getenv("MINIMAX_GROUP_ID", ""),
    "ali_api_key": os.getenv("ALI_API_KEY", ""),
    "provider": os.getenv("AUDIO_PROVIDER", "minimax"),
    "chunk_size_ms": int(os.getenv("AUDIO_CHUNK_SIZE_MS", 32)),
}


class StreamingAudioReceiver:
    """Optimized streaming receiver with parallel processing"""
    
    def __init__(self, config):
        self.config = config
        self.clients = set()
        self.current_state = "IDLE"
        
        # Streaming buffers
        self.audio_buffer = bytearray()
        self.stt_buffer = bytearray()  # For streaming STT
        self.tts_buffer = asyncio.Queue()  # For streaming TTS
        
        # Pipeline state
        self.stt_websocket = None
        self.llm_session = None
        self.tts_playing = False
        
        # Timing
        self.timings = {}
        
    async def handle_client(self, websocket):
        """Handle a Windows client connection"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    await self.handle_audio(message)
                else:
                    await self.handle_json(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        finally:
            self.clients.discard(websocket)
    
    async def handle_json(self, message):
        """Handle JSON state messages"""
        try:
            data = json.loads(message)
            if data.get("type") == "state":
                old_state = self.current_state
                self.current_state = data.get("state", "IDLE")
                logger.info(f"State change: {old_state} → {self.current_state}")
                
                # Trigger processing when state changes to PROCESSING
                if self.current_state == "PROCESSING" and self.audio_buffer:
                    await self.process_audio_streaming()
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON: {message}")
    
    async def handle_audio(self, message):
        """Handle binary audio data"""
        # Parse header
        if len(message) < 4:
            logger.warning("Invalid audio message (too short)")
            return
        
        header_len = int.from_bytes(message[:4], 'big')
        header_json = message[4:4+header_len].decode('utf-8')
        header = json.loads(header_json)
        audio_data = message[4+header_len:]
        
        logger.debug(f"Received audio: {header.get('duration_ms', 0):.1f}ms, {len(audio_data)} bytes")
        
        # Accumulate audio buffer
        self.audio_buffer.extend(audio_data)
        self.stt_buffer.extend(audio_data)
    
    async def process_audio_streaming(self):
        """Process audio with streaming pipeline for minimal latency"""
        if not self.audio_buffer:
            logger.warning("No audio buffer to process")
            return
        
        logger.info(f"Processing {len(self.audio_buffer)} bytes with streaming pipeline...")
        self.timings['start'] = datetime.now()
        
        try:
            # Create temp file for fallback
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(self._create_wav_header(len(self.audio_buffer), 16000, 1, 2))
                f.write(self.audio_buffer)
                audio_path = f.name
            
            self.timings['audio_saved'] = datetime.now()
            
            # Call streaming API based on provider
            if self.config['provider'] == 'minimax':
                result = await self.call_minimax_streaming(audio_path)
            else:
                result = await self.call_ali_streaming(audio_path)
            
            self.timings['api_complete'] = datetime.now()
            
            if result:
                # Play TTS response
                await self.play_tts_streaming(result)
            
            # Clear buffers
            self.audio_buffer = bytearray()
            self.stt_buffer = bytearray()
            
            # Log timings
            self._log_timings()
            
            # Send state update
            await self.broadcast_state("IDLE")
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            self.audio_buffer = bytearray()
            self.stt_buffer = bytearray()
            await self.broadcast_state("IDLE")
    
    def _create_wav_header(self, data_len, sample_rate, channels, sample_width):
        """Create WAV file header"""
        import struct
        byte_rate = sample_rate * channels * sample_width
        block_align = channels * sample_width
        
        header = struct.pack('<4sI4s', b'RIFF', 36 + data_len, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, sample_width * 8)
        header += struct.pack('<4sI', b'data', data_len)
        return header
    
    async def call_minimax_streaming(self, audio_path):
        """Call Minimax streaming API with parallel processing"""
        if not self.config['minimax_api_key']:
            logger.error("Minimax API key not configured")
            return None
        
        logger.info("Calling Minimax streaming API...")
        self.timings['stt_start'] = datetime.now()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.config['minimax_api_key']}",
                }
                
                # Step 1: Read audio file
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                
                # Step 2: STT (using batch API for now, streaming would need WebSocket)
                stt_url = "https://api.minimax.chat/v1/asr"
                form = aiohttp.FormData()
                form.add_field('file', audio_data, filename='audio.wav')
                
                async with session.post(stt_url, headers=headers, data=form) as resp:
                    if resp.status != 200:
                        logger.error(f"STT API error: {resp.status}")
                        return None
                    
                    stt_result = await resp.json()
                    text = stt_result.get('data', {}).get('text', '')
                    self.timings['stt_complete'] = datetime.now()
                    logger.info(f"STT result ({(self.timings['stt_complete'] - self.timings['stt_start']).total_seconds()*1000:.0f}ms): {text}")
                
                # Step 3: LLM with streaming
                chat_url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
                chat_payload = {
                    "model": "abab6.5s-chat",
                    "messages": [{"role": "user", "content": text}],
                    "stream": True
                }
                
                self.timings['llm_start'] = datetime.now()
                full_reply = []
                
                async with session.post(chat_url, headers=headers, json=chat_payload) as resp:
                    if resp.status != 200:
                        logger.error(f"Chat API error: {resp.status}")
                        return None
                    
                    async for line in resp.content:
                        if line.startswith(b"data: "):
                            try:
                                data = json.loads(line[6:])
                                choice = data.get('choices', [{}])[0]
                                if choice.get('finish_reason') != 'stop':
                                    content = choice.get('delta', {}).get('content', '')
                                    if content:
                                        full_reply.append(content)
                                        # Could stream to TTS here for even lower latency
                            except:
                                pass
                
                reply_text = ''.join(full_reply)
                self.timings['llm_complete'] = datetime.now()
                logger.info(f"LLM reply ({(self.timings['llm_complete'] - self.timings['llm_start']).total_seconds()*1000:.0f}ms): {reply_text[:50]}...")
                
                # Step 4: TTS
                tts_url = "https://api.minimax.chat/v1/t2a"
                tts_payload = {
                    "model": "speech-01",
                    "text": reply_text,
                    "voice_id": "female-shaonv",
                    "format": "mp3"
                }
                
                self.timings['tts_start'] = datetime.now()
                
                async with session.post(tts_url, headers=headers, json=tts_payload) as resp:
                    if resp.status != 200:
                        logger.error(f"TTS API error: {resp.status}")
                        return None
                    
                    tts_result = await resp.json()
                    audio_url = tts_result.get('data', {}).get('audio', '')
                    self.timings['tts_complete'] = datetime.now()
                    logger.info(f"TTS audio ready ({(self.timings['tts_complete'] - self.timings['tts_start']).total_seconds()*1000:.0f}ms)")
                    
                    return {
                        'text': reply_text,
                        'audio_url': audio_url,
                        'stt_text': text
                    }
                    
        except Exception as e:
            logger.error(f"Minimax API call failed: {e}", exc_info=True)
            return None
    
    async def call_ali_streaming(self, audio_path):
        """Call Alibaba DashScope streaming API"""
        if not self.config['ali_api_key']:
            logger.error("Alibaba API key not configured")
            return None
        
        logger.info("Calling Alibaba DashScope streaming API...")
        
        # Placeholder - similar structure to Minimax
        # Would use WebSocket for real streaming
        logger.warning("Ali streaming API not fully implemented yet")
        return None
    
    async def play_tts_streaming(self, result):
        """Play TTS audio with minimal buffering"""
        audio_url = result.get('audio_url')
        text = result.get('text')
        
        if not audio_url and not text:
            logger.warning("No audio URL or text to play")
            return
        
        logger.info(f"Playing TTS: {text[:50]}...")
        self.timings['play_start'] = datetime.now()
        
        # Update state
        await self.broadcast_state("SPEAKING")
        
        try:
            if audio_url:
                # Download and play
                async with aiohttp.ClientSession() as session:
                    async with session.get(audio_url) as resp:
                        if resp.status == 200:
                            audio_data = await resp.read()
                            
                            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                                f.write(audio_data)
                                audio_path = f.name
                            
                            # Play with ffplay (minimal buffering)
                            proc = subprocess.Popen(
                                ['ffplay', '-autoexit', '-nodisp', '-loglevel', 'quiet', 
                                 '-fflags', 'nobuffer', '-flags', 'low_delay'],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            
                            # Stream audio data
                            with open(audio_path, 'rb') as f:
                                while True:
                                    chunk = f.read(4096)
                                    if not chunk:
                                        break
                                    proc.stdin.write(chunk)
                            
                            proc.stdin.close()
                            proc.wait()
                            
                            # Cleanup
                            os.unlink(audio_path)
                            
        except Exception as e:
            logger.error(f"Error playing TTS: {e}")
        
        self.timings['play_complete'] = datetime.now()
        await self.broadcast_state("IDLE")
    
    async def broadcast_state(self, state):
        """Broadcast state to all clients"""
        if not self.clients:
            return
        
        message = json.dumps({"type": "state", "state": state})
        
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except Exception:
                disconnected.add(client)
        
        self.clients -= disconnected
    
    def _log_timings(self):
        """Log detailed timing breakdown"""
        if 'start' not in self.timings:
            return
        
        total_ms = (datetime.now() - self.timings['start']).total_seconds() * 1000
        
        logger.info("=" * 50)
        logger.info(f"⏱️  End-to-End Latency: {total_ms:.0f}ms")
        logger.info("-" * 50)
        
        if 'stt_start' in self.timings and 'stt_complete' in self.timings:
            stt_ms = (self.timings['stt_complete'] - self.timings['stt_start']).total_seconds() * 1000
            logger.info(f"📝 STT: {stt_ms:.0f}ms")
        
        if 'llm_start' in self.timings and 'llm_complete' in self.timings:
            llm_ms = (self.timings['llm_complete'] - self.timings['llm_start']).total_seconds() * 1000
            logger.info(f"🧠 LLM: {llm_ms:.0f}ms")
        
        if 'tts_start' in self.timings and 'tts_complete' in self.timings:
            tts_ms = (self.timings['tts_complete'] - self.timings['tts_start']).total_seconds() * 1000
            logger.info(f"🔊 TTS: {tts_ms:.0f}ms")
        
        if 'play_start' in self.timings and 'play_complete' in self.timings:
            play_ms = (self.timings['play_complete'] - self.timings['play_start']).total_seconds() * 1000
            logger.info(f"🔊 Play: {play_ms:.0f}ms")
        
        logger.info("=" * 50)
        
        if total_ms < 300:
            logger.info("✅ Meets <300ms target!")
        else:
            logger.info(f"⚠️ Exceeds 300ms target by {total_ms - 300:.0f}ms")
    
    async def run(self):
        """Start WebSocket server"""
        logger.info(f"Starting streaming audio receiver on port {self.config['listen_port']}")
        logger.info(f"Provider: {self.config['provider']}")
        logger.info(f"API Key configured: {'Yes' if self.config['minimax_api_key'] else 'No'}")
        
        async with websockets.serve(self.handle_client, "0.0.0.0", self.config['listen_port']):
            logger.info("Audio receiver started. Waiting for clients...")
            await asyncio.Future()  # Run forever


async def main():
    receiver = StreamingAudioReceiver(CONFIG)
    await receiver.run()


if __name__ == "__main__":
    asyncio.run(main())
