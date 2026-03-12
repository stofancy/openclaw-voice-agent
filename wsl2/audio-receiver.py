#!/usr/bin/env python3
"""
Audio Receiver for WSL2 - Windows → WSL2 Audio Proxy
- Receives audio stream from Windows
- Forwards to cloud API (Minimax/阿里)
- Plays TTS response
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "listen_port": 8765,
    "minimax_api_key": os.getenv("MINIMAX_API_KEY", ""),
    "minimax_group_id": os.getenv("MINIMAX_GROUP_ID", ""),
    "ali_api_key": os.getenv("ALI_API_KEY", ""),
    "provider": "minimax",  # or "ali"
    "tts_output": "ffplay",  # or "save"
}

class AudioReceiver:
    def __init__(self, config):
        self.config = config
        self.clients = set()
        self.current_state = "IDLE"
        self.audio_buffer = bytearray()
        self.session = None
        
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
                    await self.process_audio()
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON: {message}")
    
    async def handle_audio(self, message):
        """Handle binary audio data"""
        # Parse header (first 4 bytes = header length)
        if len(message) < 4:
            logger.warning("Invalid audio message (too short)")
            return
        
        header_len = int.from_bytes(message[:4], 'big')
        header_json = message[4:4+header_len].decode('utf-8')
        header = json.loads(header_json)
        audio_data = message[4+header_len:]
        
        logger.info(f"Received audio: {header.get('duration_ms', 0):.1f}ms, {len(audio_data)} bytes")
        
        # Accumulate audio buffer
        self.audio_buffer.extend(audio_data)
    
    async def process_audio(self):
        """Process accumulated audio with cloud API"""
        if not self.audio_buffer:
            logger.warning("No audio buffer to process")
            return
        
        logger.info(f"Processing {len(self.audio_buffer)} bytes of audio...")
        
        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                # Write WAV header
                sample_rate = 16000
                channels = 1
                sample_width = 2  # 16-bit
                
                f.write(self._create_wav_header(len(self.audio_buffer), sample_rate, channels, sample_width))
                f.write(self.audio_buffer)
                audio_path = f.name
            
            logger.info(f"Saved audio to {audio_path}")
            
            # Call cloud API
            if self.config['provider'] == 'minimax':
                result = await self.call_minimax(audio_path)
            else:
                result = await self.call_ali(audio_path)
            
            if result:
                # Play TTS response
                await self.play_tts(result.get('audio_url'), result.get('text'))
            
            # Clear buffer
            self.audio_buffer = bytearray()
            
            # Send state update
            await self.broadcast_state("IDLE")
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            self.audio_buffer = bytearray()
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
    
    async def call_minimax(self, audio_path):
        """Call Minimax API for STT + LLM + TTS"""
        if not self.config['minimax_api_key']:
            logger.error("Minimax API key not configured")
            return None
        
        logger.info("Calling Minimax API...")
        
        # Step 1: STT (Speech-to-Text)
        stt_url = "https://api.minimax.chat/v1/asr"
        
        try:
            async with aiohttp.ClientSession() as session:
                # STT
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                
                headers = {
                    "Authorization": f"Bearer {self.config['minimax_api_key']}",
                }
                
                # Note: Minimax ASR API format - adjust based on actual API docs
                form = aiohttp.FormData()
                form.add_field('file', audio_data, filename='audio.wav')
                
                async with session.post(stt_url, headers=headers, data=form) as resp:
                    if resp.status != 200:
                        logger.error(f"STT API error: {resp.status}")
                        return None
                    
                    stt_result = await resp.json()
                    text = stt_result.get('data', {}).get('text', '')
                    logger.info(f"STT result: {text}")
                
                # Step 2: LLM (Chat)
                chat_url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
                
                chat_payload = {
                    "model": "abab6.5s-chat",
                    "messages": [
                        {"role": "user", "content": text}
                    ],
                    "stream": False
                }
                
                async with session.post(chat_url, headers=headers, json=chat_payload) as resp:
                    if resp.status != 200:
                        logger.error(f"Chat API error: {resp.status}")
                        return None
                    
                    chat_result = await resp.json()
                    reply_text = chat_result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    logger.info(f"LLM reply: {reply_text}")
                
                # Step 3: TTS (Text-to-Speech)
                tts_url = "https://api.minimax.chat/v1/t2a"
                
                tts_payload = {
                    "model": "speech-01",
                    "text": reply_text,
                    "voice_id": "female-shaonv",  # Can be configured
                    "format": "mp3"
                }
                
                async with session.post(tts_url, headers=headers, json=tts_payload) as resp:
                    if resp.status != 200:
                        logger.error(f"TTS API error: {resp.status}")
                        return None
                    
                    tts_result = await resp.json()
                    audio_url = tts_result.get('data', {}).get('audio', '')
                    logger.info(f"TTS audio URL: {audio_url}")
                    
                    return {
                        'text': reply_text,
                        'audio_url': audio_url
                    }
                    
        except Exception as e:
            logger.error(f"Minimax API call failed: {e}", exc_info=True)
            return None
    
    async def call_ali(self, audio_path):
        """Call Alibaba DashScope API for STT + LLM + TTS"""
        if not self.config['ali_api_key']:
            logger.error("Alibaba API key not configured")
            return None
        
        logger.info("Calling Alibaba DashScope API...")
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.config['ali_api_key']}",
                    "Content-Type": "application/json"
                }
                
                # Step 1: STT using Paraformer
                stt_url = "https://dashscope.aliyuncs.com/api/v1/services/audio/transcription"
                
                # Upload audio and get task ID
                # Note: Simplified - actual API may require different flow
                stt_payload = {
                    "model": "paraformer-v2",
                    "input": {"file": audio_path},
                    "parameters": {"format": "wav"}
                }
                
                # For now, return mock result
                logger.warning("Ali API not fully implemented, using mock response")
                return {
                    'text': '这是阿里 API 的测试回复',
                    'audio_url': None  # Would need actual TTS call
                }
                
        except Exception as e:
            logger.error(f"Ali API call failed: {e}", exc_info=True)
            return None
    
    async def play_tts(self, audio_url, text):
        """Play TTS audio"""
        if not audio_url and not text:
            logger.warning("No audio URL or text to play")
            return
        
        logger.info(f"Playing TTS: {text[:50]}...")
        
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
                            
                            # Play with ffplay
                            proc = subprocess.Popen(
                                ['ffplay', '-autoexit', '-nodisp', '-loglevel', 'quiet', audio_path],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            proc.wait()
                            
                            # Cleanup
                            os.unlink(audio_path)
            else:
                # No audio, just log
                logger.info(f"TTS text: {text}")
                await asyncio.sleep(1)  # Simulate speaking duration
                
        except Exception as e:
            logger.error(f"Error playing TTS: {e}")
        
        # Update state
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
        
        # Remove disconnected clients
        self.clients -= disconnected
    
    async def run(self):
        """Start WebSocket server"""
        logger.info(f"Starting audio receiver on port {self.config['listen_port']}")
        
        async with websockets.serve(self.handle_client, "0.0.0.0", self.config['listen_port']):
            logger.info("Audio receiver started. Waiting for clients...")
            await asyncio.Future()  # Run forever


async def main():
    receiver = AudioReceiver(CONFIG)
    await receiver.run()


if __name__ == "__main__":
    asyncio.run(main())
