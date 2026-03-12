# ⚠️ DEPRECATED - 已废弃
# 此文件已废弃，请使用新的 handlers 模块：
# - wsl2/handlers/stt_handler.py
# - wsl2/handlers/tts_handler.py
# - wsl2/handlers/agent_handler.py
# - wsl2/handlers/websocket_handler.py
# 
# 依赖注入容器：wsl2/container.py
#
# 废弃原因：
# 1. 抽象接口层增加不必要的复杂度
# 2. 直接使用 DashScope 原生 API 更简洁
# 3. 业务逻辑已迁移到 handlers 模块
#
# 废弃日期：2026-03-13

from abc import ABC, abstractmethod
from typing import Callable, Optional, Generator


class WsClient(ABC):
    """WebSocket 客户端接口 - DEPRECATED"""
    
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
    """STT API 接口 - DEPRECATED"""
    
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
    """TTS API 接口 - DEPRECATED"""
    
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
    """Agent 调用接口 - DEPRECATED"""
    
    @abstractmethod
    def call(self, message: str) -> str:
        """同步调用 Agent"""
        pass
    
    @abstractmethod
    def call_streaming(self, message: str) -> Generator[str, None, None]:
        """流式调用 Agent"""
        pass
