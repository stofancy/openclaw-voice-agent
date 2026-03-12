#!/usr/bin/env python3
"""
OpenClaw Agent 实时语音网关
集成 Architect Agent + 百炼 STT/TTS
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
import requests
from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime, QwenTtsRealtimeCallback, AudioFormat
import dashscope
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Configuration
API_KEY = os.getenv("ALI_BAILIAN_API_KEY", "")
# 可配置的 Agent ID
AGENT_ID = os.getenv("VOICE_GATEWAY_AGENT", "travel-agency")  # travel-agency 响应更快 (2.86s vs 9.7s)
TTS_MODEL = "qwen3-tts-instruct-flash-realtime"
TTS_VOICE = "Cherry"
WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
PORT = int(os.getenv("AUDIO_PROXY_PORT", "8765"))

# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"agent_gateway_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(message, level="INFO"):
    """增强日志 - 同时输出到文件和控制台"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] [{level}] {message}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass

def log_event(event_type, details=""):
    """记录重要事件 (高亮显示)"""
    emoji_map = {
        'connect': '🔗',
        'disconnect': '🔴',
        'speaking': '🎤',
        'stt': '📝',
        'agent': '🤖',
        'tts': '🔊',
        'error': '❌',
        'success': '✅',
        'volume': '📊',
    }
    emoji = emoji_map.get(event_type, '📋')
    log(f"{emoji} {event_type.upper()}: {details}")

# Set API Key
dashscope.api_key = API_KEY


class TTSCallback(QwenTtsRealtimeCallback):
    """TTS 回调"""
    
    def __init__(self, gateway):
        self.gateway = gateway
        self.complete_event = threading.Event()
        self.audio_chunks = []
    
    def on_open(self) -> None:
        log("✅ TTS 连接已建立")
    
    def on_close(self, close_status_code: int, close_msg: str) -> None:
        log(f"🔴 TTS 连接关闭：code={close_status_code}, msg={close_msg}")
    
    def on_event(self, response: str) -> None:
        try:
            data = json.loads(response) if isinstance(response, str) else response
            event_type = data.get('type', 'unknown')
            
            if event_type == 'session.created':
                session_id = data.get('session', {}).get('id', 'unknown')
                log(f"📋 TTS 会话创建：{session_id}")
            
            elif event_type == 'response.audio.delta':
                audio_b64 = data.get('delta', '')
                if audio_b64:
                    self.audio_chunks.append(audio_b64)
                    # 实时转发到浏览器
                    self.gateway.send_audio_to_clients_sync(audio_b64)
            
            elif event_type == 'response.done':
                log(f"✅ TTS 响应完成")
            
            elif event_type == 'session.finished':
                log(f"🔴 TTS 会话结束")
                self.complete_event.set()
        
        except Exception as e:
            log(f'❌ TTS 回调错误：{e}')
    
    def wait_for_finished(self):
        self.complete_event.wait()


