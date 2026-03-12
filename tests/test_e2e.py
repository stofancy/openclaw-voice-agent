#!/usr/bin/env python3
"""
端到端 (E2E) 自动化测试
模拟完整语音通话流程
"""

import sys
import os
import asyncio
import json
import websockets
import time
import struct

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

async def test_websocket_connection():
    """测试 1: WebSocket 连接"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 1: WebSocket 连接{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    try:
        async with websockets.connect("ws://localhost:8765") as ws:
            test("WebSocket 连接成功", ws.state == websockets.protocol.State.OPEN, f"状态：{ws.state}")
            
            # 发送连接测试
            await ws.send(json.dumps({"type": "connect"}))
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(response)
            
            test("连接测试响应", data.get("type") == "connected", f"收到：{data.get('type')}")
            test("网关就绪", data.get("gateway") == "ready", f"状态：{data.get('gateway')}")
            
            return True
    except Exception as e:
        test("WebSocket 连接", False, str(e))
        return False

async def test_audio_stream():
    """测试 2: 音频流传输"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 2: 音频流传输{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    try:
        async with websockets.connect("ws://localhost:8765") as ws:
            # 发送音频流开始
            await ws.send(json.dumps({"type": "audio_stream_start"}))
            test("音频流开始消息", True, "发送成功")
            
            # 模拟发送音频数据 (PCM 16bit 16kHz 1 秒)
            samples = 16000
            audio_data = struct.pack('<' + 'h' * samples, *[0] * samples)
            await ws.send(audio_data)
            test("音频数据发送", True, f"{samples} samples")
            
            # 发送音频流结束
            await ws.send(json.dumps({"type": "audio_stream_stop"}))
            test("音频流结束消息", True, "发送成功")
            
            # 等待响应
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(response)
                test("收到网关响应", True, f"type={data.get('type')}")
            except asyncio.TimeoutError:
                test("收到网关响应", False, "超时")
            
            return True
    except Exception as e:
        test("音频流传输", False, str(e))
        return False

async def test_stt_agent_tts():
    """测试 3: STT → Agent → TTS 完整流程"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 3: STT → Agent → TTS 完整流程{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    try:
        async with websockets.connect("ws://localhost:8765") as ws:
            # 发送 STT 结果（模拟识别后的文本）
            test_text = "你好，请用一句话介绍你自己"
            await ws.send(json.dumps({
                "type": "stt_result",
                "text": test_text
            }))
            test(f"发送 STT 文本", True, test_text)
            
            # 等待状态更新
            response = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(response)
            test("收到状态更新", data.get("type") == "status", f"类型：{data.get('type')}")
            
            # 等待 Agent 回复
            response = await asyncio.wait_for(ws.recv(), timeout=60.0)
            data = json.loads(response)
            test("收到 Agent 回复", data.get("type") == "reply", f"类型：{data.get('type')}")
            
            if data.get("type") == "reply":
                reply_text = data.get("text", "")
                test("回复文本非空", len(reply_text) > 0, f"{reply_text[:50]}...")
            
            # 等待 TTS 音频
            response = await asyncio.wait_for(ws.recv(), timeout=30.0)
            data = json.loads(response)
            test("收到 TTS 音频", data.get("type") == "audio", f"类型：{data.get('type')}")
            
            if data.get("type") == "audio":
                audio_data = data.get("data", "")
                test("音频数据非空", len(audio_data) > 0, f"{len(audio_data)} bytes")
            
            return True
    except asyncio.TimeoutError as e:
        test("完整流程", False, f"等待超时：{e}")
        return False
    except Exception as e:
        test("完整流程", False, str(e))
        return False

def test_gateway_process():
    """测试 0: 网关进程状态"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 0: 网关进程状态{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    try:
        import subprocess
        result = subprocess.run(["pgrep", "-f", "agent-gateway.py"], capture_output=True, text=True)
        pids = result.stdout.strip().split('\n') if result.returncode == 0 else []
        
        test("网关进程运行", len(pids) > 0, f"PID: {', '.join(pids)}")
        
        # 检查 HTTP 服务器
        result = subprocess.run(["pgrep", "-f", "http.server 8080"], capture_output=True, text=True)
        http_pids = result.stdout.strip().split('\n') if result.returncode == 0 else []
        
        test("HTTP 服务器运行", len(http_pids) > 0, f"PID: {', '.join(http_pids)}")
        
        return True
    except Exception as e:
        test("进程检查", False, str(e))
        return False

async def run_all_tests():
    """运行所有测试"""
    print("\n")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 AI Voice Agent 端到端自动化测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print()
    
    # 测试 0: 进程检查
    test_gateway_process()
    
    # 等待网关启动
    print("\n⏳ 等待 3 秒...")
    await asyncio.sleep(3)
    
    # 测试 1: WebSocket 连接
    await test_websocket_connection()
    
    # 测试 2: 音频流
    await test_audio_stream()
    
    # 测试 3: 完整流程
    await test_stt_agent_tts()
    
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
