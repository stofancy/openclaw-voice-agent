#!/usr/bin/env python3
"""
TTS → STT 闭环测试 (按官方示例修复版)
"""
import os
import sys
import asyncio
import base64
import time
import json
import threading

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from voice_gateway.tts_service import TTSService

# 测试文本
TEST_TEXT = "你好，请帮我查询北京的天气"

async def test_tts():
    """测试 TTS 服务并保存音频"""
    print("=" * 60)
    print("步骤 1: 测试 TTS 服务")
    print("=" * 60)
    
    # 加载 API Key
    api_key = None
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('ALI_BAILIAN_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    
    if not api_key:
        print("❌ 未找到有效的 API Key")
        return None
    
    # 创建 TTS 服务
    tts_service = TTSService(api_key)
    
    print(f"📝 输入文本: {TEST_TEXT}")
    
    try:
        # 生成语音
        result = await tts_service.synthesize(TEST_TEXT, voice="Cherry")
        
        if result:
            audio_bytes = base64.b64decode(result)
            if audio_bytes[:4] == b'RIFF':
                print(f"✅ TTS 成功! 音频大小: {len(audio_bytes)} 字节 (WAV格式)")
                pcm_data = audio_bytes[44:]
                print(f"   PCM 数据大小: {len(pcm_data)} 字节")
            else:
                pcm_data = audio_bytes
            
            # 保存 PCM 文件
            pcm_path = "test_audio.pcm"
            with open(pcm_path, 'wb') as f:
                f.write(pcm_data)
            print(f"💾 已保存 PCM 到: {pcm_path}")
            
            return pcm_path
        else:
            print("❌ TTS 失败: 返回 None")
            return None
            
    except Exception as e:
        print(f"💥 TTS 异常: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_stt_official(pcm_path):
    """使用官方示例代码测试 STT"""
    print("\n" + "=" * 60)
    print("步骤 2: 测试 STT 服务 (官方示例方式)")
    print("=" * 60)
    
    if not pcm_path or not os.path.exists(pcm_path):
        print("❌ PCM 文件不存在")
        return None
    
    import websocket as ws_client
    from queue import Queue
    
    # 加载 API Key
    api_key = None
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('ALI_BAILIAN_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    
    result_queue = Queue()
    transcript_parts = []  # 收集所有转录片段
    
    # WebSocket 回调
    def on_message(ws, message):
        try:
            data = json.loads(message)
            event_type = data.get("type", "")
            print(f"STT received: {event_type}")
            
            # 检查转录结果
            if event_type == "conversation.item.input_audio_transcription.completed":
                transcript = data.get("transcript", "") or data.get("stash", "")
                if transcript:
                    print(f"✅ 完整转录: '{transcript}'")
                    result_queue.put(("completed", transcript))
            elif event_type == "conversation.item.input_audio_transcription.text":
                # 文字在 stash 字段中！
                transcript = data.get("stash", "") or data.get("transcript", "")
                if transcript:
                    transcript_parts.append(transcript)
                    print(f"📝 部分转录: '{transcript}'")
                    
        except Exception as e:
            print(f"STT parse error: {e}")
    
    def on_error(ws, error):
        print(f"STT WebSocket error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print(f"STT closed: {close_status_code} - {close_msg}")
        # 连接关闭时，如果有转录片段，返回最后一个（最完整的）
        if transcript_parts:
            final_transcript = transcript_parts[-1]  # 取最后一个
            print(f"📤 返回最终转录: '{final_transcript}'")
            result_queue.put(("final", final_transcript))
    
    def on_open(ws):
        print("STT WebSocket opened")
        
        # 会话更新事件 (带 VAD)
        event = {
            "event_id": "event_123",
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "input_audio_format": "pcm",
                "sample_rate": 16000,
                "input_audio_transcription": {
                    "language": "zh"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.2,
                    "silence_duration_ms": 800
                }
            }
        }
        ws.send(json.dumps(event))
        print("📤 已发送 session.update")
        
        # 官方示例：延迟 5 秒后再发送音频
        time.sleep(5)
        
        # 读取并发送音频
        with open(pcm_path, 'rb') as f:
            chunk_size = 3200  # 100ms at 16kHz
            chunk_count = 0
            
            while True:
                audio_data = f.read(chunk_size)
                if not audio_data:
                    print("📤 音频文件读取完毕")
                    break
                
                encoded = base64.b64encode(audio_data).decode('utf-8')
                
                eventd = {
                    "event_id": f"event_{int(time.time() * 1000)}",
                    "type": "input_audio_buffer.append",
                    "audio": encoded
                }
                ws.send(json.dumps(eventd))
                chunk_count += 1
                
                # 官方示例：模拟实时音频采集，每次发送后 sleep 0.1 秒
                time.sleep(0.1)
                
                if chunk_count % 10 == 0:
                    print(f"📤 已发送 {chunk_count} 个音频块...")
        
        print(f"✅ 共发送 {chunk_count} 个音频块")
        # 不需要手动 commit，让 VAD 自动处理
    
    # 创建 WebSocket 连接
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
    
    # 在后台运行
    def run_ws():
        ws.run_forever()
    
    thread = threading.Thread(target=run_ws, daemon=True)
    thread.start()
    
    # 等待结果 (超时 60 秒)
    try:
        result = result_queue.get(timeout=60)
        if result[0] == "completed":
            return result[1]
        elif result[0] == "final":
            return result[1]
        else:
            return result[1]
    except:
        # 超时时返回最后一个片段
        if transcript_parts:
            final_transcript = transcript_parts[-1]  # 取最后一个
            print(f"⏰ 超时，返回最后一个完整结果: '{final_transcript}'")
            return final_transcript
        print("⏰ STT 超时")
        ws.close()
        return None


def compare_results(original_text, stt_result):
    """对比原始文本和 STT 识别结果"""
    print("\n" + "=" * 60)
    print("步骤 3: 结果对比")
    print("=" * 60)
    
    print(f"📝 原始文本 (TTS输入): {original_text}")
    print(f"🔍 识别结果 (STT输出): {stt_result}")
    
    if stt_result and original_text in stt_result:
        print("\n✅ 测试通过! STT 成功识别了 TTS 生成的语音")
        return True
    elif stt_result:
        print(f"\n⚠️ 部分匹配")
        return False
    else:
        print("\n❌ 测试失败: STT 未返回有效结果")
        return False


async def main():
    print("=" * 60)
    print("TTS → STT 闭环测试 (官方示例版)")
    print("=" * 60)
    
    # 步骤 1: 测试 TTS
    pcm_path = await test_tts()
    if not pcm_path:
        print("\n❌ TTS 测试失败，终止流程")
        return
    
    # 步骤 2: 测试 STT (使用官方示例方式)
    stt_result = test_stt_official(pcm_path)
    
    # 步骤 3: 对比结果
    if stt_result:
        compare_results(TEST_TEXT, stt_result)
    else:
        print("\n❌ STT 测试失败")

if __name__ == "__main__":
    asyncio.run(main())
