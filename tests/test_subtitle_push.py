#!/usr/bin/env python3
"""
字幕推送单元测试 - 测试网关的字幕推送功能
目标：测试 stt_partial, stt_final, llm_complete 等消息类型
"""

import sys
import os
import asyncio
import unittest
import importlib.util
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def load_agent_gateway():
    """动态加载 agent-gateway.py 模块（文件名有连字符）"""
    module_path = os.path.join(os.path.dirname(__file__), '..', 'wsl2', 'agent-gateway.py')
    module_path = os.path.abspath(module_path)
    
    spec = importlib.util.spec_from_file_location("agent_gateway", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules['agent_gateway'] = module
    spec.loader.exec_module(module)
    return module


class TestSubtitlePush(unittest.TestCase):
    """字幕推送测试类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别初始化，加载模块一次"""
        cls.gateway_module = load_agent_gateway()
    
    def setUp(self):
        """测试前准备"""
        # Mock websockets
        self.mock_websocket = Mock()
        self.mock_websocket.send = AsyncMock()
        self.mock_websocket.remote_address = ('127.0.0.1', 8080)
        
        # 导入 AgentGateway
        self.gateway = self.gateway_module.AgentGateway()
        self.gateway.clients = {self.mock_websocket}
    
    def test_send_stt_partial(self):
        """测试 1: 发送 STT 增量结果"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 1: 发送 STT 增量结果{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            await self.gateway.send_stt_partial_to_clients("测试文本")
            
            # 验证发送了消息
            self.mock_websocket.send.assert_called()
            call_args = self.mock_websocket.send.call_args[0][0]
            
            import json
            data = json.loads(call_args)
            
            self.assertEqual(data['type'], 'stt_partial')
            self.assertEqual(data['text'], '测试文本')
            self.assertIn('timestamp', data)
            
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} stt_partial 消息格式正确")
        
        asyncio.run(run_test())
    
    def test_send_stt_final(self):
        """测试 2: 发送 STT 最终结果"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 2: 发送 STT 最终结果{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            await self.gateway.send_stt_final_to_clients("最终文本")
            
            # 验证发送了消息
            self.mock_websocket.send.assert_called()
            call_args = self.mock_websocket.send.call_args[0][0]
            
            import json
            data = json.loads(call_args)
            
            self.assertEqual(data['type'], 'stt_final')
            self.assertEqual(data['text'], '最终文本')
            self.assertIn('timestamp', data)
            
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} stt_final 消息格式正确")
        
        asyncio.run(run_test())
    
    def test_send_llm_complete(self):
        """测试 3: 发送 LLM 完整回复"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 3: 发送 LLM 完整回复{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            await self.gateway.send_llm_complete_to_clients("AI 回复内容")
            
            # 验证发送了消息
            self.mock_websocket.send.assert_called()
            call_args = self.mock_websocket.send.call_args[0][0]
            
            import json
            data = json.loads(call_args)
            
            self.assertEqual(data['type'], 'llm_complete')
            self.assertEqual(data['text'], 'AI 回复内容')
            self.assertIn('timestamp', data)
            
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} llm_complete 消息格式正确")
        
        asyncio.run(run_test())
    
    def test_send_llm_token(self):
        """测试 4: 发送 LLM 流式 token"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 4: 发送 LLM 流式 token{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            await self.gateway.send_llm_token_to_clients("Token")
            
            # 验证发送了消息
            self.mock_websocket.send.assert_called()
            call_args = self.mock_websocket.send.call_args[0][0]
            
            import json
            data = json.loads(call_args)
            
            self.assertEqual(data['type'], 'llm_token')
            self.assertEqual(data['text'], 'Token')
            self.assertIn('timestamp', data)
            
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} llm_token 消息格式正确")
        
        asyncio.run(run_test())
    
    def test_send_subtitle_legacy(self):
        """测试 5: 发送字幕（兼容旧版本）"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 5: 发送字幕（兼容旧版本）{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            await self.gateway.send_subtitle_to_clients("字幕文本", "user", is_final=True)
            
            # 验证发送了消息
            self.mock_websocket.send.assert_called()
            call_args = self.mock_websocket.send.call_args[0][0]
            
            import json
            data = json.loads(call_args)
            
            self.assertEqual(data['type'], 'subtitle')
            self.assertEqual(data['role'], 'user')
            self.assertEqual(data['text'], '字幕文本')
            self.assertEqual(data['is_final'], True)
            self.assertIn('timestamp', data)
            
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} subtitle 消息格式正确")
        
        asyncio.run(run_test())
    
    def test_send_to_clients_empty(self):
        """测试 6: 无客户端时不发送"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 6: 无客户端时不发送{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 清空客户端
        self.gateway.clients = set()
        
        async def run_test():
            # 不应抛出异常
            await self.gateway.send_to_clients_async({'type': 'test'})
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} 无客户端时无异常")
        
        asyncio.run(run_test())
    
    def test_timestamp_format(self):
        """测试 7: 时间戳格式"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 7: 时间戳格式{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            await self.gateway.send_stt_partial_to_clients("测试")
            
            call_args = self.mock_websocket.send.call_args[0][0]
            import json
            data = json.loads(call_args)
            
            # 验证时间戳是 ISO 格式
            timestamp = data['timestamp']
            try:
                datetime.fromisoformat(timestamp)
                print(f"{Colors.GREEN}✅ [PASS]{Colors.END} 时间戳格式正确：{timestamp}")
            except ValueError:
                self.fail(f"时间戳格式错误：{timestamp}")
        
        asyncio.run(run_test())
    
    def test_multiple_clients(self):
        """测试 8: 多客户端推送"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 8: 多客户端推送{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 添加多个客户端
        mock_ws2 = Mock()
        mock_ws2.send = AsyncMock()
        self.gateway.clients = {self.mock_websocket, mock_ws2}
        
        async def run_test():
            await self.gateway.send_to_clients_async({'type': 'broadcast'})
            
            # 验证两个客户端都收到消息
            self.mock_websocket.send.assert_called()
            mock_ws2.send.assert_called()
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} 多客户端推送成功")
        
        asyncio.run(run_test())
    
    def test_message_json_serialization(self):
        """测试 9: 消息 JSON 序列化"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 9: 消息 JSON 序列化{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            await self.gateway.send_stt_partial_to_clients("测试")
            
            call_args = self.mock_websocket.send.call_args[0][0]
            
            # 验证是有效的 JSON 字符串
            import json
            try:
                data = json.loads(call_args)
                self.assertIsInstance(data, dict)
                print(f"{Colors.GREEN}✅ [PASS]{Colors.END} JSON 序列化正确")
            except json.JSONDecodeError:
                self.fail("消息不是有效的 JSON")
        
        asyncio.run(run_test())


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 字幕推送单元测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSubtitlePush)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 汇总报告
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}📊 测试报告{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print()
    
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"总测试数：{total}")
    print(f"{Colors.GREEN}通过：{passed}{Colors.END}")
    print(f"{Colors.RED}失败：{failed}{Colors.END}")
    print(f"通过率：{pass_rate:.1f}%")
    print()
    
    if failed == 0:
        print(f"{Colors.GREEN}🎉 所有测试通过！{Colors.END}")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠️  有 {failed} 个测试失败，请修复{Colors.END}")
        for test, traceback in result.failures:
            print(f"\n{Colors.RED}失败：{test}{Colors.END}")
            print(traceback)
        for test, traceback in result.errors:
            print(f"\n{Colors.RED}错误：{test}{Colors.END}")
            print(traceback)
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
