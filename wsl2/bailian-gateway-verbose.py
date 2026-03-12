#!/usr/bin/env python3
"""
百炼 Qwen-Omni WebSocket 网关 (详细日志版)
接收浏览器音频 → 调用百炼 API → 返回响应
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
MODEL = os.getenv("BAILIAN_MODEL", "qwen3-omni-flash")
VOICE = os.getenv("BAILIAN_VOICE", "Cherry")
PORT = int(os.getenv("AUDIO_PROXY_PORT", "8765"))

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "test_audio"
OUTPUT_DIR.mkdir(exist_ok=True)

# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def save_debug_log(log_data):
    """保存调试日志到文件"""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().isoformat()}] {json.dumps(log_data, ensure_ascii=False)}\n")
    except Exception as e:
        print(f"❌ 保存日志失败：{e}")


def log_print(level, category, message, indent=0):
    """统一的日志输出函数"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    prefix = "  " * indent
    emojis = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARN": "⚠️",
        "RECV": "📨",
        "SEND": "📤",
        "PROC": "🔄",
        "API": "🤖",
        "FILE": "💾",
        "CONN": "🔌",
    }
    emoji = emojis.get(category, "•")
    print(f"{prefix}[{timestamp}] {emoji} [{level:7}] {message}", flush=True)


