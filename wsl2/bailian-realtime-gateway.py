#!/usr/bin/env python3
"""
百炼 Qwen-Omni 实时语音网关
使用 DashScope SDK 的 OmniRealtimeConversation
"""

import asyncio
import json
import os
import base64
import signal
import sys
import threading
import queue
from datetime import datetime
from pathlib import Path

import websockets
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality, AudioFormat
import dashscope
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Configuration
API_KEY = os.getenv("ALI_BAILIAN_API_KEY", "")
MODEL = "qwen3-omni-flash-realtime"
VOICE = "Chelsie"  # 官方示例使用 Chelsie
WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
PORT = int(os.getenv("AUDIO_PROXY_PORT", "8765"))

# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"realtime_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(message):
    """Simple log"""
    timestamp = datetime.now().isoformat()
    line = f"[{timestamp}] {message}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass

# Set API key
dashscope.api_key = API_KEY

class RealtimeGateway:
    def __init__(self):
        log("="*60)
        log("百炼 Qwen-Omni 实时语音网关")
        log("="*60)
        log(f"API Key: {API_KEY[:15]}...")
        log(f"Model: {MODEL}")
        log(f"Voice: {VOICE}")
        log(f"WS URL: {WS_URL}")
        log(f"Port: {PORT}")
        log(f"Log file: {LOG_FILE}")
        log("="*60)
        
        self.clients = set()
        self.conversation = None
        self.audio_buffer = queue.Queue()
        self.is_connected = False
        
        log("网关初始化完成")
        log("等待客户端连接...")
    
    def on_open(self) -> None:
        log("百炼连接已建立")
        self.is_connected = True
    
    def on_close(self, close_status_code, close_msg) -> None:
        log(f"百炼连接关闭：code={close_status_code}, msg={close_msg}")
        self.is_connected = False
    
    def on_event(self, response: str) -> None:
        try:
            type = response.get('type', 'unknown')
            
            if type == 'session.created':
                log(f"会话创建：{response['session']['id']}")
            
            elif type == 'conversation.item.input_audio_transcription.completed':
                transcript = response.get('transcript', '')
                log(f"语音识别：{transcript}")
                # 转发识别文本到浏览器
                self.send_to_clients_sync({
                    "type": "transcript",
                    "text": transcript,
                    "role": "user"
                })
            
            elif type == 'response.audio_transcript.delta':
                text = response.get('delta', '')
                log(f"LLM 文本：{text}")
                # 转发文本到浏览器（用于字幕）
                self.send_to_clients_sync({
                    "type": "subtitle",
                    "text": text,
                    "role": "ai"
                })
            
            elif type == 'response.audio.delta':
                recv_audio_b64 = response.get('delta', '')
                log(f"收到音频响应：{len(recv_audio_b64)} chars")
                # 转发音频到浏览器（只转发一次）
                self.send_audio_to_clients_sync(recv_audio_b64)
                log(f"已转发音频到浏览器")
            
            elif type == 'input_audio_buffer.speech_started':
                log('====== VAD 检测到语音开始 ======')
            
            elif type == 'response.done':
                log('====== 响应完成 ======')
            
        except Exception as e:
            log(f'回调错误：{e}')
    
    def send_to_clients_sync(self, data: dict) -> None:
        """发送数据到客户端（同步版本，用于回调）"""
        if not self.clients:
            return
        
        response_json = json.dumps(data)
        
        for client in list(self.clients):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(client.send(response_json))
                loop.close()
            except Exception as e:
                log(f"发送失败：{e}")
    
    def send_audio_to_clients_sync(self, audio_b64):
        """Send audio to WebSocket clients (sync version for callback)"""
        response_data = {
            "type": "audio",
            "data": audio_b64,
        }
        self.send_to_clients_sync(response_data)
    
    async def handle_client(self, websocket):
        """Handle browser WebSocket client"""
        log("浏览器客户端已连接")
        self.clients.add(websocket)
        
        # 如果还没连接百炼，创建连接
        if not self.conversation:
            self.create_bailian_connection()
        
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    await self.handle_audio(message)
                else:
                    await self.handle_json(message)
                    
        except websockets.exceptions.ConnectionClosed as e:
            log(f"浏览器客户端断开：code={e.code}")
        finally:
            self.clients.discard(websocket)
            log(f"当前连接数：{len(self.clients)}")
    
    async def handle_audio(self, message):
        """Handle audio from browser"""
        if len(message) < 4:
            return
        
        try:
            # Parse header
            header_len = int.from_bytes(message[:4], 'big')
            if header_len > 10000 or header_len > len(message) - 4:
                return
            
            header_json = message[4:4+header_len].decode('utf-8')
            header = json.loads(header_json)
            audio_data = message[4+header_len:]
            
            # Encode to base64 and send to Bailian
            audio_b64 = base64.b64encode(audio_data).decode('ascii')
            
            if self.conversation and self.is_connected:
                self.conversation.append_audio(audio_b64)
                log(f"转发音频到百炼：{len(audio_data)} bytes")
            
        except Exception as e:
            log(f"处理音频失败：{e}")
    
    async def handle_json(self, message):
        """Handle JSON from browser"""
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')
            
            if msg_type == 'process':
                log("收到处理请求（VAD 触发）")
                # 实时模式下不需要，VAD 会自动触发
            
        except Exception as e:
            log(f"处理 JSON 失败：{e}")
    
    def create_bailian_connection(self):
        """Create connection to Bailian"""
        log("创建百炼连接...")
        
        try:
            callback = self
            self.conversation = OmniRealtimeConversation(
                model=MODEL,
                callback=callback,
                url=WS_URL
            )
            self.conversation.connect()
            
            self.conversation.update_session(
                output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
                voice=VOICE,
                input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
                output_audio_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
                enable_input_audio_transcription=True,
                input_audio_transcription_model='gummy-realtime-v1',
                enable_turn_detection=True,
                turn_detection_type='server_vad',
            )
            
            log("百炼连接创建成功")
            
        except Exception as e:
            log(f"创建百炼连接失败：{e}")
            import traceback
            traceback.print_exc()
    
    async def run(self):
        """Run the server"""
        log(f"\n启动 WebSocket 服务器，监听端口 {PORT}")
        
        async with websockets.serve(self.handle_client, "0.0.0.0", PORT):
            log("服务器已启动")
            await asyncio.Future()

if __name__ == "__main__":
    gateway = RealtimeGateway()
    asyncio.run(gateway.run())
