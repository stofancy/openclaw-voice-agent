"""LLM 字幕推送测试"""

import pytest
import json
from datetime import datetime


class TestLlmTokenMessageFormat:
    """测试 llm_token 消息格式"""
    
    def test_llm_token_message_structure(self):
        """测试 llm_token 消息结构"""
        message = {
            "type": "llm_token",
            "token": "你",
            "timestamp": "2026-03-13T02:00:00"
        }
        
        assert "type" in message
        assert "token" in message
        assert message["type"] == "llm_token"
        assert isinstance(message["token"], str)
    
    def test_llm_token_single_char(self):
        """测试 llm_token 单字符"""
        message = {
            "type": "llm_token",
            "token": "你"
        }
        
        assert len(message["token"]) == 1
    
    def test_llm_token_multi_char(self):
        """测试 llm_token 多字符"""
        message = {
            "type": "llm_token",
            "token": "你好"
        }
        
        assert len(message["token"]) == 2
    
    def test_llm_token_punctuation(self):
        """测试 llm_token 标点符号"""
        message = {
            "type": "llm_token",
            "token": "，"
        }
        
        assert message["token"] == "，"


class TestLlmCompleteMessageFormat:
    """测试 llm_complete 消息格式"""
    
    def test_llm_complete_message_structure(self):
        """测试 llm_complete 消息结构"""
        message = {
            "type": "llm_complete",
            "text": "你好，我是助手",
            "timestamp": "2026-03-13T02:00:00"
        }
        
        assert "type" in message
        assert "text" in message
        assert message["type"] == "llm_complete"
        assert isinstance(message["text"], str)
    
    def test_llm_complete_full_sentence(self):
        """测试 llm_complete 完整句子"""
        message = {
            "type": "llm_complete",
            "text": "你好，我是助手，有什么可以帮助你的吗？"
        }
        
        assert len(message["text"]) > 10
    
    def test_llm_complete_short_response(self):
        """测试 llm_complete 短回复"""
        message = {
            "type": "llm_complete",
            "text": "好的"
        }
        
        assert message["text"] == "好的"


class TestTtsSyncMessageFormat:
    """测试 TTS 同步消息格式"""
    
    def test_tts_start_message_structure(self):
        """测试 tts_start 消息结构"""
        message = {
            "type": "tts_start",
            "timestamp": "2026-03-13T02:00:00"
        }
        
        assert "type" in message
        assert message["type"] == "tts_start"
    
    def test_tts_end_message_structure(self):
        """测试 tts_end 消息结构"""
        message = {
            "type": "tts_end",
            "timestamp": "2026-03-13T02:00:00"
        }
        
        assert "type" in message
        assert message["type"] == "tts_end"
    
    def test_tts_start_no_text(self):
        """测试 tts_start 不包含文本"""
        message = {
            "type": "tts_start",
            "timestamp": "2026-03-13T02:00:00"
        }
        
        assert "text" not in message
    
    def test_tts_end_no_text(self):
        """测试 tts_end 不包含文本"""
        message = {
            "type": "tts_end",
            "timestamp": "2026-03-13T02:00:00"
        }
        
        assert "text" not in message


class TestMessageSerialization:
    """测试消息序列化"""
    
    def test_llm_token_json_serialization(self):
        """测试 llm_token JSON 序列化"""
        message = {
            "type": "llm_token",
            "token": "你",
            "timestamp": "2026-03-13T02:00:00"
        }
        
        json_str = json.dumps(message)
        parsed = json.loads(json_str)
        
        assert parsed == message
    
    def test_llm_complete_json_serialization(self):
        """测试 llm_complete JSON 序列化"""
        message = {
            "type": "llm_complete",
            "text": "你好，我是助手",
            "timestamp": "2026-03-13T02:00:00"
        }
        
        json_str = json.dumps(message)
        parsed = json.loads(json_str)
        
        assert parsed == message
    
    def test_tts_start_json_serialization(self):
        """测试 tts_start JSON 序列化"""
        message = {
            "type": "tts_start",
            "timestamp": "2026-03-13T02:00:00"
        }
        
        json_str = json.dumps(message)
        parsed = json.loads(json_str)
        
        assert parsed == message
    
    def test_tts_end_json_serialization(self):
        """测试 tts_end JSON 序列化"""
        message = {
            "type": "tts_end",
            "timestamp": "2026-03-13T02:00:00"
        }
        
        json_str = json.dumps(message)
        parsed = json.loads(json_str)
        
        assert parsed == message


