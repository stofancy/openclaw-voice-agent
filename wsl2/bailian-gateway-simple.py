#!/usr/bin/env python3
"""
百炼 Qwen-Omni WebSocket 网关 (简化调试版)
"""

import asyncio
import json
import os
import base64
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

import websockets
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Configuration
API_KEY = os.getenv("ALI_BAILIAN_API_KEY", "")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen3-omni-flash-2025-12-01"  # 官方推荐模型
VOICE = os.getenv("BAILIAN_VOICE", "Cherry")
PORT = int(os.getenv("AUDIO_PROXY_PORT", "8765"))

# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"gateway_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(message):
    """Simple log to file and stdout"""
    timestamp = datetime.now().isoformat()
    line = f"[{timestamp}] {message}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception as e:
        print(f"Log write error: {e}")

class SimpleGateway:
    def __init__(self):
        log("="*60)
        log("实时多模态模型测试后台服务 (简化版)")
        log("="*60)
        log(f"API Key: {API_KEY[:15]}...")
        log(f"Base URL: {BASE_URL}")
        log(f"Model: {MODEL}")
        log(f"Voice: {VOICE}")
        log(f"Port: {PORT}")
        log(f"Log file: {LOG_FILE}")
        log("="*60)
        
        # Create OpenAI client (synchronous)
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.clients = set()
        self.audio_buffer = bytearray()
        self.is_processing = False
        
        log("网关初始化完成")
        log("等待客户端连接...")
    
    async def handle_client(self, websocket):
        """Handle WebSocket client"""
        log(f"客户端已连接")
        self.clients.add(websocket)
        
        msg_count = 0
        try:
            async for message in websocket:
                msg_count += 1
                
                if isinstance(message, bytes):
                    log(f"收到二进制消息 #{msg_count}: {len(message)} bytes")
                    await self.handle_audio(message)
                else:
                    log(f"收到文本消息 #{msg_count}: {message[:100]}...")
                    await self.handle_json(message)
                    
        except websockets.exceptions.ConnectionClosed as e:
            log(f"客户端断开连接 (code: {e.code})")
        except Exception as e:
            log(f"异常：{e}")
            traceback.print_exc()
        finally:
            self.clients.discard(websocket)
            log(f"当前连接数：{len(self.clients)}")
    
    async def handle_audio(self, message):
        """Handle audio data"""
        if len(message) < 4:
            log(f"消息太短：{len(message)} bytes")
            return
        
        try:
            # Parse header
            header_len = int.from_bytes(message[:4], 'big')
            if header_len > 10000 or header_len > len(message) - 4:
                log(f"无效头部长度：{header_len}")
                return
            
            header_json = message[4:4+header_len].decode('utf-8')
            header = json.loads(header_json)
            audio_data = message[4+header_len:]
            
            # Accumulate audio
            old_size = len(self.audio_buffer)
            self.audio_buffer.extend(audio_data)
            new_size = len(self.audio_buffer)
            
            chunk_id = header.get('chunk_id', 'N/A')
            log(f"累积音频：chunk #{chunk_id}, {old_size} → {new_size} bytes")
            
        except Exception as e:
            log(f"处理音频失败：{e}")
    
    async def handle_json(self, message):
        """Handle JSON message"""
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')
            
            if msg_type == 'process':
                log(f"收到处理请求，缓冲：{len(self.audio_buffer)} bytes")
                
                if not self.is_processing and self.audio_buffer:
                    log(f"开始处理音频...")
                    self.is_processing = True
                    
                    # Run in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self.process_audio_sync)
                else:
                    log(f"跳过处理 (处理中：{self.is_processing}, 缓冲：{len(self.audio_buffer)})")
            
        except json.JSONDecodeError as e:
            log(f"JSON 解析失败：{e}")
        except Exception as e:
            log(f"处理 JSON 失败：{e}")
            traceback.print_exc()
    
    def process_audio_sync(self):
        """Process audio (synchronous, runs in executor)"""
        log(f"\n{'='*60}")
        log("开始处理音频")
        log(f"{'='*60}")
        
        if not self.audio_buffer:
            log("没有音频数据")
            self.is_processing = False
            return
        
        start_time = datetime.now()
        audio_path = None
        
        try:
            # Step 1: Create WAV file
            log("步骤 1: 创建 WAV 文件")
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                sample_rate = 16000
                channels = 1
                sample_width = 2
                
                wav_header = self._create_wav_header(len(self.audio_buffer), sample_rate, channels, sample_width)
                f.write(wav_header)
                f.write(self.audio_buffer)
                audio_path = f.name
            
            file_size = os.path.getsize(audio_path)
            log(f"WAV 文件：{audio_path} ({file_size} bytes)")
            
            # Step 2: Base64 encode
            log("步骤 2: Base64 编码")
            with open(audio_path, 'rb') as f:
                audio_base64 = base64.b64encode(f.read()).decode('utf-8')
            log(f"Base64 长度：{len(audio_base64)} chars")
            
            # Step 3: Call Bailian API
            log("步骤 3: 调用百炼 API")
            response = self.call_bailian_api_sync(audio_base64)
            
            if response:
                text_len = len(response.get('text', ''))
                audio_len = len(response.get('audio_base64', ''))
                log(f"API 响应：{text_len} chars 文本，{audio_len} chars 音频")
                
                # Step 4: Send response
                log("步骤 4: 发送响应到客户端")
                asyncio.run_coroutine_threadsafe(
                    self.send_response(response),
                    asyncio.get_event_loop()
                )
                log("响应已发送")
            else:
                log("API 返回空响应")
            
            # Step 5: Cleanup
            log("步骤 5: 清理临时文件")
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)
            self.audio_buffer = bytearray()
            log("清理完成")
            
            # Stats
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            log(f"\n处理完成，耗时：{elapsed:.0f}ms")
            log(f"{'='*60}\n")
            
        except Exception as e:
            log(f"处理失败：{e}")
            traceback.print_exc()
        finally:
            self.is_processing = False
            if audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except:
                    pass
    
    def call_bailian_api_sync(self, audio_base64):
        """Call Bailian API (synchronous)
        
        注意：Qwen-Omni-Flash 不支持音频输入！
        这里先将音频 Base64 保存，然后用纯文本测试音频输出。
        """
        try:
            log("构建请求...")
            # 官方示例：纯文本输入 → 文本 + 音频输出
            messages = [
                {
                    "role": "user",
                    "content": "你好，我是语音助手测试。请回复一段话。"
                }
            ]
            
            log("调用 OpenAI SDK (stream=True)...")
            log(f"模型：{MODEL}")
            completion = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                modalities=["text", "audio"],  # 输出文本 + 音频
                audio={"voice": VOICE, "format": "wav"},
                stream=True,
            )
            
            log("处理流式响应...")
            text = ""
            audio_base64_out = ""
            
            for chunk in completion:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    
                    if delta.content:
                        text += delta.content
                    
                    if hasattr(delta, 'audio') and delta.audio:
                        if 'data' in delta.audio:
                            audio_base64_out += delta.audio['data']
            
            log(f"API 调用成功")
            log(f"文本回复：{text[:50]}... ({len(text)} chars)")
            log(f"音频数据：{len(audio_base64_out)} chars")
            
            return {
                "text": text,
                "audio_base64": audio_base64_out,
            }
            
        except Exception as e:
            log(f"API 调用失败：{e}")
            traceback.print_exc()
            return None
    
    async def send_response(self, response):
        """Send response to clients"""
        if not self.clients:
            log("没有客户端连接")
            return
        
        response_data = {
            "type": "response",
            "text": response.get('text', ''),
            "audio_info": f"音频：{len(response.get('audio_base64', ''))} chars",
            "log_file": str(LOG_FILE),
        }
        
        response_json = json.dumps(response_data, ensure_ascii=False)
        
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(response_json)
            except Exception as e:
                log(f"发送失败：{e}")
                disconnected.add(client)
        
        self.clients -= disconnected
    
    def _create_wav_header(self, data_len, sample_rate, channels, sample_width):
        """Create WAV header"""
        import struct
        byte_rate = sample_rate * channels * sample_width
        block_align = channels * sample_width
        
        header = struct.pack('<4sI4s', b'RIFF', 36 + data_len, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, sample_width * 8)
        header += struct.pack('<4sI', b'data', data_len)
        return header
    
    async def run(self):
        """Run the server"""
        log(f"\n启动 WebSocket 服务器，监听端口 {PORT}")
        
        async with websockets.serve(self.handle_client, "0.0.0.0", PORT):
            log("服务器已启动")
            await asyncio.Future()

if __name__ == "__main__":
    gateway = SimpleGateway()
    asyncio.run(gateway.run())
