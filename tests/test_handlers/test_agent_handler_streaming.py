"""Agent Handler 流式响应测试"""

import pytest
from unittest.mock import Mock

from wsl2.handlers.agent_handler import AgentHandler


class TestAgentHandlerStreamingInitialization:
    """测试 Agent Handler 流式初始化"""
    
    def test_init_streaming_buffer_empty(self):
        """测试初始化时流式缓冲区为空"""
        handler = AgentHandler()
        assert handler.streaming_buffer == ""
    
    def test_init_with_client_streaming_buffer_empty(self):
        """测试带客户端初始化时流式缓冲区为空"""
        mock_client = Mock()
        handler = AgentHandler(agent_client=mock_client)
        assert handler.streaming_buffer == ""


class TestProcessLlmToken:
    """测试 LLM token 处理"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = AgentHandler()
    
    def test_process_single_char_token(self):
        """测试处理单字符 token"""
        result = self.handler.process_llm_token("你")
        assert result == "你"
    
    def test_process_multi_char_token(self):
        """测试处理多字符 token"""
        result = self.handler.process_llm_token("你好")
        assert result == "你好"
    
    def test_process_empty_token(self):
        """测试处理空 token"""
        result = self.handler.process_llm_token("")
        assert result is None
    
    def test_process_none_token(self):
        """测试处理 None token"""
        result = self.handler.process_llm_token(None)
        assert result is None
    
    def test_process_whitespace_token(self):
        """测试处理空白 token（保留格式）"""
        result = self.handler.process_llm_token(" ")
        assert result == " "
    
    def test_process_newline_token(self):
        """测试处理换行 token"""
        result = self.handler.process_llm_token("\n")
        assert result == "\n"
    
    def test_process_punctuation_token(self):
        """测试处理标点符号 token"""
        result = self.handler.process_llm_token("，")
        assert result == "，"
    
    def test_process_mixed_token(self):
        """测试处理混合 token"""
        result = self.handler.process_llm_token("你好，")
        assert result == "你好，"


class TestStreamingBuffer:
    """测试流式缓冲区管理"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = AgentHandler()
    
    def test_reset_streaming_buffer(self):
        """测试重置流式缓冲区"""
        self.handler.streaming_buffer = "测试内容"
        self.handler.reset_streaming_buffer()
        assert self.handler.streaming_buffer == ""
    
    def test_append_to_streaming_buffer_single_token(self):
        """测试追加单个 token 到缓冲区"""
        result = self.handler.append_to_streaming_buffer("你")
        assert result == "你"
        assert self.handler.streaming_buffer == "你"
    
    def test_append_to_streaming_buffer_multiple_tokens(self):
        """测试追加多个 token 到缓冲区"""
        self.handler.append_to_streaming_buffer("你")
        self.handler.append_to_streaming_buffer("好")
        self.handler.append_to_streaming_buffer("，")
        self.handler.append_to_streaming_buffer("世")
        self.handler.append_to_streaming_buffer("界")
        
        assert self.handler.streaming_buffer == "你好，世界"
    
    def test_append_to_streaming_buffer_returns_buffer(self):
        """测试追加方法返回当前缓冲区内容"""
        self.handler.append_to_streaming_buffer("第")
        result1 = self.handler.append_to_streaming_buffer("一")
        result2 = self.handler.append_to_streaming_buffer("次")
        
        assert result1 == "第一"
        assert result2 == "第一次"
    
    def test_append_empty_token(self):
        """测试追加空 token"""
        self.handler.streaming_buffer = "已有内容"
        result = self.handler.append_to_streaming_buffer("")
        assert result == "已有内容"
        assert self.handler.streaming_buffer == "已有内容"
    
    def test_get_streaming_buffer(self):
        """测试获取流式缓冲区"""
        self.handler.streaming_buffer = "测试缓冲区"
        result = self.handler.get_streaming_buffer()
        assert result == "测试缓冲区"
    
    def test_get_empty_streaming_buffer(self):
        """测试获取空流式缓冲区"""
        handler = AgentHandler()
        result = handler.get_streaming_buffer()
        assert result == ""
    
    def test_reset_then_append(self):
        """测试重置后追加"""
        self.handler.append_to_streaming_buffer("旧内容")
        self.handler.reset_streaming_buffer()
        result = self.handler.append_to_streaming_buffer("新内容")
        
        assert result == "新内容"
        assert self.handler.streaming_buffer == "新内容"


