from abc import ABC, abstractmethod
from typing import Callable, Optional, Generator


class WsClient(ABC):
    """WebSocket 客户端接口"""
    
    @abstractmethod
    async def send(self, data: dict) -> None:
        """发送 WebSocket 消息"""
        pass
    
    @abstractmethod
    async def recv(self) -> dict:
        """接收 WebSocket 消息"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭 WebSocket 连接"""
        pass


class SttApi(ABC):
    """STT API 接口"""
    
    @abstractmethod
    def start(self) -> None:
        """开始语音识别会话"""
        pass
    
    @abstractmethod
    def send_audio_frame(self, data: bytes) -> None:
        """发送音频帧"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """停止语音识别会话"""
        pass


class TtsApi(ABC):
    """TTS API 接口"""
    
    @abstractmethod
    def connect(self) -> None:
        """连接 TTS 服务"""
        pass
    
    @abstractmethod
    def send_text(self, text: str) -> None:
        """发送文本进行合成"""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """提交 TTS 请求"""
        pass


class AgentClient(ABC):
    """Agent 调用接口"""
    
    @abstractmethod
    def call(self, message: str) -> str:
        """同步调用 Agent"""
        pass
    
    @abstractmethod
    def call_streaming(self, message: str) -> Generator[str, None, None]:
        """流式调用 Agent"""
        pass
