"""WebSocket 消息路由处理"""

import json
from typing import Any, Callable, Optional


class WebSocketHandler:
    """WebSocket 消息路由处理
    
    职责：
    - 消息解析
    - 消息路由
    - 响应格式化
    - 不包含任何 WebSocket 连接逻辑
    """
    
    def __init__(self):
        """初始化"""
        self.routes = {}
    
    def register_route(self, msg_type: str, handler: Callable) -> None:
        """注册消息路由
        
        Args:
            msg_type: 消息类型
            handler: 处理函数
        """
        self.routes[msg_type] = handler
    
    def parse_message(self, message: Any) -> Optional[dict]:
        """解析 WebSocket 消息
        
        Args:
            message: 原始消息（字符串或字节）
            
        Returns:
            解析后的字典，如果失败则返回 None
        """
        if isinstance(message, bytes):
            return self._parse_binary_message(message)
        
        if isinstance(message, str):
            return self._parse_text_message(message)
        
        return None
    
    def _parse_text_message(self, message: str) -> Optional[dict]:
        """解析文本消息
        
        Args:
            message: 文本消息
            
        Returns:
            解析后的字典
        """
        try:
            data = json.loads(message)
            return data
        except json.JSONDecodeError:
            return None
    
    def _parse_binary_message(self, message: bytes) -> Optional[dict]:
        """解析二进制消息（带 header 的音频数据）
        
        Args:
            message: 二进制消息
            
        Returns:
            包含 header 和 data 的字典
        """
        if len(message) < 4:
            return None
        
        try:
            # 解析 header 长度
            header_len = int.from_bytes(message[:4], 'big')
            
            if header_len > 10000 or header_len > len(message) - 4:
                return None
            
            # 解析 header
            header_json = message[4:4+header_len].decode('utf-8')
            header = json.loads(header_json)
            
            # 提取音频数据
            audio_data = message[4+header_len:]
            
            return {
                'type': 'audio',
                'header': header,
                'data': audio_data,
            }
            
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
    
    def route_message(self, data: dict) -> Optional[Any]:
        """路由消息到对应处理器
        
        Args:
            data: 解析后的消息数据
            
        Returns:
            处理结果
        """
        if not data or 'type' not in data:
            return None
        
        msg_type = data.get('type', 'unknown')
        handler = self.routes.get(msg_type)
        
        if handler:
            return handler(data)
        
        return None
    
    def format_response(self, response_type: str, data: Any) -> str:
        """格式化响应消息
        
        Args:
            response_type: 响应类型
            data: 响应数据
            
        Returns:
            JSON 字符串
        """
        response = {
            'type': response_type,
            **data
        }
        return json.dumps(response, ensure_ascii=False)
    
    def format_error(self, message: str, code: str = "UNKNOWN_ERROR") -> str:
        """格式化错误消息
        
        Args:
            message: 错误信息
            code: 错误代码
            
        Returns:
            JSON 字符串
        """
        return self.format_response('error', {
            'message': message,
            'code': code,
        })
