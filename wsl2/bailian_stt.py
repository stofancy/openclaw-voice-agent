#!/usr/bin/env python3
"""
⚠️ DEPRECATED - 已废弃

百炼语音识别 (STT) SDK

此文件已废弃，请使用新的 handlers 模块：
- wsl2/handlers/stt_handler.py (业务逻辑)
- wsl2/container.py (依赖注入)

废弃原因：
1. 重复封装 DashScope Recognition API
2. 业务逻辑与 API 调用耦合
3. 新方案使用依赖注入，更易测试和维护

废弃日期：2026-03-13
"""

import dashscope
from dashscope.audio.asr import Recognition

class BaiLianSTT:
    """百炼语音识别 - DEPRECATED"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        dashscope.api_key = api_key
        
    def recognize(self, audio_file_path):
        """识别音频文件 - DEPRECATED"""
        try:
            recognition = Recognition()
            result = recognition.call(audio_file_path)
            
            if result.status_code == 200:
                text = result.get('output', {}).get('text', '')
                return text
            else:
                print(f"❌ STT 失败：{result.message}")
                return ""
        except Exception as e:
            print(f"❌ STT 异常：{e}")
            return ""
            
    def recognize_bytes(self, audio_data):
        """识别音频字节数据 - DEPRECATED"""
        # 需要保存到临时文件
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # 写入 WAV 格式
            f.write(self._create_wav_header(len(audio_data), 16000, 1, 2))
            f.write(audio_data)
            temp_path = f.name
            
        try:
            return self.recognize(temp_path)
        finally:
            os.unlink(temp_path)
            
    def _create_wav_header(self, data_len, sample_rate, channels, sample_width):
        """创建 WAV 文件头 - DEPRECATED"""
        import struct
        byte_rate = sample_rate * channels * sample_width
        block_align = channels * sample_width
        
        header = struct.pack('<4sI4s', b'RIFF', 36 + data_len, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, sample_width * 8)
        header += struct.pack('<4sI', b'data', data_len)
        return header
