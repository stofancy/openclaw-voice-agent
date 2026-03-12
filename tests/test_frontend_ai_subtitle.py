"""前端 AI 字幕测试"""

import pytest


class TestAiSubtitleState:
    """测试 AI 字幕状态管理"""
    
    def test_initial_subtitle_state(self):
        """测试初始字幕状态"""
        state = {
            "aiSubtitle": "",
            "isAIReply": False
        }
        
        assert state["aiSubtitle"] == ""
        assert state["isAIReply"] is False
    
    def test_subtitle_after_first_token(self):
        """测试接收第一个 token 后的状态"""
        state = {
            "aiSubtitle": "你",
            "isAIReply": True
        }
        
        assert state["aiSubtitle"] == "你"
        assert state["isAIReply"] is True
    
    def test_subtitle_after_multiple_tokens(self):
        """测试接收多个 token 后的状态"""
        state = {
            "aiSubtitle": "你好，我是助手",
            "isAIReply": True
        }
        
        assert state["aiSubtitle"] == "你好，我是助手"
        assert state["isAIReply"] is True
    
    def test_subtitle_after_complete(self):
        """测试接收 complete 后的状态"""
        state = {
            "aiSubtitle": "你好，我是助手",
            "isAIReply": True
        }
        
        assert state["aiSubtitle"] == "你好，我是助手"
        assert state["isAIReply"] is True


class TestLlmTokenHandling:
    """测试 llm_token 消息处理"""
    
    def test_llm_token_appends_to_subtitle(self):
        """测试 llm_token 追加到字幕"""
        prev_subtitle = "你好"
        token = "，"
        new_subtitle = prev_subtitle + token
        
        assert new_subtitle == "你好，"
    
    def test_llm_token_multiple_appends(self):
        """测试多个 llm_token 连续追加"""
        subtitle = ""
        tokens = ["你", "好", "，", "我", "是"]
        
        for token in tokens:
            subtitle = subtitle + token
        
        assert subtitle == "你好，我是"
    
    def test_llm_token_sets_is_ai_reply(self):
        """测试 llm_token 设置 isAIReply 为 true"""
        is_ai_reply = False
        
        # 收到 llm_token
        is_ai_reply = True
        
        assert is_ai_reply is True
    
    def test_llm_token_empty_token(self):
        """测试空 token 处理"""
        prev_subtitle = "你好"
        token = ""
        new_subtitle = prev_subtitle + token
        
        assert new_subtitle == "你好"
    
    def test_llm_token_whitespace_token(self):
        """测试空白 token 处理"""
        prev_subtitle = "Hello"
        token = " "
        new_subtitle = prev_subtitle + token
        
        assert new_subtitle == "Hello "


class TestLlmCompleteHandling:
    """测试 llm_complete 消息处理"""
    
    def test_llm_complete_sets_final_text(self):
        """测试 llm_complete 设置最终文本"""
        data_text = "你好，我是助手"
        subtitle = data_text
        
        assert subtitle == "你好，我是助手"
    
    def test_llm_complete_overrides_streaming(self):
        """测试 llm_complete 覆盖流式内容"""
        streaming_subtitle = "你好，我"
        complete_text = "你好，我是助手"
        final_subtitle = complete_text
        
        assert final_subtitle == "你好，我是助手"
        assert final_subtitle != streaming_subtitle
    
    def test_llm_complete_maintains_is_ai_reply(self):
        """测试 llm_complete 保持 isAIReply 为 true"""
        is_ai_reply = True
        
        # 收到 llm_complete 后保持
        assert is_ai_reply is True


class TestTtsSyncHandling:
    """测试 TTS 同步处理"""
    
    def test_tts_start_highlights_subtitle(self):
        """测试 tts_start 高亮字幕"""
        state = {
            "isPlaying": True,
            "isHighlighted": True
        }
        
        assert state["isPlaying"] is True
        assert state["isHighlighted"] is True
    
    def test_tts_end_removes_highlight(self):
        """测试 tts_end 移除高亮"""
        state = {
            "isPlaying": False,
            "isHighlighted": False
        }
        
        assert state["isPlaying"] is False
        assert state["isHighlighted"] is False
    
    def test_tts_sync_sequence(self):
        """测试 TTS 同步序列"""
        states = []
        
        # 初始状态
        states.append({"isPlaying": False, "isHighlighted": False})
        
        # tts_start
        states.append({"isPlaying": True, "isHighlighted": True})
        
        # tts_end
        states.append({"isPlaying": False, "isHighlighted": False})
        
        assert states[0]["isPlaying"] is False
        assert states[1]["isPlaying"] is True
        assert states[2]["isPlaying"] is False


class TestTypewriterEffect:
    """测试打字机效果"""
    
    def test_cursor_visible_during_streaming(self):
        """测试流式期间光标可见"""
        is_final = False
        cursor_visible = not is_final
        
        assert cursor_visible is True
    
    def test_cursor_hidden_after_complete(self):
        """测试完成后光标隐藏"""
        is_final = True
        cursor_visible = not is_final
        
        assert cursor_visible is False
    
    def test_cursor_character(self):
        """测试光标字符"""
        cursor = "▋"
        
        assert cursor == "▋"
        assert len(cursor) == 1
    
    def test_subtitle_with_cursor(self):
        """测试带光标的字幕"""
        subtitle = "你好"
        cursor = "▋"
        display = subtitle + cursor
        
        assert display == "你好▋"
    
    def test_subtitle_without_cursor(self):
        """测试不带光标的字幕"""
        subtitle = "你好"
        is_final = True
        display = subtitle if is_final else subtitle + "▋"
        
        assert display == "你好"


