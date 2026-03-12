#!/usr/bin/env python3
"""
⚠️ DEPRECATED - 已废弃

百炼实时语音识别 (STT) SDK

此文件已废弃，请使用新的 handlers 模块：
- wsl2/handlers/stt_handler.py (业务逻辑)
- wsl2/container.py (依赖注入，使用原生 Recognition)

废弃原因：
1. 重复封装 DashScope ASRRealtime API
2. 新方案直接使用原生 API + 依赖注入
3. 业务逻辑已迁移到 handlers

废弃日期：2026-03-13
"""

import asyncio
import json
import dashscope
from dashscope.audio.asr_realtime import ASRRealtime, ASRRealtimeCallback

class STTCallback(ASRRealtimeCallback):
    """STT 回调 - DEPRECATED"""
    
    def __init__(self, gateway):
        self.gateway = gateway
        self.result_text = ""
        self.final_text = ""
        
    def on_open(self) -> None:
        print("✅ STT 连接已建立")
        
    def on_close(self, close_status_code: int, close_msg: str) -> None:
        print(f"🔴 STT 连接关闭：code={close_status_code}, msg={close_msg}")
        
    def on_event(self, response: str) -> None:
        try:
            data = json.loads(response) if isinstance(response, str) else response
            event_type = data.get('type', 'unknown')
            
            if event_type == 'session.created':
                session_id = data.get('session', {}).get('id', 'unknown')
                print(f"📋 STT 会话创建：{session_id}")
                
            elif event_type == 'recognizer.result.increment':
                # 增量识别结果
                text = data.get('result', {}).get('text', '')
                if text:
                    self.result_text = text
                    print(f"📝 识别中：{text}")
                    
            elif event_type == 'recognizer.result.completed':
                # 完成识别结果
                text = data.get('result', {}).get('text', '')
                if text:
                    self.final_text = text
                    print(f"✅ 识别完成：{text}")
                    
            elif event_type == 'session.finished':
                print(f"🔴 STT 会话结束")
                
        except Exception as e:
            print(f'❌ STT 回调错误：{e}')


class RealtimeSTT:
    """实时语音识别 - DEPRECATED"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.stt_realtime = None
        self.stt_callback = None
        self.is_connected = False
        
    def connect(self):
        """连接 STT 服务"""
        if self.stt_realtime and self.is_connected:
            return
        
        dashscope.api_key = self.api_key
        self.stt_callback = STTCallback(None)
        self.stt_realtime = ASRRealtime(
            model='paraformer-realtime-v2',
            callback=self.stt_callback,
        )
        self.stt_realtime.connect()
        self.is_connected = True
        print("✅ STT 已连接")
        
    def send_audio(self, audio_data):
        """发送音频数据"""
        if self.stt_realtime and self.is_connected:
            self.stt_realtime.send_audio(audio_data)
            
    def finish(self):
        """结束识别"""
        if self.stt_realtime:
            self.stt_realtime.finish()
            
    def get_result(self):
        """获取识别结果"""
        if self.stt_callback:
            return self.stt_callback.final_text or self.stt_callback.result_text
        return ""
