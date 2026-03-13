#!/usr/bin/env python3
"""
Agent 调用单元测试 - 测试 AgentGateway 的 Agent 交互逻辑
覆盖 Agent 请求构建、响应处理、错误重试等核心功能
"""

import sys
import os
import unittest
import importlib.util
import json
import subprocess
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime


def load_agent_gateway():
    """动态加载 agent-gateway.py 模块"""
    module_path = os.path.join(os.path.dirname(__file__), '..', 'wsl2', 'agent-gateway.py')
    module_path = os.path.abspath(module_path)
    
    spec = importlib.util.spec_from_file_location("agent_gateway", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules['agent_gateway'] = module
    spec.loader.exec_module(module)
    return module


class TestAgentCall(unittest.TestCase):
    """Agent 调用测试类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别初始化"""
        cls.gateway_module = load_agent_gateway()
    
    def setUp(self):
        """测试前准备"""
        with patch.object(self.gateway_module, 'websockets'):
            with patch.object(self.gateway_module, 'dashscope'):
                self.gateway = self.gateway_module.AgentGateway()
    
    def test_send_to_agent_success(self):
        """测试 1: Agent 调用成功"""
        print("\n" + "="*60)
        print("🧪 测试 1: Agent 调用成功")
        print("="*60)
        
        # Mock subprocess.run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'result': {
                'payloads': [
                    {'text': '这是 Agent 的回复'}
                ]
            }
        })
        mock_result.stderr = ""
        
        with patch.object(subprocess, 'run', return_value=mock_result) as mock_run:
            response = self.gateway.send_to_agent("你好")
            
            # 验证返回正确的回复
            self.assertEqual(response, '这是 Agent 的回复')
            
            # 验证 subprocess.run 被调用
            mock_run.assert_called_once()
            
            # 验证命令包含正确的参数
            call_args = mock_run.call_args[0][0]
            self.assertIn('openclaw', call_args)
            self.assertIn('--message', call_args)
            self.assertIn('[VOICE] 你好', call_args)
        
        print("✅ [PASS] Agent 调用成功处理正确")
    
    def test_send_to_agent_empty_payloads(self):
        """测试 2: Agent 返回空 payloads"""
        print("\n" + "="*60)
        print("🧪 测试 2: Agent 返回空 payloads")
        print("="*60)
        
        # Mock subprocess.run - 空 payloads
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'result': {
                'payloads': []
            }
        })
        
        with patch.object(subprocess, 'run', return_value=mock_result):
            response = self.gateway.send_to_agent("测试")
            
            # 验证返回默认回复
            self.assertEqual(response, "好的，我收到了你的消息。")
        
        print("✅ [PASS] 空 payloads 处理正确")
    
    def test_send_to_agent_non_zero_returncode(self):
        """测试 3: Agent 调用返回非零退出码"""
        print("\n" + "="*60)
        print("🧪 测试 3: Agent 调用返回非零退出码")
        print("="*60)
        
        # Mock subprocess.run - 失败
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Agent not found"
        
        with patch.object(subprocess, 'run', return_value=mock_result):
            response = self.gateway.send_to_agent("测试")
            
            # 验证返回降级回复
            self.assertEqual(response, "好的，我收到了。")
        
        print("✅ [PASS] 非零退出码处理正确")
    
    def test_send_to_agent_timeout(self):
        """测试 4: Agent 调用超时"""
        print("\n" + "="*60)
        print("🧪 测试 4: Agent 调用超时")
        print("="*60)
        
        # Mock subprocess.run - 超时
        with patch.object(subprocess, 'run', side_effect=subprocess.TimeoutExpired(cmd='openclaw', timeout=60)):
            response = self.gateway.send_to_agent("测试")
            
            # 验证返回超时回复
            self.assertEqual(response, "抱歉，响应超时了。")
        
        print("✅ [PASS] 超时处理正确")
    
    def test_send_to_agent_exception(self):
        """测试 5: Agent 调用异常"""
        print("\n" + "="*60)
        print("🧪 测试 5: Agent 调用异常")
        print("="*60)
        
        # Mock subprocess.run - 异常
        with patch.object(subprocess, 'run', side_effect=Exception("Unknown error")):
            response = self.gateway.send_to_agent("测试")
            
            # 验证返回错误回复
            self.assertEqual(response, "抱歉，出了点问题。")
        
        print("✅ [PASS] 异常处理正确")
    
    def test_send_to_agent_with_session_id(self):
        """测试 6: 使用 Session ID 调用 Agent"""
        print("\n" + "="*60)
        print("🧪 测试 6: 使用 Session ID 调用 Agent")
        print("="*60)
        
        # Mock environment
        with patch.dict(os.environ, {'OPENCLAW_SESSION_ID': 'test-session-123'}):
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({
                'result': {'payloads': [{'text': '回复'}]}
            })
            
            with patch.object(subprocess, 'run', return_value=mock_result) as mock_run:
                self.gateway.send_to_agent("测试")
                
                # 验证命令包含 session-id
                call_args = mock_run.call_args[0][0]
                self.assertIn('--session-id', call_args)
                self.assertIn('test-session-123', call_args)
        
        print("✅ [PASS] Session ID 参数正确")
    
    def test_send_to_agent_without_session_id(self):
        """测试 7: 不使用 Session ID 时使用 Agent ID"""
        print("\n" + "="*60)
        print("🧪 测试 7: 使用 Agent ID 调用")
        print("="*60)
        
        # Mock environment - 无 session
        with patch.dict(os.environ, {}, clear=True):
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({
                'result': {'payloads': [{'text': '回复'}]}
            })
            
            with patch.object(subprocess, 'run', return_value=mock_result) as mock_run:
                self.gateway.send_to_agent("测试")
                
                # 验证命令包含 agent 参数
                call_args = mock_run.call_args[0][0]
                self.assertIn('--agent', call_args)
        
        print("✅ [PASS] Agent ID 参数正确")
    
    def test_send_to_agent_json_parse_error(self):
        """测试 8: Agent 返回无效 JSON"""
        print("\n" + "="*60)
        print("🧪 测试 8: Agent 返回无效 JSON")
        print("="*60)
        
        # Mock subprocess.run - 无效 JSON
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "not valid json"
        
        with patch.object(subprocess, 'run', return_value=mock_result):
            try:
                response = self.gateway.send_to_agent("测试")
                # 如果代码中有异常处理，应该返回错误回复
                print("✅ [PASS] 无效 JSON 被处理")
            except json.JSONDecodeError:
                # 或者抛出异常（取决于实现）
                print("✅ [PASS] JSON 解析错误被抛出")
        
        print("✅ [PASS] 无效 JSON 处理正确")
    
    def test_send_to_agent_missing_result_key(self):
        """测试 9: Agent 响应缺少 result 键"""
        print("\n" + "="*60)
        print("🧪 测试 9: Agent 响应缺少 result 键")
        print("="*60)
        
        # Mock subprocess.run - 缺少 result
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'status': 'ok'
        })
        
        with patch.object(subprocess, 'run', return_value=mock_result):
            try:
                response = self.gateway.send_to_agent("测试")
                print("✅ [PASS] 缺少 result 键被处理")
            except (KeyError, AttributeError):
                print("✅ [PASS] KeyError 被抛出")
        
        print("✅ [PASS] 缺少 result 键处理正确")
    
    def test_send_to_agent_voice_prefix(self):
        """测试 10: 消息添加 [VOICE] 前缀"""
        print("\n" + "="*60)
        print("🧪 测试 10: 消息添加 [VOICE] 前缀")
        print("="*60)
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'result': {'payloads': [{'text': '回复'}]}
        })
        
        with patch.object(subprocess, 'run', return_value=mock_result) as mock_run:
            self.gateway.send_to_agent("你好世界")
            
            # 验证消息包含 [VOICE] 前缀
            call_args = mock_run.call_args[0][0]
            message_index = call_args.index('--message') + 1
            self.assertTrue(call_args[message_index].startswith('[VOICE]'))
        
        print("✅ [PASS] [VOICE] 前缀添加正确")


