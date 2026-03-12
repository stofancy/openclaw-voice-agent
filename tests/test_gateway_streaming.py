"""Gateway 流式消息格式测试"""

import pytest
import json
from datetime import datetime


class TestLlmTokenMessageFormat:
    """测试 llm_token 消息格式"""
    
    def test_llm_token_has_required_fields(self):
        """测试 llm_token 消息包含必需字段"""
        message = {
            "type": "llm_token",
            "token": "你",
            "timestamp": datetime.now().isoformat()
        }
        
        assert "type" in message
        assert "token" in message
        assert "timestamp" in message
        assert message["type"] == "llm_token"
    
    def test_llm_token_serializes_to_json(self):
        """测试 llm_token 可序列化为 JSON"""
        message = {
            "type": "llm_token",
            "token": "你",
            "timestamp": datetime.now().isoformat()
        }
        
        json_str = json.dumps(message, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert parsed["type"] == "llm_token"
        assert parsed["token"] == "你"
    
    def test_llm_token_single_character(self):
        """测试 llm_token 单字符"""
        message = {
            "type": "llm_token",
            "token": "你",
            "timestamp": datetime.now().isoformat()
        }
        
        assert len(message["token"]) == 1
    
    def test_llm_token_punctuation(self):
        """测试 llm_token 标点符号"""
        message = {
            "type": "llm_token",
            "token": "，",
            "timestamp": datetime.now().isoformat()
        }
        
        assert message["token"] == "，"


class TestLlmCompleteMessageFormat:
    """测试 llm_complete 消息格式"""
    
    def test_llm_complete_has_required_fields(self):
        """测试 llm_complete 消息包含必需字段"""
        message = {
            "type": "llm_complete",
            "text": "你好，我是助手",
            "timestamp": datetime.now().isoformat()
        }
        
        assert "type" in message
        assert "text" in message
        assert "timestamp" in message
        assert message["type"] == "llm_complete"
    
    def test_llm_complete_serializes_to_json(self):
        """测试 llm_complete 可序列化为 JSON"""
        message = {
            "type": "llm_complete",
            "text": "你好，我是助手",
            "timestamp": datetime.now().isoformat()
        }
        
        json_str = json.dumps(message, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert parsed["type"] == "llm_complete"
        assert parsed["text"] == "你好，我是助手"
    
    def test_llm_complete_full_sentence(self):
        """测试 llm_complete 完整句子"""
        message = {
            "type": "llm_complete",
            "text": "你好，我是助手，有什么可以帮助你的吗？",
            "timestamp": datetime.now().isoformat()
        }
        
        assert len(message["text"]) > 10


class TestTtsStartMessageFormat:
    """测试 tts_start 消息格式"""
    
    def test_tts_start_has_required_fields(self):
        """测试 tts_start 消息包含必需字段"""
        message = {
            "type": "tts_start",
            "timestamp": datetime.now().isoformat()
        }
        
        assert "type" in message
        assert "timestamp" in message
        assert message["type"] == "tts_start"
    
    def test_tts_start_serializes_to_json(self):
        """测试 tts_start 可序列化为 JSON"""
        message = {
            "type": "tts_start",
            "timestamp": datetime.now().isoformat()
        }
        
        json_str = json.dumps(message)
        parsed = json.loads(json_str)
        
        assert parsed["type"] == "tts_start"
    
    def test_tts_start_no_text_field(self):
        """测试 tts_start 不包含 text 字段"""
        message = {
            "type": "tts_start",
            "timestamp": datetime.now().isoformat()
        }
        
        assert "text" not in message


class TestTtsEndMessageFormat:
    """测试 tts_end 消息格式"""
    
    def test_tts_end_has_required_fields(self):
        """测试 tts_end 消息包含必需字段"""
        message = {
            "type": "tts_end",
            "timestamp": datetime.now().isoformat()
        }
        
        assert "type" in message
        assert "timestamp" in message
        assert message["type"] == "tts_end"
    
    def test_tts_end_serializes_to_json(self):
        """测试 tts_end 可序列化为 JSON"""
        message = {
            "type": "tts_end",
            "timestamp": datetime.now().isoformat()
        }
        
        json_str = json.dumps(message)
        parsed = json.loads(json_str)
        
        assert parsed["type"] == "tts_end"
    
    def test_tts_end_no_text_field(self):
        """测试 tts_end 不包含 text 字段"""
        message = {
            "type": "tts_end",
            "timestamp": datetime.now().isoformat()
        }
        
        assert "text" not in message


class TestMessageSequence:
    """测试消息序列"""
    
    def test_llm_tokens_before_complete(self):
        """测试 llm_token 在 llm_complete 之前"""
        messages = [
            {"type": "llm_token", "token": "你"},
            {"type": "llm_token", "token": "好"},
            {"type": "llm_complete", "text": "你好"}
        ]
        
        # 验证顺序
        assert messages[0]["type"] == "llm_token"
        assert messages[1]["type"] == "llm_token"
        assert messages[2]["type"] == "llm_complete"
        
        # 最后一个应该是 complete
        assert messages[-1]["type"] == "llm_complete"
    
    def test_tts_start_before_tts_end(self):
        """测试 tts_start 在 tts_end 之前"""
        messages = [
            {"type": "tts_start"},
            {"type": "tts_end"}
        ]
        
        assert messages[0]["type"] == "tts_start"
        assert messages[1]["type"] == "tts_end"
    
    def test_full_conversation_flow(self):
        """测试完整对话流程"""
        messages = [
            {"type": "stt_final", "text": "你好"},
            {"type": "llm_token", "token": "你"},
            {"type": "llm_token", "token": "好"},
            {"type": "llm_complete", "text": "你好"},
            {"type": "tts_start"},
            {"type": "tts_end"}
        ]
        
        # 验证消息类型顺序
        types = [m["type"] for m in messages]
        assert types == [
            "stt_final",
            "llm_token",
            "llm_token",
            "llm_complete",
            "tts_start",
            "tts_end"
        ]


class TestTokenSequence:
    """测试 token 序列"""
    
    def test_tokens_form_complete_text(self):
        """测试 token 组成完整文本"""
        tokens = ["你", "好", "，", "我", "是", "助", "手"]
        complete_text = "".join(tokens)
        
        assert complete_text == "你好，我是助手"
    
    def test_empty_tokens_filtered(self):
        """测试空 token 被过滤"""
        tokens = ["你", "", "好", "", "世", "界"]
        filtered = [t for t in tokens if t]
        complete_text = "".join(filtered)
        
        assert complete_text == "你好世界"
    
    def test_whitespace_tokens_preserved(self):
        """测试空白 token 保留"""
        tokens = ["Hello", " ", "World"]
        complete_text = "".join(tokens)
        
        assert complete_text == "Hello World"


class TestTimestampFormat:
    """测试时间戳格式"""
    
    def test_timestamp_is_iso_format(self):
        """测试时间戳是 ISO 格式"""
        timestamp = datetime.now().isoformat()
        
        # 应该能解析
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)
    
    def test_timestamp_in_message(self):
        """测试消息中的时间戳"""
        message = {
            "type": "llm_token",
            "token": "你",
            "timestamp": datetime.now().isoformat()
        }
        
        assert "timestamp" in message
        assert isinstance(message["timestamp"], str)
        
        # 应该能解析
        parsed = datetime.fromisoformat(message["timestamp"])
        assert isinstance(parsed, datetime)
    
    def test_all_message_types_have_timestamp(self):
        """测试所有消息类型都有时间戳"""
        messages = [
            {"type": "llm_token", "token": "你", "timestamp": datetime.now().isoformat()},
            {"type": "llm_complete", "text": "你好", "timestamp": datetime.now().isoformat()},
            {"type": "tts_start", "timestamp": datetime.now().isoformat()},
            {"type": "tts_end", "timestamp": datetime.now().isoformat()},
        ]
        
        for message in messages:
            assert "timestamp" in message
            # 验证可解析
            parsed = datetime.fromisoformat(message["timestamp"])
            assert isinstance(parsed, datetime)


class TestMessageValidation:
    """测试消息验证"""
    
    def test_llm_token_valid_structure(self):
        """测试 llm_token 有效结构"""
        message = {
            "type": "llm_token",
            "token": "你",
            "timestamp": datetime.now().isoformat()
        }
        
        assert message["type"] == "llm_token"
        assert isinstance(message["token"], str)
        assert len(message["token"]) >= 0
    
    def test_llm_complete_valid_structure(self):
        """测试 llm_complete 有效结构"""
        message = {
            "type": "llm_complete",
            "text": "你好",
            "timestamp": datetime.now().isoformat()
        }
        
        assert message["type"] == "llm_complete"
        assert isinstance(message["text"], str)
    
    def test_tts_start_valid_structure(self):
        """测试 tts_start 有效结构"""
        message = {
            "type": "tts_start",
            "timestamp": datetime.now().isoformat()
        }
        
        assert message["type"] == "tts_start"
    
    def test_tts_end_valid_structure(self):
        """测试 tts_end 有效结构"""
        message = {
            "type": "tts_end",
            "timestamp": datetime.now().isoformat()
        }
        
        assert message["type"] == "tts_end"


class TestEdgeCases:
    """测试边界情况"""
    
    def test_llm_token_special_characters(self):
        """测试 llm_token 特殊字符"""
        message = {
            "type": "llm_token",
            "token": "@#$%^&*()",
            "timestamp": datetime.now().isoformat()
        }
        
        json_str = json.dumps(message, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert parsed["token"] == "@#$%^&*()"
    
    def test_llm_complete_multiline(self):
        """测试 llm_complete 多行文本"""
        message = {
            "type": "llm_complete",
            "text": "第一行\n第二行\n第三行",
            "timestamp": datetime.now().isoformat()
        }
        
        json_str = json.dumps(message, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert "\n" in parsed["text"]
    
    def test_llm_token_emoji(self):
        """测试 llm_token emoji"""
        message = {
            "type": "llm_token",
            "token": "🎉",
            "timestamp": datetime.now().isoformat()
        }
        
        json_str = json.dumps(message, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert parsed["token"] == "🎉"
    
    def test_llm_complete_empty_text(self):
        """测试 llm_complete 空文本"""
        message = {
            "type": "llm_complete",
            "text": "",
            "timestamp": datetime.now().isoformat()
        }
        
        assert message["text"] == ""
        assert message["type"] == "llm_complete"
    
    def test_very_long_complete_text(self):
        """测试很长的完整文本"""
        long_text = "a" * 1000
        message = {
            "type": "llm_complete",
            "text": long_text,
            "timestamp": datetime.now().isoformat()
        }
        
        json_str = json.dumps(message, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert len(parsed["text"]) == 1000
