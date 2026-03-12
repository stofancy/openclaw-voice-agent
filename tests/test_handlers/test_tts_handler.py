"""TTS Handler 业务逻辑测试"""

import pytest
from unittest.mock import Mock

from wsl2.handlers.tts_handler import TtsHandler


class TestTtsHandlerInitialization:
    """测试 TTS Handler 初始化"""
    
    def test_init_with_client(self):
        """测试带客户端初始化"""
        mock_client = Mock()
        handler = TtsHandler(tts_client=mock_client)
        
        assert handler.tts_client == mock_client
    
    def test_init_without_client_raises(self):
        """测试不带客户端初始化会失败"""
        with pytest.raises(TypeError):
            TtsHandler()


class TestPreprocessText:
    """测试文本预处理"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.mock_client = Mock()
        self.handler = TtsHandler(tts_client=self.mock_client)
    
    def test_preprocess_normal_text(self):
        """测试预处理正常文本"""
        result = self.handler.preprocess_text("你好世界")
        assert result == "你好世界"
    
    def test_preprocess_text_with_whitespace(self):
        """测试预处理带空格的文本"""
        result = self.handler.preprocess_text("  你好世界  ")
        assert result == "你好世界"
    
    def test_preprocess_empty_string(self):
        """测试预处理空字符串"""
        result = self.handler.preprocess_text("")
        assert result is None
    
    def test_preprocess_none(self):
        """测试预处理 None"""
        result = self.handler.preprocess_text(None)
        assert result is None
    
    def test_preprocess_single_char(self):
        """测试预处理单字符（满足最小长度）"""
        result = self.handler.preprocess_text("你")
        assert result == "你"
    
    def test_preprocess_whitespace_only(self):
        """测试预处理纯空格文本"""
        result = self.handler.preprocess_text("   ")
        assert result is None


class TestProcessAudioChunk:
    """测试音频数据块处理"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.mock_client = Mock()
        self.handler = TtsHandler(tts_client=self.mock_client)
    
    def test_process_audio_chunk(self):
        """测试处理音频数据块"""
        audio_data = b"\x00\x01\x02\x03\x04"
        result = self.handler.process_audio_chunk(audio_data)
        assert result == audio_data
    
    def test_process_empty_audio_chunk(self):
        """测试处理空音频数据块"""
        audio_data = b""
        result = self.handler.process_audio_chunk(audio_data)
        assert result == audio_data
    
    def test_process_large_audio_chunk(self):
        """测试处理大音频数据块"""
        audio_data = b"\x00" * 1024
        result = self.handler.process_audio_chunk(audio_data)
        assert result == audio_data
        assert len(result) == 1024


class TestValidateResponse:
    """测试 TTS 响应验证"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.mock_client = Mock()
        self.handler = TtsHandler(tts_client=self.mock_client)
    
    def test_validate_response_with_audio(self):
        """测试验证带音频数据的响应"""
        response = {'audio': b'\x00\x01\x02'}
        assert self.handler.validate_response(response) is True
    
    def test_validate_response_with_data(self):
        """测试验证带 data 字段的响应"""
        response = {'data': b'\x00\x01\x02'}
        assert self.handler.validate_response(response) is True
    
    def test_validate_response_empty_dict(self):
        """测试验证空字典响应"""
        response = {}
        assert self.handler.validate_response(response) is False
    
    def test_validate_response_none(self):
        """测试验证 None 响应"""
        assert self.handler.validate_response(None) is False
    
    def test_validate_response_without_audio_keys(self):
        """测试验证没有音频键的响应"""
        response = {'status': 'success', 'message': 'ok'}
        assert self.handler.validate_response(response) is False
    
    def test_validate_response_with_both_keys(self):
        """测试验证同时有 audio 和 data 的响应"""
        response = {'audio': b'\x00', 'data': b'\x01'}
        assert self.handler.validate_response(response) is True


class TestEdgeCases:
    """测试边界情况"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.mock_client = Mock()
        self.handler = TtsHandler(tts_client=self.mock_client)
    
    def test_preprocess_unicode_text(self):
        """测试预处理 Unicode 文本"""
        result = self.handler.preprocess_text("🎉🚀")
        assert result == "🎉🚀"
    
    def test_preprocess_mixed_languages(self):
        """测试预处理混合语言文本"""
        result = self.handler.preprocess_text("Hello 世界")
        assert result == "Hello 世界"
    
    def test_preprocess_newline_text(self):
        """测试预处理带换行符的文本"""
        result = self.handler.preprocess_text("你好\n世界")
        assert result == "你好\n世界"
    
    def test_preprocess_tab_text(self):
        """测试预处理带制表符的文本"""
        result = self.handler.preprocess_text("你好\t世界")
        assert result == "你好\t世界"
    
    def test_audio_chunk_mutable(self):
        """测试音频数据块处理不修改原数据"""
        original = b"\x00\x01\x02"
        result = self.handler.process_audio_chunk(original)
        assert result is original  # 直接返回，不创建副本