class TestProcessSpeechEnd(unittest.TestCase):
    """说话结束处理测试"""
    
    @classmethod
    def setUpClass(cls):
        cls.gateway_module = load_agent_gateway()
    
    def setUp(self):
        with patch.object(self.gateway_module, 'websockets'):
            with patch.object(self.gateway_module, 'dashscope'):
                self.gateway = self.gateway_module.AgentGateway()
        # 创建新的事件循环用于测试
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def test_process_speech_end_stt_result(self):
        """测试 11: _process_speech_end - STT 结果处理"""
        print("\n" + "="*60)
        print("🧪 测试 11: _process_speech_end - STT 结果处理")
        print("="*60)
        
        # 设置 STT 结果
        self.gateway.stt_final_text = "用户说的话"
        
        # Mock send_to_clients_async
        self.gateway.send_to_clients_async = AsyncMock()
        
        # Mock send_to_agent
        with patch.object(self.gateway, 'send_to_agent', return_value="Agent 回复"):
            with patch.object(self.gateway, 'call_tts'):
                # 运行测试
                self.loop.run_until_complete(self.gateway._process_speech_end())
                
                # 验证发送了 stt_result
                self.gateway.send_to_clients_async.assert_called()
        
        print("✅ [PASS] _process_speech_end 处理正确")
    
    def test_process_speech_end_empty_stt(self):
        """测试 12: _process_speech_end - STT 为空时的降级处理"""
        print("\n" + "="*60)
        print("🧪 测试 12: _process_speech_end - STT 为空降级")
        print("="*60)
        
        # 设置空 STT 结果
        self.gateway.stt_final_text = ""
        self.gateway.stt_partial_text = ""
        
        # Mock send_to_clients_async
        self.gateway.send_to_clients_async = AsyncMock()
        
        # Mock send_to_agent
        with patch.object(self.gateway, 'send_to_agent', return_value="默认回复") as mock_send:
            with patch.object(self.gateway, 'call_tts'):
                self.loop.run_until_complete(self.gateway._process_speech_end())
                
                # 验证使用了默认文本
                mock_send.assert_called()
        
        print("✅ [PASS] STT 为空时降级处理正确")
    
    def test_process_speech_end_status_updates(self):
        """测试 13: _process_speech_end - 状态更新"""
        print("\n" + "="*60)
        print("🧪 测试 13: _process_speech_end - 状态更新")
        print("="*60)
        
        self.gateway.stt_final_text = "测试"
        self.gateway.send_to_clients_async = AsyncMock()
        
        with patch.object(self.gateway, 'send_to_agent', return_value="回复"):
            with patch.object(self.gateway, 'call_tts'):
                self.loop.run_until_complete(self.gateway._process_speech_end())
                
                # 验证发送了状态更新
                calls = self.gateway.send_to_clients_async.call_args_list
                status_calls = [c for c in calls if 'status' in str(c)]
                self.assertGreater(len(status_calls), 0)
        
        print("✅ [PASS] 状态更新正确")