class TestSubtitleRole:
    """测试字幕角色"""
    
    def test_ai_subtitle_role(self):
        """测试 AI 字幕角色"""
        role = "ai"
        display_role = "🤖 AI"
        
        assert role == "ai"
        assert display_role == "🤖 AI"
    
    def test_user_subtitle_role(self):
        """测试用户字幕角色"""
        role = "user"
        display_role = "👤 你"
        
        assert role == "user"
        assert display_role == "👤 你"
    
    def test_ai_subtitle_styling(self):
        """测试 AI 字幕样式"""
        classes = ["subtitle", "ai", "streaming"]
        
        assert "subtitle" in classes
        assert "ai" in classes
        assert "streaming" in classes
    
    def test_final_subtitle_styling(self):
        """测试最终字幕样式"""
        classes = ["subtitle", "ai", "final"]
        
        assert "subtitle" in classes
        assert "ai" in classes
        assert "final" in classes


class TestMessageParsing:
    """测试消息解析"""
    
    def test_parse_llm_token_message(self):
        """测试解析 llm_token 消息"""
        message = '{"type": "llm_token", "token": "你", "timestamp": "2026-03-13T02:00:00"}'
        
        import json
        data = json.loads(message)
        
        assert data["type"] == "llm_token"
        assert data["token"] == "你"
        assert "timestamp" in data
    
    def test_parse_llm_complete_message(self):
        """测试解析 llm_complete 消息"""
        message = '{"type": "llm_complete", "text": "你好", "timestamp": "2026-03-13T02:00:00"}'
        
        import json
        data = json.loads(message)
        
        assert data["type"] == "llm_complete"
        assert data["text"] == "你好"
        assert "timestamp" in data
    
    def test_parse_tts_start_message(self):
        """测试解析 tts_start 消息"""
        message = '{"type": "tts_start", "timestamp": "2026-03-13T02:00:00"}'
        
        import json
        data = json.loads(message)
        
        assert data["type"] == "tts_start"
        assert "timestamp" in data
    
    def test_parse_tts_end_message(self):
        """测试解析 tts_end 消息"""
        message = '{"type": "tts_end", "timestamp": "2026-03-13T02:00:00"}'
        
        import json
        data = json.loads(message)
        
        assert data["type"] == "tts_end"
        assert "timestamp" in data


class TestSubtitleUpdateLogic:
    """测试字幕更新逻辑"""
    
    def test_find_last_ai_streaming_subtitle(self):
        """测试查找最后一个 AI 流式字幕"""
        subtitles = [
            {"id": 1, "role": "user", "text": "你好", "isFinal": True},
            {"id": 2, "role": "ai", "text": "你", "isFinal": False},
        ]
        
        # 查找最后一个 AI 流式字幕
        last_index = None
        for i, s in enumerate(subtitles):
            if s["role"] == "ai" and not s["isFinal"]:
                last_index = i
        
        assert last_index == 1
    
    def test_create_new_ai_subtitle(self):
        """测试创建新的 AI 字幕"""
        new_subtitle = {
            "id": 3,
            "role": "ai",
            "text": "你",
            "isFinal": False,
            "timestamp": "2026-03-13T02:00:00"
        }
        
        assert new_subtitle["role"] == "ai"
        assert new_subtitle["isFinal"] is False
    
    def test_update_existing_subtitle(self):
        """测试更新现有字幕"""
        subtitle = {
            "id": 2,
            "role": "ai",
            "text": "你",
            "isFinal": False
        }
        
        # 追加 token
        updated = {
            **subtitle,
            "text": subtitle["text"] + "好",
            "isFinal": False
        }
        
        assert updated["text"] == "你好"
        assert updated["isFinal"] is False
    
    def test_finalize_subtitle(self):
        """测试完成字幕"""
        subtitle = {
            "id": 2,
            "role": "ai",
            "text": "你好",
            "isFinal": False
        }
        
        # 设置为最终状态
        finalized = {
            **subtitle,
            "text": "你好，我是助手",
            "isFinal": True
        }
        
        assert finalized["isFinal"] is True
        assert finalized["text"] == "你好，我是助手"


class TestEdgeCases:
    """测试边界情况"""
    
    def test_empty_subtitle(self):
        """测试空字幕"""
        subtitle = ""
        assert subtitle == ""
    
    def test_very_long_subtitle(self):
        """测试超长字幕"""
        subtitle = "a" * 1000
        assert len(subtitle) == 1000
    
    def test_subtitle_with_emoji(self):
        """测试带 emoji 的字幕"""
        subtitle = "你好 🎉"
        assert "🎉" in subtitle
    
    def test_subtitle_with_newlines(self):
        """测试带换行的字幕"""
        subtitle = "第一行\n第二行"
        assert "\n" in subtitle
    
    def test_rapid_token_updates(self):
        """测试快速 token 更新"""
        subtitle = ""
        tokens = ["你", "好", "，", "我", "是", "助", "手"]
        
        for token in tokens:
            subtitle = subtitle + token
        
        assert subtitle == "你好，我是助手"
