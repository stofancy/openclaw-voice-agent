"""WebSocket Handler 业务逻辑测试"""

import pytest
import json
from unittest.mock import Mock

from wsl2.handlers.websocket_handler import WebSocketHandler


class TestWebSocketHandlerInitialization:
    """测试 WebSocket Handler 初始化"""
    
    def test_init_success(self):
        """测试初始化成功"""
        handler = WebSocketHandler()
        
        assert handler is not None
        assert hasattr(handler, 'routes')
        assert isinstance(handler.routes, dict)
        assert len(handler.routes) == 0


class TestRegisterRoute:
    """测试路由注册"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = WebSocketHandler()
    
    def test_register_route_success(self):
        """测试成功注册路由"""
        mock_handler = Mock()
        self.handler.register_route('test_type', mock_handler)
        
        assert 'test_type' in self.handler.routes
        assert self.handler.routes['test_type'] == mock_handler
    
    def test_register_multiple_routes(self):
        """测试注册多个路由"""
        handler1 = Mock()
        handler2 = Mock()
        
        self.handler.register_route('type1', handler1)
        self.handler.register_route('type2', handler2)
        
        assert len(self.handler.routes) == 2
        assert self.handler.routes['type1'] == handler1
        assert self.handler.routes['type2'] == handler2
    
    def test_register_overwrite_route(self):
        """测试覆盖已有路由"""
        handler1 = Mock()
        handler2 = Mock()
        
        self.handler.register_route('test', handler1)
        self.handler.register_route('test', handler2)
        
        assert self.handler.routes['test'] == handler2


class TestParseTextMessage:
    """测试文本消息解析"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = WebSocketHandler()
    
    def test_parse_valid_json(self):
        """测试解析有效 JSON"""
        message = json.dumps({'type': 'test', 'data': 'value'})
        result = self.handler.parse_message(message)
        
        assert result is not None
        assert result['type'] == 'test'
        assert result['data'] == 'value'
    
    def test_parse_invalid_json(self):
        """测试解析无效 JSON"""
        message = "not valid json"
        result = self.handler.parse_message(message)
        
        assert result is None
    
    def test_parse_empty_string(self):
        """测试解析空字符串"""
        result = self.handler.parse_message("")
        
        assert result is None
    
    def test_parse_empty_json_object(self):
        """测试解析空 JSON 对象"""
        message = json.dumps({})
        result = self.handler.parse_message(message)
        
        assert result is not None
        assert result == {}
    
    def test_parse_unicode_json(self):
        """测试解析 Unicode JSON"""
        message = json.dumps({'type': 'test', 'message': '你好世界'}, ensure_ascii=False)
        result = self.handler.parse_message(message)
        
        assert result is not None
        assert result['message'] == '你好世界'


class TestParseBinaryMessage:
    """测试二进制消息解析"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = WebSocketHandler()
    
    def test_parse_valid_binary_message(self):
        """测试解析有效的二进制消息"""
        # 构造：4 字节 header 长度 + header JSON + 音频数据
        header = {'type': 'audio', 'format': 'pcm'}
        header_json = json.dumps(header).encode('utf-8')
        header_len = len(header_json)
        audio_data = b'\x00\x01\x02\x03'
        
        message = header_len.to_bytes(4, 'big') + header_json + audio_data
        result = self.handler.parse_message(message)
        
        assert result is not None
        assert result['type'] == 'audio'
        assert result['header'] == header
        assert result['data'] == audio_data
    
    def test_parse_binary_too_short(self):
        """测试解析过短的二进制消息"""
        message = b'\x00\x01\x02'  # 少于 4 字节
        result = self.handler.parse_message(message)
        
        assert result is None
    
    def test_parse_binary_invalid_header_len(self):
        """测试解析无效 header 长度的二进制消息"""
        # header 长度超过消息总长度
        header_len = 1000
        message = header_len.to_bytes(4, 'big') + b'\x00\x01'
        result = self.handler.parse_message(message)
        
        assert result is None
    
    def test_parse_binary_invalid_json(self):
        """测试解析无效 JSON header 的二进制消息"""
        header_len = 5
        message = header_len.to_bytes(4, 'big') + b'invalid' + b'\x00\x01'
        result = self.handler.parse_message(message)
        
        assert result is None
    
    def test_parse_binary_invalid_utf8(self):
        """测试解析无效 UTF-8 的二进制消息"""
        header_len = 5
        message = header_len.to_bytes(4, 'big') + b'\xff\xfe\xfd\xfc\xfb' + b'\x00\x01'
        result = self.handler.parse_message(message)
        
        assert result is None


class TestRouteMessage:
    """测试消息路由"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = WebSocketHandler()
    
    def test_route_to_registered_handler(self):
        """测试路由到已注册的处理器"""
        mock_handler = Mock(return_value='result')
        self.handler.register_route('test_type', mock_handler)
        
        data = {'type': 'test_type', 'data': 'value'}
        result = self.handler.route_message(data)
        
        assert result == 'result'
        mock_handler.assert_called_once_with(data)
    
    def test_route_no_handler(self):
        """测试路由到不存在的处理器"""
        data = {'type': 'unknown_type'}
        result = self.handler.route_message(data)
        
        assert result is None
    
    def test_route_missing_type(self):
        """测试路由缺少 type 字段的消息"""
        data = {'data': 'value'}
        result = self.handler.route_message(data)
        
        assert result is None
    
    def test_route_empty_data(self):
        """测试路由空数据"""
        result = self.handler.route_message({})
        
        assert result is None
    
    def test_route_none_data(self):
        """测试路由 None 数据"""
        result = self.handler.route_message(None)
        
        assert result is None


