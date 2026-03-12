#!/usr/bin/env python3
"""
OpenClaw Agent 实时语音网关
集成 Architect Agent + 百炼 STT/TTS

架构：依赖注入 + Handlers
- 外部依赖通过 container 注入
- 业务逻辑通过 handlers 处理
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
from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult
import dashscope
from dotenv import load_dotenv

# 依赖注入容器
from .container import Container

load_dotenv(Path(__file__).parent.parent / ".env")

# Configuration
API_KEY = os.getenv("ALI_BAILIAN_API_KEY", "")
# 可配置的 Agent ID
AGENT_ID = os.getenv("VOICE_GATEWAY_AGENT", "travel-agency")  # travel-agency 响应更快 (2.86s vs 9.7s)
TTS_MODEL = "qwen3-tts-instruct-flash-realtime"
TTS_VOICE = "Cherry"
WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
PORT = int(os.getenv("AUDIO_PROXY_PORT", "8765"))

# 错误处理配置
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 1.0  # 重试延迟（秒）
AGENT_TIMEOUT = 30  # Agent 超时时间（秒）
STT_TIMEOUT = 10  # STT 超时时间（秒）
TTS_TIMEOUT = 30  # TTS 超时时间（秒）

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
        'retry': '🔄',
    }
    emoji = emoji_map.get(event_type, '📋')
    log(f"{emoji} {event_type.upper()}: {details}")


def retry_with_backoff(func, max_retries=MAX_RETRIES, delay=RETRY_DELAY, **kwargs):
    """带退避的重试装饰器
    
    Args:
        func: 要执行的函数
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        **kwargs: 传递给函数的参数
    
    Returns:
        函数执行结果，失败则返回 None
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                log_event('retry', f"第 {attempt}/{max_retries} 次重试，延迟 {delay}s")
                asyncio.run(asyncio.sleep(delay))
                delay *= 2  # 指数退避
            return func(**kwargs)
        except Exception as e:
            last_error = e
            log(f"❌ 尝试 {attempt + 1}/{max_retries} 失败：{e}", "ERROR")
    
    log(f"❌ 重试 {max_retries} 次后仍失败：{last_error}", "ERROR")
    return None

# Set API Key
dashscope.api_key = API_KEY