class BailianGateway:
    """百炼网关"""
    
    def __init__(self):
        log_print("INFO", "INIT", "初始化网关...")
        log_print("INFO", "INIT", f"  API Key: {API_KEY[:15]}..." if API_KEY else "  API Key: 未配置")
        log_print("INFO", "INIT", f"  Base URL: {BASE_URL}")
        log_print("INFO", "INIT", f"  模型：{MODEL}")
        log_print("INFO", "INIT", f"  音色：{VOICE}")
        log_print("INFO", "INIT", f"  端口：{PORT}")
        
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.clients = set()
        self.audio_buffer = bytearray()
        self.is_processing = False
        self.connection_count = 0
        
        log_print("SUCCESS", "INIT", "网关初始化完成")
    
    async def handle_client(self, websocket):
        """处理客户端连接"""
        self.connection_count += 1
        conn_id = self.connection_count
        self.clients.add(websocket)
        
        log_print("INFO", "CONN", f"="*60)
        log_print("INFO", "CONN", f"新客户端连接 #{conn_id}")
        log_print("INFO", "CONN", f"  当前连接数：{len(self.clients)}")
        log_print("INFO", "CONN", f"  时间：{datetime.now().isoformat()}")
        log_print("INFO", "CONN", f"="*60)
        
        # 保存连接事件
        save_debug_log({
            "event": "client_connected",
            "conn_id": conn_id,
            "total_clients": len(self.clients)
        })
        
        msg_count = 0
        bytes_received = 0
        debug_log_count = 0
        
        try:
            async for message in websocket:
                msg_count += 1
                bytes_received += len(message) if hasattr(message, '__len__') else 0
                
                if isinstance(message, bytes):
                    log_print("INFO", "RECV", f"消息 #{msg_count}: 二进制 {len(message)} bytes")
                    save_debug_log({
                        "event": "binary_message",
                        "msg_id": msg_count,
                        "size": len(message)
                    })
                    await self.handle_audio(message, msg_count)
                else:
                    # 解析 JSON 消息
                    try:
                        data = json.loads(message)
                        msg_type = data.get('type', 'unknown')
                        
                        # 处理调试日志
                        if msg_type == 'debug_log':
                            debug_log_count += 1
                            save_debug_log({
                                "event": "frontend_debug_log",
                                "log_id": debug_log_count,
                                "data": data
                            })
                            # 每 50 条日志打印一次摘要
                            if debug_log_count % 50 == 0:
                                log_print("INFO", "DEBUG", f"已收到 {debug_log_count} 条调试日志")
                        else:
                            log_print("INFO", "RECV", f"消息 #{msg_count}: 文本 '{message[:100]}...'")
                            save_debug_log({
                                "event": "json_message",
                                "msg_id": msg_count,
                                "type": msg_type,
                                "data": data
                            })
                            await self.handle_json(message, msg_count)
                    except json.JSONDecodeError as e:
                        log_print("ERROR", "RECV", f"JSON 解析失败：{e}")
                        save_debug_log({
                            "event": "json_decode_error",
                            "msg_id": msg_count,
                            "error": str(e)
                        })
                    
            log_print("INFO", "CONN", f"客户端断开，共收到 {msg_count} 条消息 ({bytes_received} bytes, {debug_log_count} 条调试日志)")
            save_debug_log({
                "event": "client_disconnected",
                "conn_id": conn_id,
                "total_messages": msg_count,
                "total_bytes": bytes_received,
                "debug_logs": debug_log_count
            })
            
        except websockets.exceptions.ConnectionClosed as e:
            log_print("WARN", "CONN", f"连接关闭 (代码：{e.code}, 原因：{e.reason})")
        except Exception as e:
            log_print("ERROR", "CONN", f"异常：{e}")
            traceback.print_exc()
        finally:
            self.clients.discard(websocket)
            log_print("INFO", "CONN", f"当前连接数：{len(self.clients)}")
    
    async def handle_audio(self, message, msg_id):
        """处理音频数据"""
        log_print("INFO", "PROC", f"┌─ 处理音频消息 #{msg_id}")
        save_debug_log({
            "event": "handle_audio_start",
            "msg_id": msg_id,
            "message_size": len(message)
        })
        
        try:
            if len(message) < 4:
                log_print("WARN", "PROC", f"│  ⚠️ 消息太短：{len(message)} bytes")
                save_debug_log({
                    "event": "handle_audio_error",
                    "msg_id": msg_id,
                    "reason": "message_too_short",
                    "size": len(message)
                })
                return
            
            # 解析头部长度 (大端序)
            header_len = int.from_bytes(message[:4], 'big')
            log_print("INFO", "PROC", f"│  头部长度：{header_len} bytes")
            save_debug_log({
                "event": "handle_audio_header",
                "msg_id": msg_id,
                "header_len": header_len
            })
            
            # 安全检查
            if header_len > 10000 or header_len > len(message) - 4:
                log_print("ERROR", "PROC", f"│  ❌ 无效头部长度：{header_len}, 消息：{len(message)}")
                save_debug_log({
                    "event": "handle_audio_error",
                    "msg_id": msg_id,
                    "reason": "invalid_header",
                    "header_len": header_len,
                    "message_len": len(message)
                })
                return
            
            # 解析头部 JSON
            header_json = message[4:4+header_len].decode('utf-8')
            header = json.loads(header_json)
            audio_data = message[4+header_len:]
            
            log_print("INFO", "PROC", f"│  头部：{header_json[:80]}...")
            log_print("INFO", "PROC", f"│  音频数据：{len(audio_data)} bytes")
            save_debug_log({
                "event": "handle_audio_parsed",
                "msg_id": msg_id,
                "header": header,
                "audio_size": len(audio_data)
            })
            
            # 累积音频
            old_size = len(self.audio_buffer)
            self.audio_buffer.extend(audio_data)
            new_size = len(self.audio_buffer)
            
            chunk_id = header.get('chunk_id', 'N/A')
            msg_type = header.get('type', 'unknown')
            log_print("SUCCESS", "PROC", f"│  ✅ 累积：{msg_type} #{chunk_id}, {old_size} → {new_size} bytes")
            
        except Exception as e:
            log_print("ERROR", "PROC", f"│  ❌ 处理音频失败：{e}")
            traceback.print_exc()
        
        log_print("INFO", "PROC", f"└─ 音频消息处理完成")
    
    async def handle_json(self, message, msg_id):
        """处理 JSON 消息"""
        log_print("INFO", "PROC", f"┌─ 处理 JSON 消息 #{msg_id}")
        
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')
            log_print("INFO", "PROC", f"│  消息类型：{msg_type}")
            
            if msg_type == 'state':
                state = data.get('state', 'N/A')
                log_print("INFO", "PROC", f"│  状态：{state}")
                
            elif msg_type == 'process':
                timestamp = data.get('timestamp', 'N/A')
                log_print("INFO", "PROC", f"│  时间戳：{timestamp}")
                log_print("INFO", "PROC", f"│  当前音频缓冲：{len(self.audio_buffer)} bytes")
                log_print("INFO", "PROC", f"│  处理中：{self.is_processing}")
                save_debug_log({
                    "event": "process_message_received",
                    "msg_id": msg_id,
                    "timestamp": timestamp,
                    "buffer_size": len(self.audio_buffer),
                    "is_processing": self.is_processing
                })
                
                if not self.is_processing and self.audio_buffer:
                    log_print("SUCCESS", "PROC", f"│  ✅ 触发音频处理")
                    save_debug_log({
                        "event": "audio_processing_triggered",
                        "msg_id": msg_id,
                        "buffer_size": len(self.audio_buffer)
                    })
                    self.is_processing = True
                    await self.process_audio()
                else:
                    log_print("WARN", "PROC", f"│  ⚠️ 跳过处理 (处理中：{self.is_processing}, 缓冲：{len(self.audio_buffer)})")
                    save_debug_log({
                        "event": "audio_processing_skipped",
                        "msg_id": msg_id,
                        "reason": "already_processing" if self.is_processing else "no_audio_buffer",
                        "buffer_size": len(self.audio_buffer),
                        "is_processing": self.is_processing
                    })
            
            else:
                log_print("WARN", "PROC", f"│  ⚠️ 未知消息类型：{msg_type}")
                
        except json.JSONDecodeError as e:
            log_print("ERROR", "PROC", f"│  ❌ JSON 解析失败：{e}")
        except Exception as e:
            log_print("ERROR", "PROC", f"│  ❌ 处理 JSON 失败：{e}")
            traceback.print_exc()
        
        log_print("INFO", "PROC", f"└─ JSON 消息处理完成")
    
    async def process_audio(self):
        """处理累积的音频"""
        log_print("INFO", "PROC", f"\n{'='*70}")
        log_print("INFO", "PROC", f"开始处理音频")
        log_print("INFO", "PROC", f"{'='*70}")
        log_print("INFO", "PROC", f"音频缓冲：{len(self.audio_buffer)} bytes")
        log_print("INFO", "PROC", f"时间：{datetime.now().isoformat()}")
        
        # 保存调试日志
        save_debug_log({
            "event": "process_audio_started",
            "buffer_size": len(self.audio_buffer),
            "timestamp": datetime.now().isoformat()
        })
        
        if not self.audio_buffer:
            log_print("WARN", "PROC", f"没有音频数据")
            save_debug_log({
                "event": "process_audio_error",
                "reason": "no_audio_buffer"
            })
            self.is_processing = False
            return
        
        start_time = datetime.now()
        
        try:
            # 1. 创建 WAV 文件
            log_print("INFO", "FILE", f"┌─ 步骤 1: 创建 WAV 文件")
            save_debug_log({
                "event": "process_audio_step1",
                "step": "create_wav_file",
                "buffer_size": len(self.audio_buffer),
                "start_time": start_time.isoformat()
            })
            
            try:
                sample_rate = 16000
                channels = 1
                sample_width = 2
                
                log_print("INFO", "FILE", f"│  ├─ 创建临时文件...")
                save_debug_log({"event": "wav_create_temp"})
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    log_print("INFO", "FILE", f"│  ├─ 写入 WAV 头...")
                    save_debug_log({"event": "wav_write_header"})
                    
                    wav_header = self._create_wav_header(len(self.audio_buffer), sample_rate, channels, sample_width)
                    f.write(wav_header)
                    
                    log_print("INFO", "FILE", f"│  ├─ 写入音频数据...")
                    save_debug_log({"event": "wav_write_audio", "audio_size": len(self.audio_buffer)})
                    
                    f.write(self.audio_buffer)
                    audio_path = f.name
                
                log_print("INFO", "FILE", f"│  ├─ 临时文件已创建：{audio_path}")
                save_debug_log({"event": "wav_temp_created", "path": audio_path})
                
            except Exception as e:
                log_print("ERROR", "FILE", f"│  ❌ WAV 文件创建失败：{e}")
                save_debug_log({
                    "event": "wav_create_error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
                raise
            
            file_size = os.path.getsize(audio_path)
            log_print("SUCCESS", "FILE", f"│  ✅ 文件：{audio_path}")
            log_print("INFO", "FILE", f"│  大小：{file_size} bytes (WAV 头：{len(wav_header)} bytes)")
            log_print("INFO", "FILE", f"└─ WAV 文件创建完成")
            save_debug_log({
                "event": "process_audio_step1_done",
                "audio_path": audio_path,
                "file_size": file_size,
                "header_size": len(wav_header)
            })
            
            file_size = os.path.getsize(audio_path)
            log_print("SUCCESS", "FILE", f"│  ✅ 文件：{audio_path}")
            log_print("INFO", "FILE", f"│  大小：{file_size} bytes (WAV 头：{len(wav_header)} bytes)")
            log_print("INFO", "FILE", f"└─ WAV 文件创建完成")
            save_debug_log({
                "event": "process_audio_step1_done",
                "audio_path": audio_path,
                "file_size": file_size
            })
            
            # 2. Base64 编码
            log_print("INFO", "PROC", f"┌─ 步骤 2: Base64 编码")
            save_debug_log({
                "event": "process_audio_step2",
                "step": "base64_encode",
                "audio_path": audio_path
            })
            
            with open(audio_path, 'rb') as f:
                audio_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            log_print("SUCCESS", "PROC", f"│  ✅ Base64 长度：{len(audio_base64)} chars")
            log_print("INFO", "PROC", f"└─ Base64 编码完成")
            save_debug_log({
                "event": "process_audio_step2_done",
                "base64_length": len(audio_base64)
            })
            
            # 3. 调用百炼 API
            log_print("INFO", "API", f"┌─ 步骤 3: 调用百炼 API")
            log_print("INFO", "API", f"│  Base URL: {BASE_URL}")
            save_debug_log({
                "event": "process_audio_step3",
                "step": "call_bailian_api",
                "base64_length": len(audio_base64)
            })
            log_print("INFO", "API", f"│  模型：{MODEL}")
            log_print("INFO", "API", f"│  音色：{VOICE}")
            
            response = await self.call_bailian_api(audio_base64)
            
            if response:
                text_len = len(response.get('text', ''))
                audio_len = len(response.get('audio_base64', ''))
                log_print("SUCCESS", "API", f"│  ✅ API 响应：{text_len} chars 文本，{audio_len} chars 音频")
                log_print("INFO", "API", f"└─ API 调用完成")
                
                # 4. 发送响应
                log_print("INFO", "SEND", f"┌─ 步骤 4: 发送响应到客户端")
                await self.send_response(response)
                log_print("SUCCESS", "SEND", f"│  ✅ 响应已发送到 {len(self.clients)} 个客户端")
                log_print("INFO", "SEND", f"└─ 响应发送完成")
            else:
                log_print("ERROR", "API", f"│  ❌ API 返回空响应")
            
            # 5. 清理
            log_print("INFO", "FILE", f"┌─ 步骤 5: 清理临时文件")
            os.unlink(audio_path)
            self.audio_buffer = bytearray()
            log_print("SUCCESS", "FILE", f"│  ✅ 文件已删除，缓冲区已清空")
            log_print("INFO", "FILE", f"└─ 清理完成")
            
            # 6. 统计
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            log_print("INFO", "PROC", f"\n{'='*70}")
            log_print("SUCCESS", "PROC", f"处理完成，耗时：{elapsed:.0f}ms")
            log_print("INFO", "PROC", f"{'='*70}\n")
            
        except Exception as e:
            log_print("ERROR", "PROC", f"\n❌ 处理失败：{e}")
            traceback.print_exc()
            log_print("INFO", "PROC", f"{'='*70}\n")
        finally:
            self.is_processing = False
    
    async def call_bailian_api(self, audio_base64):
        """调用百炼 API"""
        try:
            # 构建消息 (使用完整的 audio_base64)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": f"data:;base64,{audio_base64}",  # 使用完整数据
                                "format": "wav",
                            },
                        },
                        {"type": "text", "text": "请识别这段音频并回复。"},
                    ],
                }
            ]
            
            log_print("INFO", "API", f"│  ├─ 发送请求到 OpenAI SDK (stream=True)...")
            
            # 调用 API (必须使用流式)
            completion = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                modalities=["text", "audio"],
                audio={"voice": VOICE, "format": "wav"},
                stream=True,  # 必须为 True
            )
            
            # 处理流式响应
            log_print("INFO", "API", f"│  ├─ 处理流式响应...")
            text = ""
            audio_base64_out = ""
            
            for chunk in completion:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    
                    # 收集文本
                    if delta.content:
                        text += delta.content
                    
                    # 收集音频
                    if hasattr(delta, 'audio') and delta.audio:
                        if 'data' in delta.audio:
                            audio_base64_out += delta.audio['data']
            
            log_print("SUCCESS", "API", f"│  ├─ API 调用成功")
            log_print("INFO", "API", f"│  ├─ 文本回复：{text[:50]}... ({len(text)} chars)")
            log_print("INFO", "API", f"│  ├─ 音频数据：{len(audio_base64_out)} chars")
            
            return {
                "text": text,
                "audio_base64": audio_base64_out,
            }
            
        except Exception as e:
            log_print("ERROR", "API", f"│  ❌ API 调用失败：{e}")
            traceback.print_exc()
            return None
    
    async def send_response(self, response):
        """发送响应到客户端"""
        if not self.clients:
            log_print("WARN", "SEND", f"没有客户端连接")
            return
        
        response_data = {
            "type": "response",
            "text": response.get('text', ''),
            "audio_info": f"音频：{len(response.get('audio_base64', ''))} chars",
        }
        
        # 添加日志确认
        response_data["debug_log_ack"] = f"日志已保存到：{LOG_FILE}"
        
        response_json = json.dumps(response_data, ensure_ascii=False)
        
        log_print("INFO", "SEND", f"发送响应到 {len(self.clients)} 个客户端")
        save_debug_log({
            "event": "response_sent",
            "clients": len(self.clients),
            "text_length": len(response.get('text', '')),
            "audio_length": len(response.get('audio_base64', ''))
        })
        
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(response_json)
            except Exception as e:
                log_print("ERROR", "SEND", f"发送失败：{e}")
                disconnected.add(client)
        
        # 清理断开的客户端
        self.clients -= disconnected
    
    def _create_wav_header(self, data_len, sample_rate, channels, sample_width):
        """创建 WAV 头"""
        import struct
        byte_rate = sample_rate * channels * sample_width
        block_align = channels * sample_width
        
        header = struct.pack('<4sI4s', b'RIFF', 36 + data_len, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, sample_width * 8)
        header += struct.pack('<4sI', b'data', data_len)
        return header
    
    async def run(self):
        """运行服务器"""
        log_print("INFO", "INIT", f"\n{'='*70}")
        log_print("INFO", "INIT", f"实时多模态模型测试后台服务")
        log_print("INFO", "INIT", f"{'='*70}")
        log_print("INFO", "INIT", f"监听端口：{PORT}")
        log_print("INFO", "INIT", f"日志文件：{LOG_FILE}")
        log_print("INFO", "INIT", f"等待客户端连接...\n")
        
        # 保存启动信息
        save_debug_log({
            "event": "service_started",
            "port": PORT,
            "log_file": str(LOG_FILE)
        })
        
        async with websockets.serve(self.handle_client, "0.0.0.0", PORT):
            await asyncio.Future()


async def main():
    gateway = BailianGateway()
    await gateway.run()


if __name__ == "__main__":
    asyncio.run(main())
