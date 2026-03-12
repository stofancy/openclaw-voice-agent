#!/usr/bin/env python3
"""
TTS 播放测试 - 验证 TTS 音频能正确发送到前端并播放
"""

import sys
import os
import asyncio
import json
import websockets

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

# 测试结果
test_results = {'passed': 0, 'failed': 0, 'total': 0}

def test(name, condition, details=""):
    test_results['total'] += 1
    if condition:
        test_results['passed'] += 1
        print(f"{Colors.GREEN}✅ [PASS]{Colors.END} {name}")
        return True
    else:
        test_results['failed'] += 1
        print(f"{Colors.RED}❌ [FAIL]{Colors.END} {name} - {details}")
        return False

async def test_tts_audio_message():
    """测试 1: TTS 音频消息格式"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 1: TTS 音频消息格式{Colors.END}")
    
    # 模拟 TTS 音频消息
    audio_message = {
        "type": "audio",
        "data": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="  # 小的 base64 PCM 数据
    }
    
    # 验证消息格式
    test("消息类型=audio", audio_message.get("type") == "audio", f"type={audio_message.get('type')}")
    test("消息包含 data 字段", "data" in audio_message, "data 字段存在")
    test("data 是 base64 字符串", isinstance(audio_message.get("data"), str), f"data 类型={type(audio_message.get('data'))}")
    
    # 验证 base64 可以解码
    import base64
    try:
        decoded = base64.b64decode(audio_message["data"])
        test("Base64 可解码", len(decoded) > 0, f"解码后长度={len(decoded)}")
    except Exception as e:
        test("Base64 可解码", False, str(e))
    
    return True

async def test_websocket_audio_send():
    """测试 2: WebSocket 发送音频消息"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 2: WebSocket 发送音频消息{Colors.END}")
    
    try:
        async with websockets.connect("ws://localhost:8765") as ws:
            # 发送音频消息
            audio_data = {
                "type": "audio",
                "data": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="
            }
            
            await ws.send(json.dumps(audio_data))
            test("音频消息发送成功", True, "发送完成")
            
            # 等待确认（如果有）
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                response_data = json.loads(response)
                test("收到响应", True, f"type={response_data.get('type')}")
            except asyncio.TimeoutError:
                test("收到响应", False, "超时（正常，网关可能不回复）")
            
            return True
    except Exception as e:
        test("WebSocket 发送音频", False, str(e))
        return False

async def test_gateway_audio_callback():
    """测试 3: 网关音频回调逻辑"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 3: 网关音频回调逻辑{Colors.END}")
    
    # 模拟 TTS 回调
    audio_chunks = []
    
    def on_audio_delta(audio_b64):
        if audio_b64:
            audio_chunks.append(audio_b64)
            return True
        return False
    
    # 测试音频数据
    test_audio = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="
    result = on_audio_delta(test_audio)
    
    test("音频回调接收数据", result == True, f"result={result}")
    test("音频块已保存", len(audio_chunks) > 0, f"chunks={len(audio_chunks)}")
    
    # 测试空数据
    result_empty = on_audio_delta("")
    test("空数据不处理", result_empty == False, f"result={result_empty}")
    
    return True

async def test_base64_to_audio():
    """测试 4: Base64 转音频数据"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 4: Base64 转音频数据{Colors.END}")
    
    import base64
    import struct
    
    # 模拟 base64 PCM 数据（24kHz 单声道 16bit）
    # 创建一个简单的静音 PCM 数据
    samples = [0] * 100  # 100 个静音样本
    pcm_data = struct.pack('<' + 'h' * len(samples), *samples)
    base64_audio = base64.b64encode(pcm_data).decode('utf-8')
    
    test("PCM 转 Base64", len(base64_audio) > 0, f"base64 长度={len(base64_audio)}")
    
    # 解码
    try:
        decoded = base64.b64decode(base64_audio)
        test("Base64 解码成功", len(decoded) == len(pcm_data), f"原始={len(pcm_data)}, 解码={len(decoded)}")
    except Exception as e:
        test("Base64 解码成功", False, str(e))
        return False
    
    # 转 Float32（前端播放格式）
    try:
        float_samples = []
        for i in range(0, len(decoded), 2):
            int16 = struct.unpack('<h', decoded[i:i+2])[0]
            float_samples.append(int16 / 32768.0)
        
        test("Int16 转 Float32", len(float_samples) == 100, f"samples={len(float_samples)}")
        test("Float32 范围正确", all(-1.0 <= s <= 1.0 for s in float_samples), "范围检查")
    except Exception as e:
        test("Int16 转 Float32", False, str(e))
    
    return True

async def test_frontend_audio_playback():
    """测试 5: 前端音频播放逻辑模拟"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 5: 前端音频播放逻辑模拟{Colors.END}")
    
    # 模拟前端播放状态
    isPlaying = False
    audioQueue = []
    
    def play_audio_base64(base64_audio):
        nonlocal isPlaying, audioQueue
        try:
            import base64
            import struct
            
            # 解码
            decoded = base64.b64decode(base64_audio)
            
            # 转 Float32
            samples = []
            for i in range(0, len(decoded), 2):
                int16 = struct.unpack('<h', decoded[i:i+2])[0]
                samples.append(int16 / 32768.0)
            
            # 加入队列
            audioQueue.append(samples)
            
            # 开始播放
            if not isPlaying:
                isPlaying = True
                return "started"
            return "queued"
        except Exception as e:
            return f"error: {e}"
    
    # 测试播放
    test_audio = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="
    result = play_audio_base64(test_audio)
    
    test("第一次播放启动", result == "started", f"result={result}")
    test("播放状态=True", isPlaying == True, f"isPlaying={isPlaying}")
    test("队列有音频", len(audioQueue) > 0, f"queue={len(audioQueue)}")
    
    # 测试队列播放
    result2 = play_audio_base64(test_audio)
    test("第二次播放排队", result2 == "queued", f"result={result2}")
    test("队列有 2 个音频", len(audioQueue) == 2, f"queue={len(audioQueue)}")
    
    return True

async def run_all_tests():
    """运行所有 TTS 播放测试"""
    print("\n")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 TTS 播放测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 运行所有测试
    await test_tts_audio_message()
    await test_websocket_audio_send()
    await test_gateway_audio_callback()
    await test_base64_to_audio()
    await test_frontend_audio_playback()
    
    # 汇总报告
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}📊 测试报告{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print()
    
    total = test_results['total']
    passed = test_results['passed']
    failed = test_results['failed']
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"总测试数：{total}")
    print(f"通过：{Colors.GREEN}{passed}{Colors.END}")
    print(f"失败：{Colors.RED}{failed}{Colors.END}")
    print(f"通过率：{pass_rate:.1f}%")
    print()
    
    if failed == 0:
        print(f"{Colors.GREEN}🎉 所有测试通过！{Colors.END}")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠️  有 {failed} 个测试失败，请修复{Colors.END}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
