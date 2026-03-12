#!/usr/bin/env python3
"""
百炼 Qwen-Omni WebSocket 网关
接收浏览器音频 → 调用百炼 API → 返回响应
"""

import asyncio
import json
import os
import base64
import tempfile
from datetime import datetime
from pathlib import Path

import websockets
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Configuration
API_KEY = os.getenv("ALI_BAILIAN_API_KEY")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = os.getenv("BAILIAN_MODEL", "qwen3-omni-flash")
VOICE = os.getenv("BAILIAN_VOICE", "Cherry")
PORT = int(os.getenv("AUDIO_PROXY_PORT", "8765"))

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "test_audio"
OUTPUT_DIR.mkdir(exist_ok=True)


class BailianGateway:
    """百炼网关"""
    
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.clients = set()
        self.audio_buffer = bytearray()
        self.is_processing = False
        
    async def handle_client(self, websocket):
        """处理客户端连接"""
        self.clients.add(websocket)
        print(f"{'='*60}")
        print(f"✅ 客户端已连接，当前连接数：{len(self.clients)}")
        print(f"   WebSocket: {websocket}")
        print(f"   时间：{datetime.now().isoformat()}")
        print(f"{'='*60}")
        
        try:
            msg_count = 0
            async for message in websocket:
                msg_count += 1
                msg_type = type(message).__name__
                
                if msg_type == 'bytes':
                    print(f"📨 #{msg_count}: 二进制 {len(message)} bytes")
                    await self.handle_audio(message)
                else:
                    print(f"📨 #{msg_count}: 文本 '{message[:200]}'")
                    await self.handle_json(message)
                    
            print(f"🔴 客户端断开，共收到 {msg_count} 条消息")
            
        except Exception as e:
            print(f"❌ 异常：{e}")
            import traceback
            traceback.print_exc()
        finally:
            self.clients.discard(websocket)
            print(f"当前连接数：{len(self.clients)}")
    
    async def handle_audio(self, message):
        """处理音频数据"""
        try:
            print(f"   ├─ 消息长度：{len(message)} bytes")
            
            if len(message) < 4:
                print(f"   ⚠️  消息太短：{len(message)}")
                return
            
            # 解析头部
            header_len = int.from_bytes(message[:4], 'big')
            print(f"   ├─ 头部长度：{header_len} bytes")
            
            # 安全检查
            if header_len > 10000 or header_len > len(message) - 4:
                print(f"   ⚠️  无效的头部长度：{header_len}, 消息长度：{len(message)}")
                return
            
            header_json = message[4:4+header_len].decode('utf-8')
            header = json.loads(header_json)
            audio_data = message[4+header_len:]
            
            print(f"   ├─ 头部：{header_json[:100]}...")
            print(f"   ├─ 音频数据：{len(audio_data)} bytes")
            
            # 累积音频
            self.audio_buffer.extend(audio_data)
            
            # 调试日志
            chunk_id = header.get('chunk_id', 0)
            msg_type = header.get('type', 'unknown')
            print(f"   ✅ 累积：{msg_type} #{chunk_id}, 总缓冲：{len(self.audio_buffer)} bytes")
                
        except Exception as e:
            print(f"   ❌ 处理音频失败：{e}")
            import traceback
            traceback.print_exc()
    
    async def handle_json(self, message):
        """处理 JSON 消息"""
        try:
            print(f"   ├─ JSON 消息：{message[:200]}...")
            
            data = json.loads(message)
            msg_type = data.get('type')
            print(f"   ├─ 消息类型：{msg_type}")
            
            if msg_type == 'state':
                state = data.get('state')
                print(f"   ├─ 状态：{state}")
                if state == 'PROCESSING' and not self.is_processing:
                    print(f"   ✅ 触发处理")
                    self.is_processing = True
                    await self.process_audio()
            elif msg_type == 'process':
                # 浏览器发送的处理信号
                print(f"   🔄 收到处理请求")
                print(f"   ├─ 时间戳：{data.get('timestamp', 'N/A')}")
                print(f"   ├─ 音频缓冲：{len(self.audio_buffer)} bytes")
                print(f"   ├─ 处理中：{self.is_processing}")
                if not self.is_processing and self.audio_buffer:
                    print(f"   ✅ 开始处理音频")
                    self.is_processing = True
                    await self.process_audio()
                else:
                    print(f"   ⚠️  跳过处理 (处理中：{self.is_processing}, 缓冲：{len(self.audio_buffer)})")
            else:
                print(f"   ⚠️  未知消息类型：{msg_type}")
                
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON 解析失败：{e}")
        except Exception as e:
            print(f"   ❌ 处理 JSON 失败：{e}")
            import traceback
            traceback.print_exc()
    
    async def process_audio(self):
        """处理累积的音频"""
        print(f"\n{'='*60}")
        print(f"🔄 开始处理音频")
        print(f"{'='*60}")
        print(f"   音频缓冲：{len(self.audio_buffer)} bytes")
        print(f"   时间：{datetime.now().isoformat()}")
        
        if not self.audio_buffer:
            print(f"   ⚠️  没有音频数据")
            self.is_processing = False
            return
        
        start_time = datetime.now()
        
        try:
            # 保存为临时 WAV 文件
            print(f"   ├─ 创建 WAV 文件...")
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                sample_rate = 16000
                channels = 1
                sample_width = 2
                
                f.write(self._create_wav_header(len(self.audio_buffer), sample_rate, channels, sample_width))
                f.write(self.audio_buffer)
                audio_path = f.name
            
            print(f"   ✅ 临时文件：{audio_path}")
            print(f"   ├─ 文件大小：{os.path.getsize(audio_path)} bytes")
            
            # 编码为 Base64
            print(f"   ├─ 编码 Base64...")
            with open(audio_path, 'rb') as f:
                audio_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            print(f"   ✅ Base64 长度：{len(audio_base64)} chars")
            
            # 调用百炼 API
            print(f"   ├─ 调用百炼 API...")
            print(f"   ├─ 模型：{MODEL}")
            print(f"   ├─ 音色：{VOICE}")
            response = await self.call_bailian_api(audio_base64)
            
            if response:
                print(f"   ✅ API 响应：{len(response.get('text', ''))} chars 文本，{len(response.get('audio_base64', ''))} chars 音频")
                
                # 发送响应到客户端
                print(f"   ├─ 发送响应到客户端...")
                await self.send_response(response)
                print(f"   ✅ 响应已发送")
            else:
                print(f"   ⚠️  API 返回空响应")
            
            # 清理
            os.unlink(audio_path)
            self.audio_buffer = bytearray()
            
            # 统计
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            print(f"\n✅ 处理完成，耗时：{elapsed:.0f}ms")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n❌ 处理失败：{e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
        finally:
            self.is_processing = False
    
    async def call_bailian_api(self, audio_base64):
        """调用百炼 API"""
        try:
            print(f"      ├─ 构建请求...")
            
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": f"data:;base64,{audio_base64[:100]}...",  # 只显示前 100 字符
                                "format": "wav",
                            },
                        },
                        {"type": "text", "text": "请识别这段音频并回复。"},
                    ],
                }
            ]
            
            print(f"      ├─ 调用 OpenAI SDK...")
            print(f"      ├─ Base URL: {BASE_URL}")
            print(f"      ├─ 模型：{MODEL}")
            
            # 调用 API
            completion = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                modalities=["text", "audio"],
                audio={"voice": VOICE, "format": "wav"},
                stream=False,
            )
            
            print(f"      ✅ API 调用成功")
            
            # 解析响应
            text = completion.choices[0].message.content
            print(f"      ├─ 文本回复：{text[:50]}...")
            
            # 提取音频
            audio_base64_out = ""
            if hasattr(completion.choices[0].message, 'audio'):
                audio_base64_out = completion.choices[0].message.audio.get('data', '')
                print(f"      ├─ 音频数据：{len(audio_base64_out)} chars")
            
            return {
                "text": text,
                "audio_base64": audio_base64_out,
            }
            
        except Exception as e:
            print(f"      ❌ API 调用失败：{e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def send_response(self, response):
        """发送响应到客户端"""
        if not self.clients:
            print("⚠️  没有客户端")
            return
        
        # 保存音频
        audio_info = ""
        if response.get('audio_base64'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_path = OUTPUT_DIR / f"gateway_reply_{timestamp}.wav"
            
            with open(audio_path, "wb") as f:
                f.write(base64.b64decode(response['audio_base64']))
            
            audio_info = f"音频：{audio_path} ({len(response['audio_base64'])/1024:.1f} KB)"
            print(f"💾 {audio_info}")
        
        # 发送 JSON 响应
        response_data = {
            "type": "response",
            "text": response.get('text', ''),
            "audio_info": audio_info,
        }
        
        for client in self.clients:
            try:
                await client.send(json.dumps(response_data))
            except Exception as e:
                print(f"❌ 发送失败：{e}")
    
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
        print("="*60)
        print("🎧 百炼 Qwen-Omni WebSocket 网关")
        print("="*60)
        print(f"✅ API Key: {API_KEY[:15]}...")
        print(f"✅ 模型：{MODEL}")
        print(f"✅ 音色：{VOICE}")
        print(f"✅ 端口：{PORT}")
        print("="*60)
        print("等待客户端连接...\n")
        
        async with websockets.serve(self.handle_client, "0.0.0.0", PORT):
            await asyncio.Future()


async def main():
    gateway = BailianGateway()
    await gateway.run()


if __name__ == "__main__":
    asyncio.run(main())
