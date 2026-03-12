#!/usr/bin/env python3
"""
音量和静音功能单元测试
"""

import sys
import os
import asyncio

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

async def test_vad_threshold():
    """测试 1: VAD 阈值"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 1: VAD 阈值{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 导入网关模块
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'wsl2'))
    from agent_gateway import AgentGateway
    
    gateway = AgentGateway()
    
    # 测试 VAD 阈值
    test("VAD 阈值存在", hasattr(gateway, 'vad_threshold'), "vad_threshold 属性")
    test("VAD 阈值=0.2", gateway.vad_threshold == 0.2, f"实际值：{gateway.vad_threshold}")
    
    # 测试静音判定时间
    test("静音判定时间存在", hasattr(gateway, 'silence_duration'), "silence_duration 属性")
    test("静音判定时间=1.2s", gateway.silence_duration == 1.2, f"实际值：{gateway.silence_duration}")
    
    return True

async def test_tts_playing_flag():
    """测试 2: TTS 播放标志"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 2: TTS 播放标志{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 导入网关模块
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'wsl2'))
    from agent_gateway import AgentGateway
    
    gateway = AgentGateway()
    
    # 测试 TTS 播放标志
    test("TTS 播放标志存在", hasattr(gateway, 'is_playing_tts'), "is_playing_tts 属性")
    test("TTS 播放标志初始=False", gateway.is_playing_tts == False, f"实际值：{gateway.is_playing_tts}")
    
    # 测试 TTS 播放锁
    test("TTS 播放锁存在", hasattr(gateway, 'tts_playing_lock'), "tts_playing_lock 属性")
    
    return True

async def test_processing_flag():
    """测试 3: 处理中标志"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 3: 处理中标志{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 导入网关模块
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'wsl2'))
    from agent_gateway import AgentGateway
    
    gateway = AgentGateway()
    
    # 测试处理中标志
    test("处理中标志存在", hasattr(gateway, '_is_processing'), "_is_processing 属性")
    test("处理中标志初始=False", gateway._is_processing == False, f"实际值：{gateway._is_processing}")
    
    return True

async def test_audio_buffer():
    """测试 4: 音频缓冲区"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 4: 音频缓冲区{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 导入网关模块
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'wsl2'))
    from agent_gateway import AgentGateway
    
    gateway = AgentGateway()
    
    # 测试音频缓冲区
    test("音频缓冲区存在", hasattr(gateway, 'audio_buffer'), "audio_buffer 属性")
    test("音频缓冲区初始为空", len(gateway.audio_buffer) == 0, f"实际长度：{len(gateway.audio_buffer)}")
    
    # 测试说话状态
    test("说话状态存在", hasattr(gateway, 'is_speaking'), "is_speaking 属性")
    test("说话状态初始=False", gateway.is_speaking == False, f"实际值：{gateway.is_speaking}")
    
    return True

async def run_all_tests():
    """运行所有单元测试"""
    print("\n")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 音量和静音功能单元测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print()
    
    # 测试 1: VAD 阈值
    await test_vad_threshold()
    
    # 测试 2: TTS 播放标志
    await test_tts_playing_flag()
    
    # 测试 3: 处理中标志
    await test_processing_flag()
    
    # 测试 4: 音频缓冲区
    await test_audio_buffer()
    
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