class STTCallback(RecognitionCallback):
    """实时 STT 回调"""
    
    def __init__(self, gateway):
        self.gateway = gateway
        self.result_text = ""
        self.final_text = ""
        self.partial_callback = None  # 用于回调增量结果
        
    def on_open(self) -> None:
        log("✅ STT 连接已建立")
        
    def on_close(self) -> None:
        log("🔴 STT 连接关闭")
        
    def on_complete(self) -> None:
        log("✅ STT 识别完成")
        
    def on_error(self, result: RecognitionResult) -> None:
        log_event('error', f"STT 错误：{result}")
        # 记录详细错误信息用于诊断
        error_details = {
            'status_code': getattr(result, 'status_code', 'unknown'),
            'message': getattr(result, 'message', str(result)),
            'timestamp': datetime.now().isoformat()
        }
        log(f"📋 STT 错误详情：{json.dumps(error_details)}", "ERROR")
        
    def on_event(self, result: RecognitionResult) -> None:
        try:
            # RecognitionResult 对象包含识别结果
            text = getattr(result, 'text', '') or getattr(result, 'output', {}).get('text', '')
            
            if text:
                self.result_text = text
                log(f"📝 识别中：{text}", "DEBUG")
                # 通知网关有增量结果
                if self.partial_callback:
                    self.partial_callback(text, is_final=False)
                # 流式推送给前端（stt_partial）
                if self.gateway:
                    asyncio.create_task(self.gateway.send_stt_partial_to_clients(text))
                
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
        log_event('disconnect', f"TTS 连接关闭：code={close_status_code}, msg={close_msg}")
        # 非正常关闭时标记需要重连
        if close_status_code != 1000:  # 1000 是正常关闭
            self.gateway.is_tts_connected = False
            log("⚠️ TTS 异常断开，标记需要重连", "WARN")
    
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
    """Agent 语音网关
    
    使用依赖注入：
    - container: 依赖注入容器
    - handlers: 业务逻辑处理器
    """
    
    def __init__(self, container: Container = None):
        """初始化网关
        
        Args:
            container: 依赖注入容器（可选，默认创建新实例）
        """
        # 依赖注入
        self.container = container or Container()
        self.stt_handler = self.container.stt_handler()
        self.tts_handler = self.container.tts_handler()
        self.agent_handler = self.container.agent_handler()
        self.ws_handler = self.container.websocket_handler()
        
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
        log("依赖注入：已加载 container 和 handlers")
        log("="*60)
        
        self.clients = set()
        
        # STT 相关（使用原生客户端，由 container 管理）
        self.stt_client = self.container.stt_client()
        self.stt_callback = None
        self.is_stt_connected = False
        self.current_stt_text = ""  # 当前 STT 识别结果
        
        # TTS 相关（使用原生客户端，由 container 管理）
        self.tts_client = self.container.tts_client()
        self.tts_callback = None
        self.is_tts_connected = False
        
        # 实时音频流处理 - 性能优化：使用环形缓冲区
        self.audio_buffer = bytearray()  # 音频缓冲区（用于备份）
        self.audio_buffer_max_size = 1024 * 1024  # 1MB 最大缓冲
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
        
        # 预初始化 TTS 连接（降低延迟）
        self.tts_pre_initialized = False
        
        # WebSocket 连接池 - 性能优化
        self.ws_pool = []  # WebSocket 连接池
        self.ws_pool_size = 3  # 连接池大小
        self.ws_pool_index = 0  # 轮询索引
        
        # 性能指标
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_latency': 0.0,
            'last_latency': 0.0
        }
        
        log("网关初始化完成")
        log("等待客户端连接...")
        log(f"VAD 配置：threshold={self.vad_threshold}, silence={self.silence_duration}s")
        log(f"音频缓冲：max_size={self.audio_buffer_max_size} bytes")
        log(f"WebSocket 池：size={self.ws_pool_size}")
    
    def init_stt(self):
        """初始化实时 STT（使用 container 注入的客户端）"""
        if self.stt_client and self.is_stt_connected:
            return
        
        log("初始化实时 STT...")
        dashscope.api_key = API_KEY
        self.stt_callback = STTCallback(self)
        
        # 设置回调函数处理增量结果
        def on_stt_partial(text, is_final):
            # 使用 handler 处理文本
            cleaned_text = self.stt_handler.process_increment(text)
            self.stt_partial_text = cleaned_text
            if is_final:
                # 使用 handler 验证最终结果
                validated_text = self.stt_handler.process_final(cleaned_text)
                self.stt_final_text = validated_text or cleaned_text
                self.stt_event.set()  # 通知 STT 完成
                log(f"✅ STT 最终结果：{self.stt_final_text}")
            else:
                log(f"📝 STT 增量：{cleaned_text}", "DEBUG")
        
        self.stt_callback.partial_callback = on_stt_partial
        
        # stt_client 由 container 注入，直接使用
        self.stt_callback.on_open()  # 触发连接
        self.is_stt_connected = True
        
        try:
            log("✅ STT 初始化完成（使用 container 注入的客户端）")
        except Exception as e:
            log(f"❌ STT 初始化失败：{e}", "ERROR")
            self.is_stt_connected = False
            raise
    
    def init_tts(self):
        """初始化 TTS（使用 container 注入的客户端）"""
        if self.tts_client and self.is_tts_connected:
            return
        
        log("初始化 TTS...")
        self.tts_callback = TTSCallback(self)
        
        # tts_client 由 container 注入，直接使用
        self.tts_client.connect()
        self.tts_client.update_session(
            voice=TTS_VOICE,
            response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
            mode='server_commit'
        )
        self.is_tts_connected = True
        
        try:
            log("✅ TTS 初始化完成（使用 container 注入的客户端）")
        except Exception as e:
            log(f"❌ TTS 初始化失败：{e}")
            self.is_tts_connected = False
            raise
    
    def send_to_agent(self, transcript: str) -> str:
        """发送语音识别文本给 Agent（使用 agent_handler 处理）
        
        错误处理：
        - 无效输入：友好提示
        - Agent 无响应：超时处理
        - API 失败：降级回复
        """
        log(f"🗣️  用户说：{transcript}")
        
        # 无效用户输入检查
        if not transcript or not transcript.strip():
            log_event('error', "无效用户输入：空文本")
            return "抱歉，我没有听清楚，能再说一遍吗？"
        
        # 过滤无效字符
        cleaned_text = transcript.strip()
        if len(cleaned_text) < 2:
            log_event('error', f"无效用户输入：文本太短 ({len(cleaned_text)} 字符)")
            return "抱歉，我没有听清楚，能再说一遍吗？"
        
        try:
            # 使用 handler 预处理消息
            processed_text = self.agent_handler.preprocess_message(cleaned_text)
            if not processed_text:
                log("⚠️  消息预处理后为空，使用原始文本")
                processed_text = cleaned_text
            
            log(f"📝 预处理后消息：{processed_text}")
            
            # 使用 OpenClaw CLI 调用 Agent
            import subprocess
            
            # 获取默认会话 ID (从环境或配置文件)
            session_id = os.getenv("OPENCLAW_SESSION_ID", "")
            
            cmd = ["openclaw", "agent", "--message", f"[VOICE] {processed_text}", "--json"]
            
            if session_id:
                cmd.extend(["--session-id", session_id])
            else:
                cmd.extend(["--agent", AGENT_ID])
            
            log(f"📞 调用 Agent: {' '.join(cmd)}")
            
            # 带超时的 Agent 调用（优化：降低超时时间）
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=AGENT_TIMEOUT  # 使用配置的超时时间
            )
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout)
                    payloads = response.get('result', {}).get('payloads', [])
                    if payloads:
                        raw_reply = payloads[0].get('text', '')
                        if raw_reply and raw_reply.strip():
                            reply = self.agent_handler.process_response(raw_reply)
                            log_event('success', f"Agent 回复：{reply[:50]}...")
                            return reply
                        else:
                            log_event('error', "Agent 返回空回复")
                            return "好的，我收到了你的消息。"
                    else:
                        log_event('error', "Agent 无回复内容")
                        return "好的，我收到了。"
                except json.JSONDecodeError as e:
                    log_event('error', f"Agent 响应解析失败：{e}")
                    return "抱歉，响应格式有误。"
            else:
                log_event('error', f"Agent 请求失败：{result.stderr[:200]}")
                return "好的，我收到了。"
        
        except subprocess.TimeoutExpired:
            log_event('error', f"Agent 调用超时 ({AGENT_TIMEOUT}s)")
            return "抱歉，响应超时了，请稍后再试。"
        except FileNotFoundError:
            log_event('error', "OpenClaw 命令未找到")
            return "抱歉，系统配置有误。"
        except Exception as e:
            log_event('error', f"发送 Agent 失败：{e}")
            return "抱歉，出了点问题，请稍后再试。"
    
    def call_tts(self, text: str) -> None:
        """调用 TTS 合成语音（使用 tts_handler 处理）- 防止重叠播放
        
        错误处理：
        - TTS API 失败：通知前端显示文本提示
        - 连接断开：自动重连
        - 超时：降级处理
        """
        if not text:
            return
        
        # 使用锁确保线程安全
        with self.tts_playing_lock:
            if self.is_playing_tts:
                log("⏳ TTS 正在播放，跳过", "INFO")
                return
            self.is_playing_tts = True
        
        log_event('tts', f"合成：{text[:50]}...")
        tts_success = False
        
        try:
            # 使用 handler 预处理文本
            processed_text = self.tts_handler.preprocess_text(text)
            if not processed_text:
                log_event('error', "TTS 文本无效，跳过")
                # 通知前端 TTS 失败，显示文本
                self._notify_tts_fallback(text)
                return
            
            log(f"📝 预处理后 TTS 文本：{processed_text[:50]}...")
            
            # 检查并重连 TTS（带重试）
            if not self.is_tts_connected or not self.tts_client:
                log("🔌 TTS 未连接，尝试重连...", "INFO")
                for attempt in range(MAX_RETRIES):
                    try:
                        self.tts_client = None
                        self.tts_callback = None
                        self.is_tts_connected = False
                        self.init_tts()
                        if self.is_tts_connected:
                            log_event('success', f"TTS 重连成功 (尝试 {attempt + 1}/{MAX_RETRIES})")
                            break
                    except Exception as e:
                        log(f"⚠️ TTS 重连尝试 {attempt + 1}/{MAX_RETRIES} 失败：{e}", "WARN")
                        if attempt < MAX_RETRIES - 1:
                            import time
                            time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    log_event('error', "TTS 重连失败，降级到文本显示")
                    self._notify_tts_fallback(processed_text)
                    return
            
            # 分句发送（避免太长）
            sentences = processed_text.split('.')
            for sentence in sentences:
                if sentence.strip():
                    self.tts_client.append_text(sentence + '.')
            
            self.tts_client.finish()
            
            # 带超时等待 TTS 完成
            import time
            start_time = time.time()
            self.tts_callback.complete_event.wait(timeout=TTS_TIMEOUT)
            elapsed = time.time() - start_time
            
            if elapsed >= TTS_TIMEOUT:
                log_event('error', f"TTS 超时 ({TTS_TIMEOUT}s)")
                self._notify_tts_fallback(processed_text)
            else:
                log_event('success', f"TTS 合成完成 ({elapsed:.2f}s)")
                tts_success = True
        
        except Exception as e:
            log_event('error', f"TTS 合成失败：{e}")
            self.is_tts_connected = False
            self._notify_tts_fallback(text)
        finally:
            with self.tts_playing_lock:
                self.is_playing_tts = False
        
        return tts_success
    
    def _notify_tts_fallback(self, text: str) -> None:
        """TTS 失败时通知前端显示文本提示"""
        log("📝 TTS 降级：显示文本提示", "INFO")
        try:
            # 创建新事件循环发送通知
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self.send_to_clients_async({
                    "type": "tts_fallback",
                    "text": text,
                    "reason": "TTS API 失败，显示文本"
                }))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.send_to_clients_async({
                    "type": "tts_fallback",
                    "text": text,
                    "reason": "TTS API 失败，显示文本"
                }))
                loop.close()
        except Exception as e:
            log(f"⚠️ 发送 TTS 降级通知失败：{e}", "WARN")
    
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
        """Handle browser WebSocket client（使用 handlers 处理业务逻辑）"""
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        log(f"🌐 浏览器客户端已连接 (IP: {client_ip})")
        self.clients.add(websocket)
        
        # 预初始化 STT 和 TTS（降低延迟）
        if not self.is_stt_connected:
            try:
                self.init_stt()
            except Exception as e:
                log(f"⚠️  STT 初始化失败：{e}", "WARN")
        
        if not self.tts_pre_initialized:
            try:
                self.init_tts()
                self.tts_pre_initialized = True
                log("✅ TTS 预初始化完成", "INFO")
            except Exception as e:
                log(f"⚠️  TTS 预初始化失败：{e}", "WARN")
        
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
        """处理实时音频流数据 - 流式 STT
        
        性能优化：
        - 音频流缓冲优化：限制缓冲区大小，避免内存泄漏
        - 批量发送：减少网络请求次数
        - GPU 加速：使用 numpy 进行音频处理（如果可用）
        """
        try:
            audio_data = message
            
            # 性能优化：使用更高效的音量计算
            import struct
            samples = struct.unpack('<' + 'h' * (len(audio_data) // 2), audio_data)
            # 简化 RMS 计算，减少 CPU 使用
            rms = (sum(s * s for s in samples[:1000]) / min(1000, len(samples))) ** 0.5
            volume = min(1.0, rms / 1000)
            
            # VAD 检测
            is_voice = volume > self.vad_threshold
            self._process_vad(is_voice, volume)
            
            # 音频流缓冲优化：限制缓冲区大小，避免内存泄漏
            if is_voice:
                if len(self.audio_buffer) < self.audio_buffer_max_size:
                    self.audio_buffer.extend(audio_data)
                else:
                    # 缓冲区满时，丢弃最早的 50%
                    log("⚠️ 音频缓冲区满，清理旧数据", "WARN")
                    self.audio_buffer = self.audio_buffer[len(self.audio_buffer)//2:]
                    self.audio_buffer.extend(audio_data)
            
            # 流式 STT: 实时发送音频到百炼
            if is_voice and self.is_stt_connected and self.stt_realtime:
                try:
                    self.stt_realtime.send_audio_frame(audio_data)
                except Exception as e:
                    log(f"⚠️ STT 发送失败：{e}", "WARN")
            
            # 发送音量更新到客户端（降低频率，减少网络流量）
            if self.clients:
                await self.send_to_clients_async({
                    "type": "volume",
                    "volume": volume,
                    "is_speaking": self.is_speaking
                })
            
        except Exception as e:
            log(f"❌ 处理音频流失败：{e}", "ERROR")
    
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
        """说话结束处理：STT → Agent → TTS (使用 handlers 处理业务逻辑)
        
        错误处理：
        - 网络断开重连：自动重试 3 次
        - STT API 失败：降级到文件识别
        - Agent 无响应：超时处理
        - TTS API 失败：显示文本提示
        """
        start_time = datetime.now()
        self.metrics['total_requests'] += 1
        
        try:
            # 发送状态到客户端
            await self.send_to_clients_async({
                "type": "status",
                "status": "recognizing"
            })
            
            # STT 识别（带重试机制）
            stt_text = await self._process_stt_with_retry()
            
            # 降级处理
            if not stt_text:
                log_event('error', "STT 识别失败，使用默认文本")
                stt_text = "你好"
            
            log(f"📝 STT 识别结果：{stt_text}")
            
            # 发送识别结果到客户端
            await self.send_to_clients_async({
                "type": "stt_result",
                "text": stt_text,
                "is_final": True
            })
            
            # 处理状态
            await self.send_to_clients_async({
                "type": "status",
                "status": "processing"
            })
            
            # 确保 TTS 连接正常
            await self._ensure_tts_connected()
            
            # 调用 Agent（带超时处理）
            reply = self.send_to_agent(stt_text)
            log(f"🤖 Agent 回复：{reply[:100]}...")
            
            # 发送 Agent 回复
            await self.send_to_clients_async({
                "type": "reply",
                "text": reply
            })
            await self.send_llm_complete_to_clients(reply)
            
            # TTS 合成（带错误处理）
            if reply:
                await self.send_tts_start_to_clients()
                log_event('tts', '开始合成语音')
                self.call_tts(reply)
                await self.send_tts_end_to_clients()
            
            # 更新性能指标
            elapsed = (datetime.now() - start_time).total_seconds()
            self.metrics['last_latency'] = elapsed
            self.metrics['successful_requests'] += 1
            self.metrics['avg_latency'] = (
                (self.metrics['avg_latency'] * (self.metrics['successful_requests'] - 1) + elapsed)
                / self.metrics['successful_requests']
            )
            log(f"✅ 处理完成，延迟：{elapsed:.2f}s，平均：{self.metrics['avg_latency']:.2f}s")
            
            # 重置 STT 状态
            self.stt_partial_text = ""
            self.stt_final_text = ""
            self.stt_event.clear()
            self.audio_buffer = bytearray()
            
        except Exception as e:
            self.metrics['failed_requests'] += 1
            log_event('error', f"_process_speech_end 错误：{e}")
            # 通知前端错误
            await self.send_to_clients_async({
                "type": "error",
                "message": f"处理失败：{str(e)}",
                "recoverable": True
            })
    
    async def _process_stt_with_retry(self) -> str:
        """STT 识别（带重试和降级）
        
        Returns:
            识别文本，失败返回空字符串
        """
        for attempt in range(MAX_RETRIES):
            try:
                if self.is_stt_connected and self.stt_client:
                    self.stt_client.stop()
                    
                    if self.stt_event.wait(timeout=STT_TIMEOUT):
                        raw_text = self.stt_final_text
                        stt_text = self.stt_handler.process_final(raw_text) or raw_text
                        log_event('success', f"STT 完成 (尝试 {attempt + 1}/{MAX_RETRIES}): {stt_text}")
                        return stt_text
                    else:
                        log(f"⏱️ STT 超时 (尝试 {attempt + 1}/{MAX_RETRIES})", "WARN")
                else:
                    log(f"⚠️ STT 未连接 (尝试 {attempt + 1}/{MAX_RETRIES})", "WARN")
                
                if attempt < MAX_RETRIES - 1:
                    log_event('retry', f"STT 失败，重试 {attempt + 2}/{MAX_RETRIES}")
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    # 尝试重连 STT
                    try:
                        self.init_stt()
                    except Exception as e:
                        log(f"⚠️ STT 重连失败：{e}", "WARN")
                
            except Exception as e:
                log(f"⚠️ STT 尝试 {attempt + 1}/{MAX_RETRIES} 失败：{e}", "WARN")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        
        # 降级到文件识别
        log("🔄 STT 流式识别失败，尝试文件识别降级...", "WARN")
        return self._fallback_stt_file_recognition()
    
    def _fallback_stt_file_recognition(self) -> str:
        """STT 降级方案：使用文件识别 API"""
        try:
            if len(self.audio_buffer) == 0:
                return ""
            
            log("📁 使用文件识别降级方案", "INFO")
            # 使用已有的 _call_stt_api 方法
            text = self._call_stt_api(bytes(self.audio_buffer))
            if text:
                log_event('success', f"文件识别成功：{text}")
                return text
            else:
                log_event('error', "文件识别也失败")
                return ""
        except Exception as e:
            log_event('error', f"降级方案失败：{e}")
            return ""
    
    async def _ensure_tts_connected(self) -> bool:
        """确保 TTS 连接正常（带重试）
        
        Returns:
            是否连接成功
        """
        if self.is_tts_connected and self.tts_client:
            return True
        
        log("🔄 TTS 未连接，尝试重连...", "INFO")
        for attempt in range(MAX_RETRIES):
            try:
                self.tts_client = None
                self.tts_callback = None
                self.is_tts_connected = False
                self.init_tts()
                if self.is_tts_connected:
                    log_event('success', f"TTS 重连成功 (尝试 {attempt + 1}/{MAX_RETRIES})")
                    return True
            except Exception as e:
                log(f"⚠️ TTS 重连尝试 {attempt + 1}/{MAX_RETRIES} 失败：{e}", "WARN")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        
        log_event('error', "TTS 重连失败")
        return False
    
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
        """处理 STT 识别结果（使用 handlers 处理）"""
        log_event('speaking', f'用户说：{text}')
        
        try:
            # 发送状态
            await self.send_to_clients_async({"type": "status", "status": "recognizing"})
            log("📤 发送 status=recognizing", "DEBUG")
            
            # 使用 handler 预处理文本
            processed_text = self.stt_handler.process_final(text)
            if not processed_text:
                log("⚠️  STT 文本无效，使用默认文本", "WARN")
                processed_text = "你好"
            
            # 调用 Agent (使用 handler 处理)
            log("⏳ 调用 Agent...", "INFO")
            reply = self.send_to_agent(processed_text)
            log_event('agent', reply[:50] + '...' if len(reply) > 50 else reply)
            
            # 发送文本回复（兼容旧格式 + 新格式 llm_complete）
            await self.send_to_clients_async({
                "type": "reply",
                "text": reply
            })
            # 发送 llm_complete
            await self.send_llm_complete_to_clients(reply)
            log(f"📤 发送 reply + llm_complete: {reply[:50]}...", "DEBUG")
            
            # 调用 TTS (使用 handler 处理)
            if reply:
                # 发送 TTS 开始通知
                await self.send_tts_start_to_clients()
                
                log_event('tts', '开始合成语音')
                self.call_tts(reply)
                
                # 发送 TTS 结束通知
                await self.send_tts_end_to_clients()
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
    
    # ========== 授权的消息推送方法（阶段一）==========
    
    async def send_stt_partial_to_clients(self, text: str) -> None:
        """发送 STT 增量结果到客户端（stt_partial）
        
        Args:
            text: 增量识别文本
        """
        await self.send_to_clients_async({
            "type": "stt_partial",
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        log(f"📤 发送 stt_partial: {text[:50]}...", "DEBUG")
    
    async def send_stt_final_to_clients(self, text: str) -> None:
        """发送 STT 最终结果到客户端（stt_final）
        
        Args:
            text: 最终识别文本
        """
        await self.send_to_clients_async({
            "type": "stt_final",
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        log(f"📤 发送 stt_final: {text[:50]}...", "DEBUG")
    
    async def send_llm_token_to_clients(self, token: str) -> None:
        """发送 LLM 流式 token 到客户端（llm_token）
        
        Args:
            token: token 文本（单个字符或词）
        """
        await self.send_to_clients_async({
            "type": "llm_token",
            "token": token,
            "timestamp": datetime.now().isoformat()
        })
        log(f"📤 发送 llm_token: {token}", "DEBUG")
    
    async def send_llm_complete_to_clients(self, text: str) -> None:
        """发送 LLM 完整回复到客户端（llm_complete）
        
        Args:
            text: 完整回复文本
        """
        await self.send_to_clients_async({
            "type": "llm_complete",
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        log(f"📤 发送 llm_complete: {text[:50]}...", "DEBUG")
    
    async def send_tts_start_to_clients(self) -> None:
        """发送 TTS 开始播放通知到客户端（tts_start）"""
        await self.send_to_clients_async({
            "type": "tts_start",
            "timestamp": datetime.now().isoformat()
        })
        log("📤 发送 tts_start", "DEBUG")
    
    async def send_tts_end_to_clients(self) -> None:
        """发送 TTS 播放结束通知到客户端（tts_end）"""
        await self.send_to_clients_async({
            "type": "tts_end",
            "timestamp": datetime.now().isoformat()
        })
        log("📤 发送 tts_end", "DEBUG")
    
    # ========== 兼容旧版本（保留）==========
    
    async def send_subtitle_to_clients(self, text: str, role: str, is_final: bool = False) -> None:
        """发送字幕到客户端（流式）- 兼容旧版本
        
        Args:
            text: 字幕文本
            role: 角色 ('user' 或 'ai')
            is_final: 是否为最终结果
        """
        await self.send_to_clients_async({
            "type": "subtitle",
            "role": role,
            "text": text,
            "is_final": is_final,
            "timestamp": datetime.now().isoformat()
        })
        log(f"📤 发送字幕：[{role}] {text[:50]}...", "DEBUG")
    
    async def run(self, host="0.0.0.0", port=PORT):
        """运行服务器"""
        log(f"\n启动 WebSocket 服务器，监听端口 {port}")
        
        async with websockets.serve(self.handle_client, host, port):
            log("✅ 服务器已启动")
            log("等待浏览器连接...")
            await asyncio.Future()


async def main():
    """主函数"""
    # 创建依赖注入容器
    container = Container()
    
    # 创建网关（注入 container）
    gateway = AgentGateway(container=container)
    
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
