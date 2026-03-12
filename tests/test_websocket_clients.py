#!/usr/bin/env python3
"""
WebSocket 客户端管理单元测试 - 测试网关的客户端连接管理功能
目标：测试客户端连接、断开、消息处理等
"""

import sys
import os
import asyncio
import unittest
import importlib.util
from unittest.mock import Mock, MagicMock, patch, AsyncMock

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


class TestWebSocketClients(unittest.TestCase):
    """WebSocket 客户端管理测试类"""
    
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
    
    def test_client_connect(self):
        """测试 1: 客户端连接"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 1: 客户端连接{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 初始无客户端
        self.assertEqual(len(self.gateway.clients), 0)
        
        # 添加客户端
        self.gateway.clients.add(self.mock_websocket)
        
        self.assertEqual(len(self.gateway.clients), 1)
        self.assertIn(self.mock_websocket, self.gateway.clients)
        
        print(f"{Colors.GREEN}✅ [PASS]{Colors.END} 客户端连接成功")
    
    def test_client_disconnect(self):
        """测试 2: 客户端断开"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 2: 客户端断开{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 添加客户端
        self.gateway.clients.add(self.mock_websocket)
        self.assertEqual(len(self.gateway.clients), 1)
        
        # 移除客户端
        self.gateway.clients.discard(self.mock_websocket)
        
        self.assertEqual(len(self.gateway.clients), 0)
        self.assertNotIn(self.mock_websocket, self.gateway.clients)
        
        print(f"{Colors.GREEN}✅ [PASS]{Colors.END} 客户端断开成功")
    
    def test_multiple_clients(self):
        """测试 3: 多客户端管理"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 3: 多客户端管理{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 添加多个客户端
        clients = [Mock() for _ in range(5)]
        for client in clients:
            self.gateway.clients.add(client)
        
        self.assertEqual(len(self.gateway.clients), 5)
        
        # 移除一个
        self.gateway.clients.discard(clients[0])
        self.assertEqual(len(self.gateway.clients), 4)
        
        print(f"{Colors.GREEN}✅ [PASS]{Colors.END} 多客户端管理正确")
    
    def test_handle_json_connect_message(self):
        """测试 4: 处理 connect 消息"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 4: 处理 connect 消息{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            # 添加客户端
            self.gateway.clients.add(self.mock_websocket)
            
            # 模拟 connect 消息
            message = '{"type": "connect"}'
            await self.gateway.handle_json(message)
            
            # 验证发送了 connected 响应
            self.mock_websocket.send.assert_called()
            call_args = self.mock_websocket.send.call_args[0][0]
            
            import json
            data = json.loads(call_args)
            self.assertEqual(data['type'], 'connected')
            self.assertIn('timestamp', data)
            
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} connect 消息处理正确")
        
        asyncio.run(run_test())
    
    def test_handle_json_stt_result(self):
        """测试 5: 处理 stt_result 消息"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 5: 处理 stt_result 消息{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            # Mock process_stt_result
            self.gateway.process_stt_result = AsyncMock()
            
            # 模拟 stt_result 消息
            message = '{"type": "stt_result", "text": "测试文本"}'
            await self.gateway.handle_json(message)
            
            # 验证调用了 process_stt_result
            self.gateway.process_stt_result.assert_called_once_with("测试文本")
            
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} stt_result 消息处理正确")
        
        asyncio.run(run_test())
    
    def test_handle_json_invalid(self):
        """测试 6: 处理无效 JSON"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 6: 处理无效 JSON{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            # 无效 JSON 不应抛出异常
            try:
                await self.gateway.handle_json('invalid json{')
                print(f"{Colors.GREEN}✅ [PASS]{Colors.END} 无效 JSON 处理无异常")
            except Exception as e:
                self.fail(f"处理无效 JSON 时抛出异常：{e}")
        
        asyncio.run(run_test())
    
    def test_handle_audio_stream_start(self):
        """测试 7: 处理 audio_stream_start 消息"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 7: 处理 audio_stream_start 消息{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            # 模拟 audio_stream_start 消息
            message = '{"type": "audio_stream_start"}'
            await self.gateway.handle_json(message)
            
            # 验证音频缓冲区被清空
            self.assertEqual(len(self.gateway.audio_buffer), 0)
            self.assertEqual(self.gateway.is_speaking, False)
            
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} audio_stream_start 处理正确")
        
        asyncio.run(run_test())
    
    def test_handle_audio_stream_stop(self):
        """测试 8: 处理 audio_stream_stop 消息"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 8: 处理 audio_stream_stop 消息{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        async def run_test():
            # Mock _process_speech_end
            self.gateway._process_speech_end = AsyncMock()
            
            # 先添加一些音频数据
            self.gateway.audio_buffer.extend(b'\x00\x01\x02\x03')
            
            # 模拟 audio_stream_stop 消息
            message = '{"type": "audio_stream_stop"}'
            await self.gateway.handle_json(message)
            
            # 验证调用了 _process_speech_end
            self.gateway._process_speech_end.assert_called()
            
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} audio_stream_stop 处理正确")
        
        asyncio.run(run_test())
    
    def test_client_set_operations(self):
        """测试 9: 客户端集合操作"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 9: 客户端集合操作{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 测试集合操作
        client1 = Mock()
        client2 = Mock()
        
        self.gateway.clients.add(client1)
        self.gateway.clients.add(client2)
        self.gateway.clients.add(client1)  # 重复添加
        
        self.assertEqual(len(self.gateway.clients), 2)
        
        # 测试 list 转换（用于迭代）
        client_list = list(self.gateway.clients)
        self.assertEqual(len(client_list), 2)
        
        print(f"{Colors.GREEN}✅ [PASS]{Colors.END} 集合操作正确")


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 WebSocket 客户端管理单元测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWebSocketClients)
    
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
