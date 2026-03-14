"""
Configuration module for Voice Gateway.
"""
import os
from pathlib import Path
from typing import Optional


def _load_env_file() -> None:
    """Load .env file from project root."""
    # 尝试多个可能的 .env 位置
    possible_paths = [
        # 从当前模块向上查找
        Path(__file__).parent.parent.parent / ".env",
        # 项目根目录（audio-proxy/.env）
        Path(__file__).parent.parent.parent.parent / "audio-proxy" / ".env",
    ]
    
    for env_path in possible_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        # 只设置未定义的环境变量
                        if key not in os.environ:
                            os.environ[key] = value
            return


# 模块加载时自动加载 .env
_load_env_file()


class Config:
    """Application configuration."""
    
    def __init__(self, host=None, port=None, debug=None, stt_service_url=None, 
                 tts_service_url=None, agent_service_url=None,
                 WS_HOST=None, WS_PORT=None, DASHSCOPE_API_KEY=None):
        # Handle both new-style and old-style parameter names
        self.debug = debug if debug is not None else os.getenv("DEBUG", "false").lower() == "true"
        self.host = host if host is not None else WS_HOST if WS_HOST is not None else os.getenv("HOST", "0.0.0.0")
        self.port = port if port is not None else WS_PORT if WS_PORT is not None else int(os.getenv("PORT", "8080"))
        
        # 百炼 API 配置
        self.bailian_api_key = os.getenv("ALI_BAILIAN_API_KEY", "")
        self.bailian_ws_url = os.getenv("BAILIAN_WS_URL", "wss://dashscope.aliyuncs.com/api-ws/v1/realtime")
        self.bailian_asr_url = os.getenv("BAILIAN_ASR_URL", "wss://dashscope.aliyuncs.com/api-ws/v1/realtime")
        self.bailian_tts_url = os.getenv("BAILIAN_TTS_URL", "wss://dashscope.aliyuncs.com/api-ws/v1/realtime")
        self.bailian_model = os.getenv("BAILIAN_MODEL", "qwen3-omni-flash-realtime")
        self.bailian_stt_model = os.getenv("BAILIAN_STT_MODEL", "paraformer-realtime")
        self.bailian_tts_model = os.getenv("BAILIAN_TTS_MODEL", "sambert-realtime")
        
        # 兼容旧的配置
        self.dashscope_api_key = DASHSCOPE_API_KEY if DASHSCOPE_API_KEY is not None else os.getenv("DASHSCOPE_API_KEY", self.bailian_api_key)
        self.stt_service_url = stt_service_url if stt_service_url is not None else os.getenv("STT_SERVICE_URL", "http://localhost:8081")
        self.tts_service_url = tts_service_url if tts_service_url is not None else os.getenv("TTS_SERVICE_URL", "http://localhost:8082")
        self.agent_service_url = agent_service_url if agent_service_url is not None else os.getenv("AGENT_SERVICE_URL", "http://localhost:8083")