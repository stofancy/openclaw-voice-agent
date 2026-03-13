"""
Configuration module for Voice Gateway.
"""
import os
from typing import Optional

class Config:
    """Application configuration."""
    
    def __init__(self, host=None, port=None, debug=None, stt_service_url=None, 
                 tts_service_url=None, agent_service_url=None,
                 WS_HOST=None, WS_PORT=None, DASHSCOPE_API_KEY=None):
        # Handle both new-style and old-style parameter names
        self.debug = debug if debug is not None else os.getenv("DEBUG", "false").lower() == "true"
        self.host = host if host is not None else WS_HOST if WS_HOST is not None else os.getenv("HOST", "0.0.0.0")
        self.port = port if port is not None else WS_PORT if WS_PORT is not None else int(os.getenv("PORT", "8080"))
        self.stt_service_url = stt_service_url if stt_service_url is not None else os.getenv("STT_SERVICE_URL", "http://localhost:8081")
        self.tts_service_url = tts_service_url if tts_service_url is not None else os.getenv("TTS_SERVICE_URL", "http://localhost:8082")
        self.agent_service_url = agent_service_url if agent_service_url is not None else os.getenv("AGENT_SERVICE_URL", "http://localhost:8083")
        self.dashscope_api_key = DASHSCOPE_API_KEY if DASHSCOPE_API_KEY is not None else os.getenv("DASHSCOPE_API_KEY", "")