#!/usr/bin/env python3
"""
STT Callback 单元测试 - 测试 STTCallback 类的回调功能
目标：测试新版 dashscope RecognitionCallback 的适配
"""

import sys
import os
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


class MockRecognitionResult:
    """模拟 RecognitionResult 对象"""
    def __init__(self, text=''):
        self.text = text
        self.output = {'text': text}


class TestSTTCallback(unittest.TestCase):
    """STTCallback 测试类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别初始化，加载模块一次"""
        cls.gateway_module = load_agent_gateway()
    
    def setUp(self):
        """测试前准备"""
        # Mock gateway
        self.mock_gateway = Mock()
        self.mock_gateway.send_stt_partial_to_clients = AsyncMock()
        self.mock_gateway.send_stt_final_to_clients = AsyncMock()
        
        # 导入 STTCallback
        self.callback = self.gateway_module.STTCallback(self.mock_gateway)
        
    def test_on_open(self):
        """测试 1: on_open 回调"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 1: on_open 回调{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 调用 on_open
        try:
            self.callback.on_open()
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} on_open 无异常")
            self.assertTrue(True)
        except Exception as e:
            print(f"{Colors.RED}❌ [FAIL]{Colors.END} on_open 异常：{e}")
            self.fail(f"on_open 抛出异常：{e}")
    
    def test_on_close(self):
        """测试 2: on_close 回调"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 2: on_close 回调{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 调用 on_close (新版无参数)
        try:
            self.callback.on_close()
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} on_close 无异常")
            self.assertTrue(True)
        except Exception as e:
            print(f"{Colors.RED}❌ [FAIL]{Colors.END} on_close 异常：{e}")
            self.fail(f"on_close 抛出异常：{e}")
    
    def test_on_complete(self):
        """测试 3: on_complete 回调"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 3: on_complete 回调{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 调用 on_complete
        try:
            self.callback.on_complete()
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} on_complete 无异常")
            self.assertTrue(True)
        except Exception as e:
            print(f"{Colors.RED}❌ [FAIL]{Colors.END} on_complete 异常：{e}")
            self.fail(f"on_complete 抛出异常：{e}")
    
    def test_on_error(self):
        """测试 4: on_error 回调"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 4: on_error 回调{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 创建模拟结果
        mock_result = MockRecognitionResult(text="Error occurred")
        
        try:
            self.callback.on_error(mock_result)
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} on_error 无异常")
            self.assertTrue(True)
        except Exception as e:
            print(f"{Colors.RED}❌ [FAIL]{Colors.END} on_error 异常：{e}")
            self.fail(f"on_error 抛出异常：{e}")
    
    def test_on_event_with_text(self):
        """测试 5: on_event 有文本"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 5: on_event 有文本{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 创建模拟结果
        mock_result = MockRecognitionResult(text="测试文本")
        
        # 设置 partial_callback
        mock_callback = Mock()
        self.callback.partial_callback = mock_callback
        
        # 调用 on_event
        try:
            self.callback.on_event(mock_result)
            
            # 验证 result_text 被更新
            self.assertEqual(self.callback.result_text, "测试文本")
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} result_text 更新正确")
            
            # 验证 partial_callback 被调用
            mock_callback.assert_called_once()
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} partial_callback 被调用")
            
        except Exception as e:
            print(f"{Colors.RED}❌ [FAIL]{Colors.END} on_event 异常：{e}")
            self.fail(f"on_event 抛出异常：{e}")
    
    def test_on_event_empty_text(self):
        """测试 6: on_event 空文本"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 6: on_event 空文本{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 创建空结果
        mock_result = MockRecognitionResult(text='')
        
        # 设置 partial_callback
        mock_callback = Mock()
        self.callback.partial_callback = mock_callback
        
        # 调用 on_event
        try:
            self.callback.on_event(mock_result)
            
            # 验证 partial_callback 未被调用（空文本）
            mock_callback.assert_not_called()
            print(f"{Colors.GREEN}✅ [PASS]{Colors.END} 空文本不触发回调")
            
        except Exception as e:
            print(f"{Colors.RED}❌ [FAIL]{Colors.END} on_event 异常：{e}")
            self.fail(f"on_event 抛出异常：{e}")
    
    def test_partial_callback_is_final(self):
        """测试 7: partial_callback is_final 参数"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 7: partial_callback is_final 参数{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 设置 partial_callback
        received_args = []
        def capture_callback(text, is_final):
            received_args.append((text, is_final))
        
        self.callback.partial_callback = capture_callback
        
        # 调用 on_event
        mock_result = MockRecognitionResult(text="测试")
        self.callback.on_event(mock_result)
        
        # 验证 is_final=False
        self.assertEqual(len(received_args), 1)
        self.assertEqual(received_args[0][1], False)
        print(f"{Colors.GREEN}✅ [PASS]{Colors.END} is_final=False 正确")
    
    def test_callback_initialization(self):
        """测试 8: Callback 初始化"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 8: Callback 初始化{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        from agent_gateway import STTCallback
        
        callback = STTCallback(self.mock_gateway)
        
        self.assertEqual(callback.gateway, self.mock_gateway)
        self.assertEqual(callback.result_text, "")
        self.assertEqual(callback.final_text, "")
        self.assertIsNone(callback.partial_callback)
        
        print(f"{Colors.GREEN}✅ [PASS]{Colors.END} 初始化状态正确")
    
    def test_final_text_update(self):
        """测试 9: final_text 更新"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}🧪 测试 9: final_text 更新{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        # 模拟多次调用
        mock_result1 = MockRecognitionResult(text="部分文本")
        mock_result2 = MockRecognitionResult(text="最终文本")
        
        self.callback.on_event(mock_result1)
        self.assertEqual(self.callback.result_text, "部分文本")
        
        self.callback.on_event(mock_result2)
        self.assertEqual(self.callback.result_text, "最终文本")
        
        print(f"{Colors.GREEN}✅ [PASS]{Colors.END} 文本更新正确")


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 STT Callback 单元测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSTTCallback)
    
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
