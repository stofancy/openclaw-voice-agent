#!/usr/bin/env python3
"""
百炼语音识别 (STT) SDK
"""

import dashscope
from dashscope.audio.asr import Recognition

class BaiLianSTT:
    """百炼语音识别"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        dashscope.api_key = api_key
        
    def recognize(self, audio_file_path):
        """识别音频文件"""
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
        """识别音频字节数据"""
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
        """创建 WAV 文件头"""
        import struct
        byte_rate = sample_rate * channels * sample_width
        block_align = channels * sample_width
        
        header = struct.pack('<4sI4s', b'RIFF', 36 + data_len, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, sample_width * 8)
        header += struct.pack('<4sI', b'data', data_len)
        return header
