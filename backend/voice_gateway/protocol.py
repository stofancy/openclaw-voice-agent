"""
Protocol definitions for Voice Gateway.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class AudioRequest:
    """Audio processing request."""
    audio_data: bytes
    content_type: str
    language: str = "en-US"
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class STTResponse:
    """Speech-to-Text response."""
    text: str
    confidence: float
    language: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class TTSRequest:
    """Text-to-Speech request."""
    text: str
    voice: str = "default"
    language: str = "en-US"
    speed: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class TTSResponse:
    """Text-to-Speech response."""
    audio_data: bytes
    content_type: str
    metadata: Optional[Dict[str, Any]] = None