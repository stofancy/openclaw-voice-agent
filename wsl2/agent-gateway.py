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
import tempfile
import struct
import traceback
from datetime import datetime
from pathlib import Path

import websockets
import requests
from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime, QwenTtsRealtimeCallback, AudioFormat
from dashscope.audio.asr import Recognition
from dashscope.audio.asr_realtime import ASRRealtime, ASRRealtimeCallback
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


class STTCallback(ASRRealtimeCallback):
    """实时 STT 回调"""
    
    def __init__(self, gateway):
        self.gateway = gateway
        self.result_text = ""
        self.final_text = ""
        self.partial_callback = None  # 用于回调增量结果
        
    def on_open(self) -> None:
        log("✅ STT 连接已建立")
        
    def on_close(self, close_status_code: int, close_msg: str) -> None:
        log(f"🔴 STT 连接关闭：code={close_status_code}, msg={close_msg}")
        
    def on_event(self, response: str) -> None:
        try:
            data = json.loads(response) if isinstance(response, str) else response
            event_type = data.get('type', 'unknown')
            
            if event_type == 'session.created':
                session_id = data.get('session', {}).get('id', 'unknown')
                log(f"📋 STT 会话创建：{session_id}")
                
            elif event_type == 'recognizer.result.increment':
                # 增量识别结果（流式）
                text = data.get('result', {}).get('text', '')
                if text:
                    self.result_text = text
                    log(f"📝 识别中：{text}", "DEBUG")
                    # 通知网关有增量结果
                    if self.partial_callback:
                        self.partial_callback(text, is_final=False)
                    
            elif event_type == 'recognizer.result.completed':
                # 完成识别结果
                text = data.get('result', {}).get('text', '')
                if text:
                    self.final_text = text
                    log(f"✅ 识别完成：{text}")
                    # 通知网关有最终结果
                    if self.partial_callback:
                        self.partial_callback(text, is_final=True)
                    
            elif event_type == 'session.finished':
                log(f"🔴 STT 会话结束")
                
        except Exception as e:
            log(f'❌ STT 回调错误：{e}', "ERROR")


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
            
            log(f"📥 TTS 回调事件：{event_type}", "DEBUG")
            
            if event_type == 'session.created':
                session_id = data.get('session', {}).get('id', 'unknown')
                log(f"📋 TTS 会话创建：{session_id}")
            
            elif event_type == 'response.audio.delta':
                audio_b64 = data.get('delta', '')
                log(f"🎵 收到 TTS 音频块：{len(audio_b64)} bytes", "DEBUG")
                if audio_b64:
                    self.audio_chunks.append(audio_b64)
                    log(f"📤 发送音频到客户端...", "INFO")
                    # 实时转发到浏览器
                    self.gateway.send_audio_to_clients_sync(audio_b64)
                    log(f"✅ 音频已发送到客户端", "DEBUG")
            
            elif event_type == 'response.done':
                log(f"✅ TTS 响应完成，共 {len(self.audio_chunks)} 个音频块")
            
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
        
        # STT 相关
        self.stt_realtime = None
        self.stt_callback = None
        self.is_stt_connected = False
        self.current_stt_text = ""  # 当前 STT 识别结果
        
        # TTS 相关
        self.tts_realtime = None
        self.tts_callback = None
        self.is_tts_connected = False
        
        # 实时音频流处理
        self.audio_buffer = bytearray()  # 音频缓冲区（用于备份）
        self.is_speaking = False  # 是否正在说话
        self.silence_start = None  # 静音开始时间
        self.last_audio_time = None  # 最后收到音频时间
        
        # VAD 配置 - 优化避免误触发和重叠播放
        self.vad_threshold = 0.2  # VAD 阈值 (0-1) - 提高避免误触发
        self.silence_duration = 1.2  # 静音判定时间 (秒) - 延长避免打断
        self.min_speech_duration = 0.5  # 最小语音时长 (秒)
        self.speech_start = None  # 说话开始时间
        
        # TTS 播放状态
        self.is_playing_tts = False  # 是否正在播放 TTS
        self.tts_playing_lock = threading.Lock()  # TTS 播放锁
        
        # 流式 STT 状态
        self.stt_partial_text = ""  # 增量识别结果
        self.stt_final_text = ""  # 最终识别结果
        self.stt_event = threading.Event()  # STT 完成事件
        
        log("网关初始化完成")
        log("等待客户端连接...")
        log(f"VAD 配置：threshold={self.vad_threshold}, silence={self.silence_duration}s")
    
    def init_stt(self):
        """初始化实时 STT"""
        if self.stt_realtime and self.is_stt_connected:
            return
        
        log("初始化实时 STT...")
        dashscope.api_key = API_KEY
        self.stt_callback = STTCallback(self)
        
        # 设置回调函数处理增量结果
        def on_stt_partial(text, is_final):
            self.stt_partial_text = text
            if is_final:
                self.stt_final_text = text
                self.stt_event.set()  # 通知 STT 完成
                log(f"✅ STT 最终结果：{text}")
            else:
                log(f"📝 STT 增量：{text}", "DEBUG")
        
        self.stt_callback.partial_callback = on_stt_partial
        
        self.stt_realtime = ASRRealtime(
            model='paraformer-realtime-v2',
            callback=self.stt_callback,
        )
        
        try:
            self.stt_realtime.connect()
            self.is_stt_connected = True
            log("✅ STT 初始化完成")
        except Exception as e:
            log(f"❌ STT 初始化失败：{e}", "ERROR")
            self.is_stt_connected = False
            raise
    
    def init_tts(self):
        """初始化 TTS"""
        if self.tts_realtime and self.is_tts_connected:
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
        """调用 TTS 合成语音 - 防止重叠播放"""
        if not text:
            return
        
        # 使用锁确保线程安全
        with self.tts_playing_lock:
            if self.is_playing_tts:
                log("⏳ TTS 正在播放，跳过", "INFO")
                return
            
            self.is_playing_tts = True
        
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
            self.is_tts_connected = False
        finally:
            with self.tts_playing_lock:
                self.is_playing_tts = False
    
    def send_audio_to_clients_sync(self, audio_b64):
        """发送音频到客户端（同步版本，用于回调）"""
        response_data = {
            "type": "audio",
            "data": audio_b64,
        }
        try:
            # 尝试获取当前事件循环，如果没有则创建新的
            try:
                loop = asyncio.get_running_loop()
                # 在当前循环中创建任务（非阻塞）
                asyncio.create_task(self.send_to_clients_async(response_data))
            except RuntimeError:
                # 没有运行中的循环，创建新循环并运行
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.send_to_clients_async(response_data))
                loop.close()
        except Exception as e:
            log(f"❌ 发送音频失败：{e}")
    
    def send_to_clients_sync(self, data: dict) -> None:
        """发送数据到客户端（同步版本，用于回调）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_to_clients_async(data))
            loop.close()
        except Exception as e:
            log(f"发送失败：{e}")
    
    async def handle_client(self, websocket):
        """Handle browser WebSocket client"""
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        log(f"🌐 浏览器客户端已连接 (IP: {client_ip})")
        self.clients.add(websocket)
        
        # 初始化 STT（如果需要）
        if not self.is_stt_connected:
            try:
                self.init_stt()
            except Exception as e:
                log(f"⚠️  STT 初始化失败：{e}", "WARN")
        
        try:
            async for message in websocket:
                try:
                    if isinstance(message, bytes):
                        await self.handle_audio(message)
                    else:
                        await self.handle_json(message)
                except Exception as e:
                    log(f"❌ 处理消息失败：{e}", "ERROR")
                    traceback.print_exc()
        
        except websockets.exceptions.ConnectionClosed:
            log(f"🌐 浏览器客户端断开")
        except Exception as e:
            log(f"❌ WebSocket 错误：{e}", "ERROR")
            traceback.print_exc()
        finally:
            self.clients.discard(websocket)
            log(f"当前连接数：{len(self.clients)}")
    
    async def handle_audio(self, message: bytes) -> None:
        """处理实时音频流数据 - 流式 STT"""
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
            
            # 累积音频到缓冲区（备份）
            if is_voice:
                self.audio_buffer.extend(audio_data)
            
            # 流式 STT: 实时发送音频到百炼
            if is_voice and self.is_stt_connected and self.stt_realtime:
                try:
                    self.stt_realtime.send_audio(audio_data)
                    log(f"📤 发送音频到 STT: {len(audio_data)} bytes", "DEBUG")
                except Exception as e:
                    log(f"⚠️  STT 发送失败：{e}", "WARN")
            
            # 发送音量更新到客户端
            await self.send_to_clients_async({
                "type": "volume",
                "volume": volume,
                "is_speaking": self.is_speaking
            })
            
        except Exception as e:
            log(f"❌ 处理音频流失败：{e}")
    
    def _process_vad(self, is_voice: bool, volume: float) -> None:
        """VAD (Voice Activity Detection) 处理 - 优化灵敏度"""
        now = datetime.now()
        
        if is_voice:
            # 检测到声音 (提高阈值避免误触发)
            if not self.is_speaking:
                # 开始说话 - 重置 STT 状态
                self.is_speaking = True
                self.speech_start = now
                self.silence_start = None
                self.stt_partial_text = ""
                self.stt_final_text = ""
                self.stt_event.clear()
                log_event('speaking', f'开始 (volume={volume:.2f})')
                
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
                    
                    # 检测说话结束 (延长静音判定时间)
                    if silence_duration >= self.silence_duration:
                        speech_duration = (now - self.speech_start).total_seconds()
                        
                        if speech_duration >= self.min_speech_duration:
                            # 说话结束，处理音频
                            log_event('speaking', f'结束 (持续 {speech_duration:.2f}s)')
                            asyncio.create_task(self._process_speech_end())
                        else:
                            log(f"⚠️  语音太短 ({speech_duration:.2f}s)，忽略")
                        
                        # 重置状态
                        self.is_speaking = False
                        self.silence_start = None
                        self.speech_start = None
    
    async def _process_speech_end(self) -> None:
        """说话结束处理：STT → Agent → TTS (流式 STT)"""
        try:
            # 发送状态到客户端
            await self.send_to_clients_async({
                "type": "status",
                "status": "recognizing"
            })
            log("📤 发送 status=recognizing", "DEBUG")
            
            # 结束 STT 识别
            if self.is_stt_connected and self.stt_realtime:
                log("🛑 结束 STT 识别...", "INFO")
                self.stt_realtime.finish()
                
                # 等待 STT 完成 (最多 5 秒)
                if self.stt_event.wait(timeout=5.0):
                    stt_text = self.stt_final_text
                    log(f"✅ STT 完成：{stt_text}")
                else:
                    stt_text = self.stt_partial_text
                    log(f"⏱️ STT 超时，使用部分结果：{stt_text}", "WARN")
            else:
                log("⚠️  STT 未连接，使用备用方案", "WARN")
                stt_text = ""
            
            # 降级处理
            if not stt_text:
                log("⚠️  STT 识别失败，使用默认文本", "WARN")
                stt_text = "你好"
            
            log(f"📝 STT 识别结果：{stt_text}")
            
            # 发送识别结果到客户端 (用于字幕)
            await self.send_to_clients_async({
                "type": "stt_result",
                "text": stt_text,
                "is_final": True
            })
            log(f"📤 发送 stt_result: {stt_text}", "DEBUG")
            
            # 调用 Agent
            await self.send_to_clients_async({
                "type": "status",
                "status": "processing"
            })
            log("📤 发送 status=processing", "DEBUG")
            
            reply = self.send_to_agent(stt_text)
            log(f"🤖 Agent 回复：{reply[:100]}...")
            
            # 发送 Agent 回复 (用于字幕)
            await self.send_to_clients_async({
                "type": "reply",
                "text": reply
            })
            log(f"📤 发送 reply: {reply[:50]}...", "DEBUG")
            
            # TTS 合成
            if reply:
                log_event('tts', '开始合成语音')
                self.call_tts(reply)
                log("✅ TTS 调用完成", "DEBUG")
            
            # 重置 STT 状态
            self.stt_partial_text = ""
            self.stt_final_text = ""
            self.stt_event.clear()
            self.audio_buffer = bytearray()
            
        except Exception as e:
            log(f"❌ _process_speech_end 错误：{e}", "ERROR")
    
    def _call_stt_api(self, audio_data: bytes) -> str:
        """调用百炼 STT API - 异步识别"""
        try:
            # 创建临时 WAV 文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                # 写入 WAV 头
                f.write(self._create_wav_header(len(audio_data), 16000, 1, 2))
                f.write(audio_data)
                temp_path = f.name
            
            try:
                # 调用识别 API (异步方式)
                log("📞 调用百炼 STT...", "INFO")
                from dashscope.audio.asr import RecognitionCallback
                
                class MyCallback(RecognitionCallback):
                    def on_event(self, result):
                        pass
                
                callback = MyCallback()
                recognition = Recognition(
                    model='paraformer-realtime-v2',
                    callback=callback,
                    format='wav',
                    sample_rate=16000,
                )
                result = recognition.call(temp_path)
                
                if result.status_code == 200:
                    text = result.get('output', {}).get('text', '')
                    log(f"✅ STT 成功：{text}", "INFO")
                    return text
                else:
                    log(f"❌ STT 失败：{result.message}", "ERROR")
                    return ""
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            log(f"❌ STT 异常：{e}", "ERROR")
            return ""
    
    def _create_wav_header(self, data_len, sample_rate, channels, sample_width):
        """创建 WAV 文件头"""
        byte_rate = sample_rate * channels * sample_width
        block_align = channels * sample_width
        
        header = struct.pack('<4sI4s', b'RIFF', 36 + data_len, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, sample_width * 8)
        header += struct.pack('<4sI', b'data', data_len)
        return header
    
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
            
            elif msg_type == 'browser_log':
                # 浏览器日志
                level = data.get('level', 'log')
                message = data.get('message', '')
                if message:
                    log(f"🌐 BROWSER [{level.upper()}]: {message}")
            
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
        
        try:
            # 发送状态
            await self.send_to_clients_async({"type": "status", "status": "recognizing"})
            log("📤 发送 status=recognizing", "DEBUG")
            
            # 调用 Agent (同步)
            log("⏳ 调用 Agent...", "INFO")
            reply = self.send_to_agent(text)
            log_event('agent', reply[:50] + '...' if len(reply) > 50 else reply)
            
            # 发送文本回复
            await self.send_to_clients_async({
                "type": "reply",
                "text": reply
            })
            log(f"📤 发送 reply: {reply[:50]}...", "DEBUG")
            
            # 调用 TTS (同步)
            if reply:
                log_event('tts', '开始合成语音')
                self.call_tts(reply)
                log("✅ TTS 调用完成", "DEBUG")
        except Exception as e:
            log(f"❌ process_stt_result 错误：{e}", "ERROR")
    
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
    
    # 设置信号处理
    def signal_handler(sig, frame):
        log(f"📥 收到信号 {sig}，正在关闭...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await gateway.run()
    except Exception as e:
        log(f"❌ 网关崩溃：{e}", "ERROR")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("👋 网关已停止")
    except Exception as e:
        log(f"❌ 网关异常退出：{e}", "ERROR")
        traceback.print_exc()
        sys.exit(1)
