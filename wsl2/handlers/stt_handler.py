"""STT 业务逻辑处理"""

from typing import Optional


class SttHandler:
    """STT 业务逻辑处理
    
    职责：
    - 文本清洗、格式化
    - 结果验证、后处理
    - 不包含任何 API 调用逻辑
    """
    
    def __init__(self, stt_client):
        """初始化
        
        Args:
            stt_client: DashScope Recognition 客户端（由容器注入）
        """
        self.stt_client = stt_client
    
    def process_increment(self, text: str) -> str:
        """处理增量识别结果
        
        Args:
            text: 原始识别文本
            
        Returns:
            清洗后的文本
        """
        if not text:
            return ""
        return text.strip()
    
    def process_final(self, text: str) -> Optional[str]:
        """处理最终识别结果
        
        Args:
            text: 原始识别文本
            
        Returns:
            验证通过的文本，如果无效则返回 None
        """
        if not text:
            return None
        
        cleaned = text.strip()
        
        # 验证：长度至少 2 个字符
        if len(cleaned) < 2:
            return None
        
        return cleaned
    
    def validate_text(self, text: str) -> bool:
        """验证文本是否有效
        
        Args:
            text: 待验证文本
            
        Returns:
            是否有效
        """
        if not text:
            return False
        
        cleaned = text.strip()
        return len(cleaned) >= 2