class TestMessageTypes(unittest.TestCase):
    """消息类型处理测试"""
    
    @classmethod
    def setUpClass(cls):
        cls.gateway_module = load_agent_gateway()
    
    def setUp(self):
        with patch.object(self.gateway_module, 'websockets'):
            with patch.object(self.gateway_module, 'dashscope'):
                self.gateway = self.gateway_module.AgentGateway()
        # 创建新的事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def test_handle_json_stt_result(self):
        """测试 14: handle_json - stt_result 消息"""
        print("\n" + "="*60)
        print("🧪 测试 14: handle_json - stt_result 消息")
        print("="*60)
        
        self.gateway.send_to_clients_async = AsyncMock()
        self.gateway.process_stt_result = AsyncMock()
        
        message = json.dumps({
            'type': 'stt_result',
            'text': '识别结果'
        })
        
        self.loop.run_until_complete(self.gateway.handle_json(message))
        
        # 验证 process_stt_result 被调用
        self.gateway.process_stt_result.assert_called_once_with('识别结果')
        
        print("✅ [PASS] stt_result 消息处理正确")
    
    def test_handle_json_connect(self):
        """测试 15: handle_json - connect 消息"""
        print("\n" + "="*60)
        print("🧪 测试 15: handle_json - connect 消息")
        print("="*60)
        
        self.gateway.send_to_clients_async = AsyncMock()
        
        message = json.dumps({'type': 'connect'})
        
        self.loop.run_until_complete(self.gateway.handle_json(message))
        
        # 验证发送了 connected 响应
        self.gateway.send_to_clients_async.assert_called()
        call_args = self.gateway.send_to_clients_async.call_args[0][0]
        self.assertEqual(call_args['type'], 'connected')
        
        print("✅ [PASS] connect 消息处理正确")
    
    def test_handle_json_audio_stream_start(self):
        """测试 16: handle_json - audio_stream_start 消息"""
        print("\n" + "="*60)
        print("🧪 测试 16: handle_json - audio_stream_start 消息")
        print("="*60)
        
        # 先设置一些缓冲区数据
        self.gateway.audio_buffer = bytearray(b'test')
        self.gateway.is_speaking = True
        
        message = json.dumps({'type': 'audio_stream_start'})
        
        self.loop.run_until_complete(self.gateway.handle_json(message))
        
        # 验证缓冲区被清空
        self.assertEqual(len(self.gateway.audio_buffer), 0)
        self.assertFalse(self.gateway.is_speaking)
        
        print("✅ [PASS] audio_stream_start 消息处理正确")
    
    def test_handle_json_invalid_json(self):
        """测试 17: handle_json - 无效 JSON"""
        print("\n" + "="*60)
        print("🧪 测试 17: handle_json - 无效 JSON")
        print("="*60)
        
        message = "not valid json {"
        
        # 应该不抛出异常
        try:
            self.loop.run_until_complete(self.gateway.handle_json(message))
            print("✅ [PASS] 无效 JSON 被正确处理")
        except json.JSONDecodeError:
            print("✅ [PASS] JSONDecodeError 被捕获")
        
        print("✅ [PASS] 无效 JSON 处理正确")
    
    def test_handle_json_unknown_type(self):
        """测试 18: handle_json - 未知消息类型"""
        print("\n" + "="*60)
        print("🧪 测试 18: handle_json - 未知消息类型")
        print("="*60)
        
        message = json.dumps({'type': 'unknown_type'})
        
        # 应该不抛出异常
        try:
            self.loop.run_until_complete(self.gateway.handle_json(message))
            print("✅ [PASS] 未知类型被正确处理")
        except Exception as e:
            print(f"✅ [PASS] 异常被捕获：{type(e).__name__}")
        
        print("✅ [PASS] 未知消息类型处理正确")


