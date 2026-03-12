"""TTS 业务逻辑处理"""

from typing import Optional


class TtsHandler:
    """TTS 业务逻辑处理
    
    职责：
    - 文本预处理
    - 合成结果处理
    - 不包含任何 API 调用逻辑
    """
    
    def __init__(self, tts_client):
        """初始化
        
        Args:
            tts_client: DashScope QwenTtsRealtime 客户端（由容器注入）
        """
        self.tts_client = tts_client
    
    def preprocess_text(self, text: str) -> Optional[str]:
        """预处理输入文本
        
        Args:
            text: 原始文本
            
        Returns:
            预处理后的文本，如果无效则返回 None
        """
        if not text:
            return None
        
        cleaned = text.strip()
        
        # 验证：长度至少 1 个字符
        if len(cleaned) < 1:
            return None
        
        return cleaned
    
    def process_audio_chunk(self, audio_data: bytes) -> bytes:
        """处理音频数据块
        
        Args:
            audio_data: 原始音频数据
            
        Returns:
            处理后的音频数据（当前直接返回）
        """
        # 纯业务逻辑：可以在这里添加音频格式转换、采样率调整等
        return audio_data
    
    def validate_response(self, response: dict) -> bool:
        """验证 TTS 响应是否有效
        
        Args:
            response: TTS API 响应
            
        Returns:
            是否有效
        """
        if not response:
            return False
        
        # 检查是否有音频数据
        if 'audio' not in response and 'data' not in response:
            return False
        
        return True