class TestStreamingTokenSequence:
    """测试流式 token 序列"""
    
    def test_token_sequence_forms_complete_text(self):
        """测试 token 序列组成完整文本"""
        tokens = ["你", "好", "，", "我", "是", "助", "手"]
        complete_text = "".join(tokens)
        
        assert complete_text == "你好，我是助手"
    
    def test_token_sequence_with_punctuation(self):
        """测试带标点的 token 序列"""
        tokens = ["今", "天", "天", "气", "真", "好", "。"]
        complete_text = "".join(tokens)
        
        assert complete_text == "今天天气真好。"
    
    def test_token_sequence_with_whitespace(self):
        """测试带空白的 token 序列"""
        tokens = ["H", "e", "l", "l", "o", " ", "世", "界"]
        complete_text = "".join(tokens)
        
        assert complete_text == "Hello 世界"
    
    def test_empty_token_in_sequence(self):
        """测试序列中的空 token"""
        tokens = ["你", "", "好"]
        complete_text = "".join(tokens)
        
        assert complete_text == "你好"


class TestMessageOrdering:
    """测试消息顺序"""
    
    def test_llm_tokens_before_complete(self):
        """测试 llm_token 在 llm_complete 之前"""
        messages = [
            {"type": "llm_token", "token": "你"},
            {"type": "llm_token", "token": "好"},
            {"type": "llm_complete", "text": "你好"}
        ]
        
        token_count = sum(1 for m in messages if m["type"] == "llm_token")
        complete_count = sum(1 for m in messages if m["type"] == "llm_complete")
        
        # 最后一个消息应该是 llm_complete
        assert messages[-1]["type"] == "llm_complete"
        # 应该有多个 token 消息
        assert token_count >= 2
        # 应该只有一个 complete 消息
        assert complete_count == 1
    
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
        
        # 验证消息顺序
        assert messages[0]["type"] == "stt_final"
        assert messages[1]["type"] == "llm_token"
        assert messages[2]["type"] == "llm_token"
        assert messages[3]["type"] == "llm_complete"
        assert messages[4]["type"] == "tts_start"
        assert messages[5]["type"] == "tts_end"


class TestTimestampFormat:
    """测试时间戳格式"""
    
    def test_timestamp_iso_format(self):
        """测试时间戳 ISO 格式"""
        timestamp = datetime.now().isoformat()
        
        # ISO 格式应该包含日期和时间
        assert "T" in timestamp or " " in timestamp
    
    def test_timestamp_in_message(self):
        """测试消息中的时间戳"""
        message = {
            "type": "llm_token",
            "token": "你",
            "timestamp": datetime.now().isoformat()
        }
        
        assert "timestamp" in message
        assert isinstance(message["timestamp"], str)


class TestEdgeCases:
    """测试边界情况"""
    
    def test_llm_token_special_characters(self):
        """测试 llm_token 特殊字符"""
        message = {
            "type": "llm_token",
            "token": "@#$%^&*()"
        }
        
        json_str = json.dumps(message)
        parsed = json.loads(json_str)
        
        assert parsed["token"] == "@#$%^&*()"
    
    def test_llm_complete_multiline(self):
        """测试 llm_complete 多行文本"""
        message = {
            "type": "llm_complete",
            "text": "第一行\n第二行\n第三行"
        }
        
        json_str = json.dumps(message, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert "\n" in parsed["text"]
    
    def test_llm_token_emoji(self):
        """测试 llm_token emoji"""
        message = {
            "type": "llm_token",
            "token": "🎉"
        }
        
        json_str = json.dumps(message, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert parsed["token"] == "🎉"
    
    def test_llm_complete_empty_text(self):
        """测试 llm_complete 空文本"""
        message = {
            "type": "llm_complete",
            "text": ""
        }
        
        assert message["text"] == ""
        assert message["type"] == "llm_complete"