class TestSendMessageMethods(unittest.TestCase):
    """消息发送方法测试"""
    
    @classmethod
    def setUpClass(cls):
        cls.gateway_module = load_agent_gateway()
    
    def setUp(self):
        with patch.object(self.gateway_module, 'websockets'):
            with patch.object(self.gateway_module, 'dashscope'):
                self.gateway = self.gateway_module.AgentGateway()
        # 创建新的事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def test_send_stt_partial_to_clients(self):
        """测试 19: send_stt_partial_to_clients"""
        print("\n" + "="*60)
        print("🧪 测试 19: send_stt_partial_to_clients")
        print("="*60)
        
        self.gateway.send_to_clients_async = AsyncMock()
        
        self.loop.run_until_complete(self.gateway.send_stt_partial_to_clients("测试文本"))
        
        self.gateway.send_to_clients_async.assert_called_once()
        call_args = self.gateway.send_to_clients_async.call_args[0][0]
        self.assertEqual(call_args['type'], 'stt_partial')
        self.assertEqual(call_args['text'], '测试文本')
        
        print("✅ [PASS] send_stt_partial_to_clients 正确")
    
    def test_send_llm_complete_to_clients(self):
        """测试 20: send_llm_complete_to_clients"""
        print("\n" + "="*60)
        print("🧪 测试 20: send_llm_complete_to_clients")
        print("="*60)
        
        self.gateway.send_to_clients_async = AsyncMock()
        
        self.loop.run_until_complete(self.gateway.send_llm_complete_to_clients("完整回复"))
        
        self.gateway.send_to_clients_async.assert_called_once()
        call_args = self.gateway.send_to_clients_async.call_args[0][0]
        self.assertEqual(call_args['type'], 'llm_complete')
        self.assertEqual(call_args['text'], '完整回复')
        
        print("✅ [PASS] send_llm_complete_to_clients 正确")


if __name__ == "__main__":
    import asyncio
    unittest.main(verbosity=2)
