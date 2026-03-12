#!/usr/bin/env python3
"""
单独测试 TTS：文字转语音
不依赖前端，直接测试百炼 TTS API
"""

import sys
import os
import asyncio
import tempfile
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'wsl2'))

from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime, QwenTtsRealtimeCallback, AudioFormat
import dashscope
import json
import wave

# 加载配置
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

API_KEY = os.getenv('ALI_BAILIAN_API_KEY', '')
dashscope.api_key = API_KEY

# 存储音频数据
audio_chunks = []
tts_finished = False

class TTSCallback(QwenTtsRealtimeCallback):
    """TTS 回调"""
    
    def __init__(self):
        global tts_finished
        self.finished = False
    
    def on_open(self) -> None:
        print("✅ TTS 连接已建立")
    
    def on_close(self, close_status_code: int, close_msg: str) -> None:
        print(f"🔴 TTS 连接关闭：code={close_status_code}")
    
    def on_event(self, response: str) -> None:
        global audio_chunks, tts_finished
        try:
            data = json.loads(response) if isinstance(response, str) else response
            event_type = data.get('type', 'unknown')
            
            if event_type == 'session.created':
                session_id = data.get('session', {}).get('id', 'unknown')
                print(f"📋 TTS 会话创建：{session_id}")
            
            elif event_type == 'response.audio.delta':
                audio_b64 = data.get('delta', '')
                if audio_b64:
                    import base64
                    audio_data = base64.b64decode(audio_b64)
                    audio_chunks.append(audio_data)
                    print(f"🎵 收到音频块：{len(audio_data)} bytes")
            
            elif event_type == 'response.done':
                print(f"✅ TTS 响应完成，共 {len(audio_chunks)} 个音频块")
            
            elif event_type == 'session.finished':
                print(f"🔴 TTS 会话结束")
                tts_finished = True
        
        except Exception as e:
            print(f'❌ TTS 回调错误：{e}')

def test_tts():
    """测试 TTS：文字转语音"""
    global audio_chunks
    audio_chunks = []
    
    print("="*80)
    print("🧪 单独测试 TTS：文字转语音")
    print("="*80)
    
    # 创建 TTS 实例
    print("\n[1] 创建 TTS 实例...")
    tts_callback = TTSCallback()
    tts_realtime = QwenTtsRealtime(
        model='qwen3-tts-instruct-flash-realtime',
        callback=tts_callback,
    )
    
    # 连接
    print("[2] 连接 TTS 服务...")
    tts_realtime.connect()
    tts_realtime.update_session(
        voice='Cherry',
        response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
        mode='server_commit'
    )
    print("✅ TTS 已连接")
    
    # 发送文本
    print("\n[3] 发送文本：'你好！'")
    tts_realtime.append_text('你好！')
    tts_realtime.finish()
    
    # 等待完成
    print("[4] 等待 TTS 完成...")
    import time
    for i in range(30):
        time.sleep(1)
        if tts_finished:
            print("✅ TTS 完成")
            break
    else:
        print("⚠️  等待超时")
    
    # 保存音频
    print("\n[5] 保存音频...")
    if audio_chunks:
        # 合并音频
        full_audio = b''.join(audio_chunks)
        print(f"   总音频大小：{len(full_audio)} bytes")
        
        # 保存为 WAV 文件
        output_path = tempfile.mktemp(suffix='.wav')
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(1)  # 单声道
            wf.setsampwidth(2)  # 16bit
            wf.setframerate(24000)  # 24kHz
            wf.writeframes(full_audio)
        
        print(f"   保存路径：{output_path}")
        
        # 尝试播放
        print("\n[6] 尝试播放音频...")
        import subprocess
        try:
            result = subprocess.run(
                ['ffplay', '-autoexit', '-nodisp', '-loglevel', 'quiet', output_path],
                timeout=10,
                capture_output=True
            )
            print("✅ 音频播放成功")
        except subprocess.TimeoutExpired:
            print("⚠️  播放超时（可能正常）")
        except FileNotFoundError:
            print("⚠️  ffplay 未安装，跳过播放")
        except Exception as e:
            print(f"⚠️  播放失败：{e}")
        
        # 验证文件
        file_size = os.path.getsize(output_path)
        print(f"\n   WAV 文件大小：{file_size} bytes")
        
        if file_size > 44:  # WAV 头 44 bytes
            print("\n" + "="*80)
            print("✅ TTS 测试通过 - 音频生成成功")
            print("="*80)
            return 0, output_path
        else:
            print("\n" + "="*80)
            print("❌ TTS 测试失败 - 音频文件为空")
            print("="*80)
            return 1, None
    else:
        print("\n" + "="*80)
        print("❌ TTS 测试失败 - 没有收到音频数据")
        print("="*80)
        return 1, None

if __name__ == "__main__":
    exit_code, output_path = test_tts()
    if output_path:
        print(f"\n音频文件：{output_path}")
    sys.exit(exit_code)
