#!/usr/bin/env python3
"""
简化的 STT 测试 - 验证连接和基本功能
"""
import os
import sys
import time
import json
import threading
import base64

# 测试文本
TEST_TEXT = "你好"

def test_stt_simple():
    """简化版 STT 测试"""
    print("=" * 60)
    print("简化版 STT 测试")
    print("=" * 60)
    
    # 加载 API Key
    api_key = None
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('ALI_BAILIAN_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    
    print(f"API Key: {api_key[:10]}...")
    
    # 创建短音频 (1秒 PCM)
    import wave
    import math
    
    # 生成 1 秒的 440Hz 正弦波
    sample_rate = 16000
    duration = 1
    frequency = 440
    
    audio_data = []
    for i in range(int(sample_rate * duration)):
        value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        audio_data.append(value.to_bytes(2, 'little', signed=True))
    audio_bytes = b''.join(audio_data)
    
    # 保存为 WAV
    wav_path = "test_1sec.wav"
    with wave.open(wav_path, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(audio_bytes)
    
    print(f"已生成测试音频: {wav_path}")
    
    # 读取音频
    with open(wav_path, 'rb') as f:
        pcm_data = f.read()
    
    print(f"PCM 大小: {len(pcm_data)} 字节")
    
    import websocket as ws_client
    
    results = []
    
    def on_message(ws, message):
        try:
            data = json.loads(message)
            event_type = data.get("type", "")
            print(f"📥 收到事件: {event_type}")
            
            if "transcription" in event_type and "text" in event_type:
                transcript = data.get("transcript", "")
                if transcript:
                    print(f"📝 转录: '{transcript}'")
                    results.append(transcript)
                    
        except Exception as e:
            print(f"解析错误: {e}")
    
    def on_error(ws, error):
        print(f"❌ 错误: {error}")
    
    def on_close(ws, status, msg):
        print(f"🔒 连接关闭: {status} - {msg}")
        if results:
            print(f"📤 最终结果: {''.join(results)}")
    
    def on_open(ws):
        print("🔌 已连接")
        
        # 发送 session.update
        event = {
            "event_id": "event_1",
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "input_audio_format": "pcm",
                "sample_rate": 16000,
                "input_audio_transcription": {"language": "zh"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.2,
                    "silence_duration_ms": 800
                }
            }
        }
        ws.send(json.dumps(event))
        print("📤 已发送 session.update")
        
        # 等待 3 秒
        time.sleep(3)
        
        # 发送音频 (分块)
        chunk_size = 3200
        total_sent = 0
        for i in range(0, len(pcm_data), chunk_size):
            chunk = pcm_data[i:i+chunk_size]
            encoded = base64.b64encode(chunk).decode('utf-8')
            
            eventd = {
                "event_id": f"event_{i}",
                "type": "input_audio_buffer.append",
                "audio": encoded
            }
            ws.send(json.dumps(eventd))
            total_sent += 1
            time.sleep(0.1)  # 模拟实时
        
        print(f"📤 已发送 {total_sent} 个音频块")
        
        # 等待结果
        time.sleep(10)
        ws.close()
    
    # 创建 WebSocket
    model = "qwen3-asr-flash-realtime-2026-02-10"
    url = f"wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model={model}"
    
    ws = ws_client.WebSocketApp(
        url,
        header=[
            f"Authorization: Bearer {api_key}",
            "OpenAI-Beta: realtime=v1"
        ],
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    print("🚀 启动 WebSocket...")
    ws.run_forever()


if __name__ == "__main__":
    test_stt_simple()
