"""Agent 调用业务逻辑处理"""

from typing import Generator, Optional, AsyncGenerator


class AgentHandler:
    """Agent 调用业务逻辑处理
    
    职责：
    - 消息预处理
    - 响应后处理
    - 流式响应处理
    - 不包含任何 API 调用逻辑
    """
    
    def __init__(self, agent_client=None):
        """初始化
        
        Args:
            agent_client: Agent 客户端（可选，由容器注入）
        """
        self.agent_client = agent_client
        self.streaming_buffer = ""
    
    def preprocess_message(self, message: str) -> Optional[str]:
        """预处理用户消息
        
        Args:
            message: 原始消息
            
        Returns:
            预处理后的消息，如果无效则返回 None
        """
        if not message:
            return None
        
        cleaned = message.strip()
        
        # 验证：长度至少 1 个字符
        if len(cleaned) < 1:
            return None
        
        return cleaned
    
    def process_response(self, response: str) -> str:
        """处理 Agent 响应
        
        Args:
            response: 原始响应
            
        Returns:
            处理后的响应
        """
        if not response:
            return ""
        
        return response.strip()
    
    def process_streaming_chunk(self, chunk: str) -> Optional[str]:
        """处理流式响应块
        
        Args:
            chunk: 原始响应块
            
        Returns:
            处理后的响应块，如果无效则返回 None
        """
        if not chunk:
            return None
        
        cleaned = chunk.strip()
        return cleaned if cleaned else None
    
    def process_llm_token(self, token: str) -> Optional[str]:
        """处理 LLM 流式 token
        
        Args:
            token: 单个 token（字符或词）
            
        Returns:
            处理后的 token，如果无效则返回 None
        """
        if not token:
            return None
        
        # 过滤空白 token
        if token.strip() == "" and len(token) > 0:
            return token  # 保留空白字符用于格式
        
        return token
    
    def validate_message(self, message: str) -> bool:
        """验证消息是否有效
        
        Args:
            message: 待验证消息
            
        Returns:
            是否有效
        """
        if not message:
            return False
        
        cleaned = message.strip()
        return len(cleaned) >= 1
    
    def reset_streaming_buffer(self) -> None:
        """重置流式缓冲区"""
        self.streaming_buffer = ""
    
    def append_to_streaming_buffer(self, token: str) -> str:
        """追加 token 到流式缓冲区
        
        Args:
            token: token 文本
            
        Returns:
            当前缓冲区内容
        """
        if token:
            self.streaming_buffer += token
        return self.streaming_buffer
    
    def get_streaming_buffer(self) -> str:
        """获取当前流式缓冲区内容
        
        Returns:
            缓冲区内容
        """
        return self.streaming_buffer
