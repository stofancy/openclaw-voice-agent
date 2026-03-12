"""依赖注入容器

使用 dependency-injector 管理所有外部依赖和业务 handlers。
"""

from dependency_injector import containers, providers

# DashScope 原生客户端
from dashscope.audio.asr import Recognition
from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime

# WebSocket 客户端
import websockets

# 业务 Handlers
from .handlers import SttHandler, TtsHandler, AgentHandler, WebSocketHandler


class Container(containers.DeclarativeContainer):
    """依赖注入容器
    
    职责：
    - 管理所有外部依赖（DashScope 客户端、WebSocket）
    - 管理业务 handlers
    - 提供统一的依赖获取接口
    
    使用示例：
        container = Container()
        container.config.from_dict({
            'stt': {'model': 'paraformer-realtime-v2'},
            'tts': {'model': 'qwen3-tts-instruct-flash-realtime'},
        })
        
        # 获取 handler
        stt_handler = container.stt_handler()
    """
    
    # 配置
    config = providers.Configuration()
    
    # ==================== 外部依赖（原生库） ====================
    
    # STT 客户端 - 使用 DashScope 原生 Recognition
    stt_client = providers.Singleton(
        Recognition,
        model='paraformer-realtime-v2',
        format='pcm',
        sample_rate=16000,
    )
    
    # TTS 客户端 - 使用 DashScope 原生 QwenTtsRealtime
    tts_client = providers.Singleton(
        QwenTtsRealtime,
        model='qwen3-tts-instruct-flash-realtime',
    )
    
    # WebSocket 客户端工厂 - 使用 websockets 原生库
    websocket_client = providers.Factory(
        websockets.connect,
    )
    
    # ==================== 业务 Handlers ====================
    
    # STT 业务处理器
    stt_handler = providers.Factory(
        SttHandler,
        stt_client=stt_client,
    )
    
    # TTS 业务处理器
    tts_handler = providers.Factory(
        TtsHandler,
        tts_client=tts_client,
    )
    
    # Agent 业务处理器
    agent_handler = providers.Factory(
        AgentHandler,
    )
    
    # WebSocket 消息路由器
    websocket_handler = providers.Factory(
        WebSocketHandler,
    )