class TestStreamingWorkflow:
    """测试流式工作流程"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = AgentHandler()
    
    def test_complete_streaming_workflow(self):
        """测试完整的流式工作流程"""
        # 模拟流式 token 序列
        tokens = ["你", "好", "，", "我", "是", "助", "手"]
        
        # 逐个处理 token
        results = []
        for token in tokens:
            processed = self.handler.process_llm_token(token)
            if processed:
                self.handler.append_to_streaming_buffer(processed)
                results.append(processed)
        
        # 验证缓冲区内容
        assert self.handler.get_streaming_buffer() == "你好，我是助手"
        assert len(results) == 7
        
        # 重置缓冲区
        self.handler.reset_streaming_buffer()
        assert self.handler.get_streaming_buffer() == ""
    
    def test_streaming_with_punctuation(self):
        """测试带标点的流式处理"""
        tokens = ["今", "天", "天", "气", "真", "好", "。"]
        
        for token in tokens:
            self.handler.append_to_streaming_buffer(token)
        
        assert self.handler.get_streaming_buffer() == "今天天气真好。"
    
    def test_streaming_with_whitespace(self):
        """测试带空白的流式处理"""
        tokens = ["Hello", " ", "W", "o", "r", "l", "d"]
        
        for token in tokens:
            self.handler.append_to_streaming_buffer(token)
        
        assert self.handler.get_streaming_buffer() == "Hello World"
    
    def test_multiple_reset_cycles(self):
        """测试多次重置循环"""
        # 第一轮
        for token in ["第", "一", "轮"]:
            self.handler.append_to_streaming_buffer(token)
        assert self.handler.get_streaming_buffer() == "第一轮"
        
        self.handler.reset_streaming_buffer()
        
        # 第二轮
        for token in ["第", "二", "轮"]:
            self.handler.append_to_streaming_buffer(token)
        assert self.handler.get_streaming_buffer() == "第二轮"
        
        self.handler.reset_streaming_buffer()
        
        # 第三轮
        for token in ["第", "三", "轮"]:
            self.handler.append_to_streaming_buffer(token)
        assert self.handler.get_streaming_buffer() == "第三轮"


class TestEdgeCases:
    """测试边界情况"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = AgentHandler()
    
    def test_process_unicode_token(self):
        """测试处理 Unicode token"""
        result = self.handler.process_llm_token("🎉")
        assert result == "🎉"
    
    def test_process_emoji_token(self):
        """测试处理 emoji token"""
        result = self.handler.process_llm_token("🚀")
        assert result == "🚀"
    
    def test_append_long_token(self):
        """测试追加长 token"""
        long_token = "a" * 100
        result = self.handler.append_to_streaming_buffer(long_token)
        assert result == long_token
        assert len(result) == 100
    
    def test_streaming_buffer_no_max_length(self):
        """测试流式缓冲区无最大长度限制"""
        for i in range(1000):
            self.handler.append_to_streaming_buffer("x")
        
        assert len(self.handler.get_streaming_buffer()) == 1000
    
    def test_process_mixed_language_tokens(self):
        """测试处理混合语言 token"""
        tokens = ["你", "好", " ", "H", "e", "l", "l", "o"]
        
        for token in tokens:
            self.handler.append_to_streaming_buffer(token)
        
        assert self.handler.get_streaming_buffer() == "你好 Hello"
