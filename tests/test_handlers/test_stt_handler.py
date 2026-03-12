"""STT Handler 业务逻辑测试"""

import pytest
from unittest.mock import Mock

from wsl2.handlers.stt_handler import SttHandler


class TestSttHandlerInitialization:
    """测试 STT Handler 初始化"""
    
    def test_init_with_client(self):
        """测试带客户端初始化"""
        mock_client = Mock()
        handler = SttHandler(stt_client=mock_client)
        
        assert handler.stt_client == mock_client
    
    def test_init_without_client_raises(self):
        """测试不带客户端初始化会失败"""
        with pytest.raises(TypeError):
            SttHandler()


class TestProcessIncrement:
    """测试增量识别结果处理"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.mock_client = Mock()
        self.handler = SttHandler(stt_client=self.mock_client)
    
    def test_process_normal_text(self):
        """测试处理正常文本"""
        result = self.handler.process_increment("你好世界")
        assert result == "你好世界"
    
    def test_process_text_with_whitespace(self):
        """测试处理带空格的文本"""
        result = self.handler.process_increment("  你好  世界  ")
        assert result == "你好  世界"
    
    def test_process_empty_string(self):
        """测试处理空字符串"""
        result = self.handler.process_increment("")
        assert result == ""
    
    def test_process_none(self):
        """测试处理 None"""
        result = self.handler.process_increment(None)
        assert result == ""
    
    def test_process_whitespace_only(self):
        """测试处理纯空格文本"""
        result = self.handler.process_increment("   ")
        assert result == ""


class TestProcessFinal:
    """测试最终识别结果处理"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.mock_client = Mock()
        self.handler = SttHandler(stt_client=self.mock_client)
    
    def test_process_valid_text(self):
        """测试处理有效文本"""
        result = self.handler.process_final("你好世界")
        assert result == "你好世界"
    
    def test_process_text_with_whitespace(self):
        """测试处理带空格的文本"""
        result = self.handler.process_final("  你好世界  ")
        assert result == "你好世界"
    
    def test_process_empty_string(self):
        """测试处理空字符串"""
        result = self.handler.process_final("")
        assert result is None
    
    def test_process_none(self):
        """测试处理 None"""
        result = self.handler.process_final(None)
        assert result is None
    
    def test_process_single_char(self):
        """测试处理单字符（长度不足）"""
        result = self.handler.process_final("你")
        assert result is None
    
    def test_process_two_chars(self):
        """测试处理两字符（刚好满足）"""
        result = self.handler.process_final("你好")
        assert result == "你好"
    
    def test_process_whitespace_only(self):
        """测试处理纯空格文本"""
        result = self.handler.process_final("   ")
        assert result is None


class TestValidateText:
    """测试文本验证"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.mock_client = Mock()
        self.handler = SttHandler(stt_client=self.mock_client)
    
    def test_validate_valid_text(self):
        """测试验证有效文本"""
        assert self.handler.validate_text("你好世界") is True
    
    def test_validate_two_chars(self):
        """测试验证两字符文本"""
        assert self.handler.validate_text("你好") is True
    
    def test_validate_single_char(self):
        """测试验证单字符文本"""
        assert self.handler.validate_text("你") is False
    
    def test_validate_empty_string(self):
        """测试验证空字符串"""
        assert self.handler.validate_text("") is False
    
    def test_validate_none(self):
        """测试验证 None"""
        assert self.handler.validate_text(None) is False
    
    def test_validate_whitespace_only(self):
        """测试验证纯空格文本"""
        assert self.handler.validate_text("   ") is False
    
    def test_validate_text_with_leading_trailing_spaces(self):
        """测试验证带首尾空格的文本"""
        assert self.handler.validate_text("  你好  ") is True


class TestEdgeCases:
    """测试边界情况"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.mock_client = Mock()
        self.handler = SttHandler(stt_client=self.mock_client)
    
    def test_unicode_characters(self):
        """测试 Unicode 字符处理"""
        result = self.handler.process_increment("🎉🚀")
        assert result == "🎉🚀"
    
    def test_mixed_languages(self):
        """测试混合语言处理"""
        result = self.handler.process_increment("Hello 世界")
        assert result == "Hello 世界"
    
    def test_special_characters(self):
        """测试特殊字符处理"""
        result = self.handler.process_increment("你好@#￥%……")
        assert result == "你好@#￥%……"
    
    def test_newline_characters(self):
        """测试换行符处理"""
        result = self.handler.process_increment("你好\n世界")
        assert result == "你好\n世界"