class AgentGateway:
    """Agent 语音网关"""
    
    def __init__(self):
        log("="*60)
        log("OpenClaw Agent 实时语音网关")
        log("="*60)
        log(f"API Key: {API_KEY[:15]}...")
        log(f"Agent ID: {AGENT_ID}")
        log(f"TTS Model: {TTS_MODEL}")
        log(f"TTS Voice: {TTS_VOICE}")
        log(f"Port: {PORT}")
        log(f"Log file: {LOG_FILE}")
        log("="*60)
        
        self.clients = set()
        self.tts_realtime = None
        self.tts_callback = None
        self.is_tts_connected = False
        
        # 实时音频流处理
        self.audio_buffer = bytearray()  # 音频缓冲区
        self.is_speaking = False  # 是否正在说话
        self.silence_start = None  # 静音开始时间
        self.last_audio_time = None  # 最后收到音频时间
        
        # VAD 配置
        self.vad_threshold = 0.3  # VAD 阈值 (0-1)
        self.silence_duration = 1.0  # 静音判定时间 (秒)
        self.min_speech_duration = 0.5  # 最小语音时长 (秒)
        self.speech_start = None  # 说话开始时间
        
        log("网关初始化完成")
        log("等待客户端连接...")
        log(f"VAD 配置：threshold={self.vad_threshold}, silence={self.silence_duration}s")
    
    def init_tts(self):
        """初始化 TTS"""
        if self.tts_realtime and self.is_tts_connected:
            log("TTS 已连接，跳过初始化", "INFO")
            return
        
        log("初始化 TTS...")
        self.tts_callback = TTSCallback(self)
        self.tts_realtime = QwenTtsRealtime(
            model=TTS_MODEL,
            callback=self.tts_callback,
        )
        
        try:
            self.tts_realtime.connect()
            self.tts_realtime.update_session(
                voice=TTS_VOICE,
                response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
                mode='server_commit'
            )
            self.is_tts_connected = True
            log("✅ TTS 初始化完成")
        except Exception as e:
            log(f"❌ TTS 初始化失败：{e}")
            self.is_tts_connected = False
            raise
    
    def send_to_agent(self, transcript: str) -> str:
        """发送语音识别文本给 Agent"""
        log(f"🗣️  用户说：{transcript}")
        
        try:
            # 使用 OpenClaw CLI 调用 Agent
            import subprocess
            
            # 获取默认会话 ID (从环境或配置文件)
            session_id = os.getenv("OPENCLAW_SESSION_ID", "")
            
            cmd = ["openclaw", "agent", "--message", f"[VOICE] {transcript}", "--json"]
            
            if session_id:
                # 使用指定会话
                cmd.extend(["--session-id", session_id])
            else:
                # 使用配置的 Agent
                cmd.extend(["--agent", AGENT_ID])
            
            log(f"📞 调用 Agent: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                # 提取回复内容
                payloads = response.get('result', {}).get('payloads', [])
                if payloads:
                    reply = payloads[0].get('text', '')
                    log(f"🤖  Agent 回复：{reply[:100]}...")
                    return reply
                else:
                    log(f"⚠️  无回复内容")
                    return "好的，我收到了你的消息。"
            else:
                log(f"⚠️  Agent 请求失败：{result.stderr[:200]}")
                # 降级：返回固定回复
                return "好的，我收到了。"
        
        except subprocess.TimeoutExpired:
            log(f"⏱️  Agent 调用超时 (60s)")
            return "抱歉，响应超时了。"
        except Exception as e:
            log(f"❌ 发送 Agent 失败：{e}")
            return "抱歉，出了点问题。"
    
    def call_tts(self, text: str) -> None:
        """调用 TTS 合成语音"""
        if not text:
            return
        
        log(f"🔊 TTS 合成：{text[:50]}...")
        
        try:
            # 检查并重连 TTS
            if not self.is_tts_connected or not self.tts_realtime:
                log("🔌 TTS 未连接，重新初始化...", "INFO")
                self.tts_realtime = None
                self.tts_callback = None
                self.is_tts_connected = False
                self.init_tts()
            
            # 分句发送（避免太长）
            sentences = text.split('。')
            for sentence in sentences:
                if sentence.strip():
                    self.tts_realtime.append_text(sentence + '。')
            
            self.tts_realtime.finish()
            self.tts_callback.wait_for_finished()
            
            log("✅ TTS 合成完成")
        
        except Exception as e:
            log(f"❌ TTS 合成失败：{e}")
            # 标记为未连接，下次会重连
            self.is_tts_connected = False
    
    def send_audio_to_clients_sync(self, audio_b64):
        """发送音频到客户端（同步版本，用于回调）"""
        response_data = {
            "type": "audio",
            "data": audio_b64,
        }
        self.send_to_clients_sync(response_data)
    
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
    
    async def handle_client(self, websocket):
        """Handle browser WebSocket client"""
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        log(f"🌐 浏览器客户端已连接 (IP: {client_ip})")
        log(f"📋 WebSocket 状态：{websocket.state}")
        log(f"🔗 WebSocket 协议：{websocket.protocol}")
        log(f"👥 当前连接数：{len(self.clients) + 1}")
        self.clients.add(websocket)
        
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    await self.handle_audio(message)
                else:
                    await self.handle_json(message)
        
        except websockets.exceptions.ConnectionClosed:
            log(f"🌐 浏览器客户端断开")
        
        finally:
            self.clients.discard(websocket)
            log(f"当前连接数：{len(self.clients)}")
    
    async def handle_audio(self, message: bytes) -> None:
        """处理实时音频流数据"""
        try:
            # 解析音频数据 (假设是 PCM 16bit 16kHz)
            audio_data = message
            
            # 计算音量 (简单的 RMS)
            import struct
            samples = struct.unpack('<' + 'h' * (len(audio_data) // 2), audio_data)
            rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
            volume = min(1.0, rms / 1000)  # 归一化到 0-1
            
            # VAD 检测
            is_voice = volume > self.vad_threshold
            self._process_vad(is_voice, volume)
            
            # 累积音频到缓冲区
            if is_voice:
                self.audio_buffer.extend(audio_data)
            
            # 发送音量更新到客户端
            await self.send_to_clients_async({
                "type": "volume",
                "volume": volume,
                "is_speaking": self.is_speaking
            })
            
        except Exception as e:
            log(f"❌ 处理音频流失败：{e}")
    
    def _process_vad(self, is_voice: bool, volume: float) -> None:
        """VAD (Voice Activity Detection) 处理"""
        now = datetime.now()
        
        if is_voice:
            # 检测到声音
            if not self.is_speaking:
                # 开始说话
                self.is_speaking = True
                self.speech_start = now
                self.silence_start = None
                log(f"🎤 检测到说话开始 (volume={volume:.2f})")
                
                # 通知客户端
                asyncio.create_task(self.send_to_clients_async({
                    "type": "user_started_speaking"
                }))
            
            self.last_audio_time = now
            self.silence_start = None
            
        else:
            # 静音
            if self.is_speaking:
                if self.silence_start is None:
                    self.silence_start = now
                else:
                    silence_duration = (now - self.silence_start).total_seconds()
                    
                    # 检测说话结束
                    if silence_duration >= self.silence_duration:
                        speech_duration = (now - self.speech_start).total_seconds()
                        
                        if speech_duration >= self.min_speech_duration:
                            # 说话结束，处理音频
                            log(f"🎤 检测到说话结束 (持续 {speech_duration:.2f}s)")
                            asyncio.create_task(self._process_speech_end())
                        else:
                            log(f"⚠️  语音太短 ({speech_duration:.2f}s)，忽略")
                        
                        # 重置状态
                        self.is_speaking = False
                        self.audio_buffer = bytearray()
                        self.silence_start = None
                        self.speech_start = None
    
    async def _process_speech_end(self) -> None:
        """说话结束处理：STT → Agent → TTS"""
        if len(self.audio_buffer) == 0:
            return
        
        log(f"📦 处理语音数据：{len(self.audio_buffer)} bytes")
        
        # 发送状态到客户端
        await self.send_to_clients_async({
            "type": "status",
            "status": "recognizing"
        })
        
        # TODO: 调用百炼 STT API
        # 暂时使用占位符
        stt_text = "识别的文本"  # 需要调用 STT API
        
        log(f"📝 STT 识别结果：{stt_text}")
        
        # 发送识别结果到客户端 (用于字幕)
        await self.send_to_clients_async({
            "type": "stt_result",
            "text": stt_text,
            "is_final": True
        })
        
        # 调用 Agent
        await self.send_to_clients_async({
            "type": "status",
            "status": "processing"
        })
        
        reply = self.send_to_agent(stt_text)
        log(f"🤖 Agent 回复：{reply[:100]}...")
        
        # 发送 Agent 回复 (用于字幕)
        await self.send_to_clients_async({
            "type": "agent_reply",
            "text": reply
        })
        
        # TTS 合成
        if reply:
            self.call_tts(reply)
    
    async def handle_json(self, message: str) -> None:
        """处理 JSON 消息"""
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')
            
            log(f"📥 收到 JSON 消息：type={msg_type}")
            # debug_log("消息内容", data)  # 临时注释，避免未定义错误
            
            if msg_type == 'process':
                log("收到处理请求")
                # 这里应该触发 STT 处理
                # 简化处理：暂时不处理
            
            elif msg_type == 'stt_result':
                # STT 识别结果，转发给 Agent
                text = data.get('text', '')
                if text:
                    log_event('stt', text)
                    await self.process_stt_result(text)
                else:
                    log("⚠️  STT 结果为空", "WARNING")
            
            elif msg_type == 'connect':
                log_event('connect', '客户端连接测试')
                await self.send_to_clients_async({
                    "type": "connected",
                    "timestamp": datetime.now().isoformat(),
                    "gateway": "ready"
                })
            
            elif msg_type == 'audio_stream_start':
                log("🎤 音频流开始")
                self.audio_buffer = bytearray()
                self.is_speaking = False
            
            elif msg_type == 'audio_stream_stop':
                log("🎤 音频流结束")
                # 如果有缓冲的音频，处理它
                if len(self.audio_buffer) > 0:
                    await self._process_speech_end()
        
        except json.JSONDecodeError as e:
            log(f"❌ JSON 解析失败：{e}")
            log(f"   原始消息：{message[:200]}")
        except Exception as e:
            log(f"❌ 处理 JSON 失败：{e}", exc_info=True)
    
    async def process_stt_result(self, text: str) -> None:
        """处理 STT 识别结果"""
        log_event('speaking', f'用户说：{text}')
        
        # 发送状态
        await self.send_to_clients_async({"type": "status", "status": "processing"})
        
        # 调用 Agent (同步)
        log("⏳ 调用 Agent...", "INFO")
        reply = self.send_to_agent(text)
        log_event('agent', reply[:50] + '...' if len(reply) > 50 else reply)
        
        # 发送文本回复
        await self.send_to_clients_async({
            "type": "reply",
            "text": reply
        })
        
        # 调用 TTS (同步)
        if reply:
            log_event('tts', '开始合成语音')
            self.call_tts(reply)
    
    async def send_to_clients_async(self, data: dict) -> None:
        """发送数据到客户端（异步版本）"""
        if not self.clients:
            return
        
        response_json = json.dumps(data)
        
        for client in list(self.clients):
            try:
                await client.send(response_json)
            except Exception as e:
                log(f"发送失败：{e}")
    
    async def run(self, host="0.0.0.0", port=PORT):
        """运行服务器"""
        log(f"\n启动 WebSocket 服务器，监听端口 {port}")
        
        async with websockets.serve(self.handle_client, host, port):
            log("✅ 服务器已启动")
            log("等待浏览器连接...")
            await asyncio.Future()


async def main():
    """主函数"""
    gateway = AgentGateway()
    await gateway.run()


if __name__ == "__main__":
    asyncio.run(main())