class TestFormatResponse:
    """测试响应格式化"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = WebSocketHandler()
    
    def test_format_simple_response(self):
        """测试格式化简单响应"""
        result = self.handler.format_response('success', {'message': 'ok'})
        
        parsed = json.loads(result)
        assert parsed['type'] == 'success'
        assert parsed['message'] == 'ok'
    
    def test_format_response_with_multiple_fields(self):
        """测试格式化多字段响应"""
        result = self.handler.format_response('data', {
            'id': 123,
            'value': 'test',
            'flag': True
        })
        
        parsed = json.loads(result)
        assert parsed['type'] == 'data'
        assert parsed['id'] == 123
        assert parsed['value'] == 'test'
        assert parsed['flag'] is True
    
    def test_format_response_with_unicode(self):
        """测试格式化 Unicode 响应"""
        result = self.handler.format_response('message', {'text': '你好世界'})
        
        parsed = json.loads(result)
        assert parsed['text'] == '你好世界'
    
    def test_format_response_empty_data(self):
        """测试格式化空数据响应"""
        result = self.handler.format_response('empty', {})
        
        parsed = json.loads(result)
        assert parsed['type'] == 'empty'


class TestFormatError:
    """测试错误格式化"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = WebSocketHandler()
    
    def test_format_error_default_code(self):
        """测试格式化默认错误代码"""
        result = self.handler.format_error('Something went wrong')
        
        parsed = json.loads(result)
        assert parsed['type'] == 'error'
        assert parsed['message'] == 'Something went wrong'
        assert parsed['code'] == 'UNKNOWN_ERROR'
    
    def test_format_error_custom_code(self):
        """测试格式化自定义错误代码"""
        result = self.handler.format_error('Invalid input', 'INVALID_INPUT')
        
        parsed = json.loads(result)
        assert parsed['type'] == 'error'
        assert parsed['message'] == 'Invalid input'
        assert parsed['code'] == 'INVALID_INPUT'
    
    def test_format_error_unicode_message(self):
        """测试格式化 Unicode 错误消息"""
        result = self.handler.format_error('发生错误')
        
        parsed = json.loads(result)
        assert parsed['message'] == '发生错误'


class TestEdgeCases:
    """测试边界情况"""
    
    def setup_method(self):
        """每个测试前的准备"""
        self.handler = WebSocketHandler()
    
    def test_parse_message_bytes_type(self):
        """测试解析 bytes 类型的非二进制消息"""
        # 不是有效的二进制格式
        message = b'not a valid format'
        result = self.handler.parse_message(message)
        
        assert result is None
    
    def test_parse_message_unknown_type(self):
        """测试解析未知类型的消息"""
        message = 12345  # 不是 str 或 bytes
        result = self.handler.parse_message(message)
        
        assert result is None
    
    def test_route_message_handler_exception(self):
        """测试路由时处理器抛出异常"""
        def raising_handler(data):
            raise ValueError("Test error")
        
        self.handler.register_route('test', raising_handler)
        
        with pytest.raises(ValueError):
            self.handler.route_message({'type': 'test'})
    
    def test_format_response_nested_data(self):
        """测试格式化嵌套数据响应"""
        result = self.handler.format_response('nested', {
            'outer': {
                'inner': {
                    'value': 'deep'
                }
            }
        })
        
        parsed = json.loads(result)
        assert parsed['outer']['inner']['value'] == 'deep'
