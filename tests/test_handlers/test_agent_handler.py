"""Agent Handler 业务逻辑测试"""

import pytest
from unittest.mock import Mock

from wsl2.handlers.agent_handler import AgentHandler


class TestAgentHandlerInitialization:
    """测试 Agent Handler 初始化"""
    
    def test_init_without_client(self):
        """测试不带客户端初始化"""
        handler = AgentHandler()
        
        assert handler.agent_client is None
    
    def test_init_with_client(self):
        """测试带客户端初始化"""
        mock_client = Mock()
        handler = AgentHandler(agent_client=mock_client)
        
        assert handler.agent_client == mock_client


class TestPreprocessMessage:
    """测试消息预处理"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = AgentHandler()
    
    def test_preprocess_normal_message(self):
        """测试预处理正常消息"""
        result = self.handler.preprocess_message("你好")
        assert result == "你好"
    
    def test_preprocess_message_with_whitespace(self):
        """测试预处理带空格的消息"""
        result = self.handler.preprocess_message("  你好  ")
        assert result == "你好"
    
    def test_preprocess_empty_string(self):
        """测试预处理空字符串"""
        result = self.handler.preprocess_message("")
        assert result is None
    
    def test_preprocess_none(self):
        """测试预处理 None"""
        result = self.handler.preprocess_message(None)
        assert result is None
    
    def test_preprocess_single_char(self):
        """测试预处理单字符（满足最小长度）"""
        result = self.handler.preprocess_message("你")
        assert result == "你"
    
    def test_preprocess_whitespace_only(self):
        """测试预处理纯空格消息"""
        result = self.handler.preprocess_message("   ")
        assert result is None


class TestProcessResponse:
    """测试 Agent 响应处理"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = AgentHandler()
    
    def test_process_normal_response(self):
        """测试处理正常响应"""
        result = self.handler.process_response("你好，我是助手")
        assert result == "你好，我是助手"
    
    def test_process_response_with_whitespace(self):
        """测试处理带空格的响应"""
        result = self.handler.process_response("  你好  ")
        assert result == "你好"
    
    def test_process_empty_response(self):
        """测试处理空响应"""
        result = self.handler.process_response("")
        assert result == ""
    
    def test_process_none_response(self):
        """测试处理 None 响应"""
        result = self.handler.process_response(None)
        assert result == ""
    
    def test_process_response_with_newlines(self):
        """测试处理带换行符的响应"""
        result = self.handler.process_response("第一行\n第二行")
        assert result == "第一行\n第二行"


class TestProcessStreamingChunk:
    """测试流式响应块处理"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = AgentHandler()
    
    def test_process_normal_chunk(self):
        """测试处理正常响应块"""
        result = self.handler.process_streaming_chunk("你好")
        assert result == "你好"
    
    def test_process_chunk_with_whitespace(self):
        """测试处理带空格的响应块"""
        result = self.handler.process_streaming_chunk("  你好  ")
        assert result == "你好"
    
    def test_process_empty_chunk(self):
        """测试处理空响应块"""
        result = self.handler.process_streaming_chunk("")
        assert result is None
    
    def test_process_none_chunk(self):
        """测试处理 None 响应块"""
        result = self.handler.process_streaming_chunk(None)
        assert result is None
    
    def test_process_whitespace_only_chunk(self):
        """测试处理纯空格响应块"""
        result = self.handler.process_streaming_chunk("   ")
        assert result is None


class TestValidateMessage:
    """测试消息验证"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = AgentHandler()
    
    def test_validate_valid_message(self):
        """测试验证有效消息"""
        assert self.handler.validate_message("你好") is True
    
    def test_validate_single_char(self):
        """测试验证单字符消息"""
        assert self.handler.validate_message("你") is True
    
    def test_validate_empty_string(self):
        """测试验证空字符串"""
        assert self.handler.validate_message("") is False
    
    def test_validate_none(self):
        """测试验证 None"""
        assert self.handler.validate_message(None) is False
    
    def test_validate_whitespace_only(self):
        """测试验证纯空格消息"""
        assert self.handler.validate_message("   ") is False
    
    def test_validate_message_with_spaces(self):
        """测试验证带空格的消息"""
        assert self.handler.validate_message("  你好  ") is True


class TestEdgeCases:
    """测试边界情况"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = AgentHandler()
    
    def test_preprocess_unicode_message(self):
        """测试预处理 Unicode 消息"""
        result = self.handler.preprocess_message("🎉🚀")
        assert result == "🎉🚀"
    
    def test_preprocess_mixed_languages(self):
        """测试预处理混合语言消息"""
        result = self.handler.preprocess_message("Hello 世界")
        assert result == "Hello 世界"
    
    def test_process_response_with_special_chars(self):
        """测试处理带特殊字符的响应"""
        result = self.handler.process_response("你好@#￥%……")
        assert result == "你好@#￥%……"
    
    def test_validate_long_message(self):
        """测试验证长消息"""
        long_message = "a" * 1000
        assert self.handler.validate_message(long_message) is True
    
    def test_process_streaming_chunk_preserves_content(self):
        """测试流式响应块处理保留内容"""
        chunk = "这是第一个块"
        result = self.handler.process_streaming_chunk(chunk)
        assert result == chunk
