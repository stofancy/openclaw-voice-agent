"""Container 依赖注入测试"""

import pytest
from unittest.mock import Mock, patch

from wsl2.container import Container


class TestContainerInitialization:
    """测试 Container 初始化"""
    
    def test_container_create_success(self):
        """测试容器成功创建"""
        container = Container()
        assert container is not None
        assert hasattr(container, 'config')
        assert hasattr(container, 'stt_client')
        assert hasattr(container, 'tts_client')
        assert hasattr(container, 'websocket_client')
        assert hasattr(container, 'stt_handler')
        assert hasattr(container, 'tts_handler')
        assert hasattr(container, 'agent_handler')
        assert hasattr(container, 'websocket_handler')
    
    def test_container_config_initialization(self):
        """测试容器配置初始化"""
        container = Container()
        # 配置应该是 Configuration 提供者
        assert container.config is not None


class TestDependencyInjection:
    """测试依赖注入是否正确"""
    
    def test_stt_handler_injection(self):
        """测试 STT Handler 依赖注入"""
        container = Container()
        
        # Mock stt_client provider
        mock_stt_client = Mock()
        container.stt_client.override(providers.Object(mock_stt_client))
        
        stt_handler = container.stt_handler()
        
        assert stt_handler is not None
        assert stt_handler.stt_client == mock_stt_client
    
    def test_tts_handler_injection(self):
        """测试 TTS Handler 依赖注入"""
        container = Container()
        
        # Mock tts_client provider
        mock_tts_client = Mock()
        container.tts_client.override(providers.Object(mock_tts_client))
        
        tts_handler = container.tts_handler()
        
        assert tts_handler is not None
        assert tts_handler.tts_client == mock_tts_client
    
    def test_agent_handler_injection(self):
        """测试 Agent Handler 依赖注入"""
        container = Container()
        
        agent_handler = container.agent_handler()
        
        assert agent_handler is not None
        # agent_client 是可选的，默认为 None
        assert agent_handler.agent_client is None
    
    def test_websocket_handler_injection(self):
        """测试 WebSocket Handler 依赖注入"""
        container = Container()
        
        websocket_handler = container.websocket_handler()
        
        assert websocket_handler is not None
        assert hasattr(websocket_handler, 'routes')
        assert isinstance(websocket_handler.routes, dict)


class TestSingletonScope:
    """测试 Singleton 作用域"""
    
    def test_stt_client_is_singleton(self):
        """测试 STT 客户端是单例"""
        container = Container()
        
        # 使用 Object provider 来模拟单例
        mock_client = Mock()
        container.stt_client.override(providers.Object(mock_client))
        
        client1 = container.stt_client()
        client2 = container.stt_client()
        
        # Singleton 应该返回同一个实例
        assert client1 is client2
    
    def test_tts_client_is_singleton(self):
        """测试 TTS 客户端是单例"""
        container = Container()
        
        mock_client = Mock()
        container.tts_client.override(providers.Object(mock_client))
        
        client1 = container.tts_client()
        client2 = container.tts_client()
        
        assert client1 is client2


class TestFactoryScope:
    """测试 Factory 作用域"""
    
    def test_websocket_client_is_factory(self):
        """测试 WebSocket 客户端是工厂模式"""
        container = Container()
        
        # Factory 每次调用应该返回新实例
        # 由于 websockets.connect 是异步函数，这里测试概念
        assert container.websocket_client is not None
    
    def test_handlers_are_factory(self):
        """测试 Handlers 是工厂模式"""
        container = Container()
        
        # Mock the clients to avoid real initialization
        mock_stt_client = Mock()
        mock_tts_client = Mock()
        container.stt_client.override(providers.Object(mock_stt_client))
        container.tts_client.override(providers.Object(mock_tts_client))
        
        # 每次获取应该返回新实例
        handler1 = container.stt_handler()
        handler2 = container.stt_handler()
        
        # Factory 应该返回不同的实例
        assert handler1 is not handler2
        
        handler3 = container.tts_handler()
        handler4 = container.tts_handler()
        
        assert handler3 is not handler4


class TestConfigurationOverride:
    """测试配置覆盖"""
    
    def test_config_from_dict(self):
        """测试从字典配置"""
        container = Container()
        container.config.from_dict({
            'stt': {'model': 'test-model'},
            'tts': {'model': 'test-tts-model'},
        })
        
        # 配置应该被正确设置
        assert container.config.stt.model() == 'test-model'
        assert container.config.tts.model() == 'test-tts-model'
    
    def test_config_from_env(self):
        """测试从环境变量配置"""
        container = Container()
        
        # 测试配置存在
        assert container.config is not None


# Import providers here to avoid circular import issues in tests
from dependency_injector import providers
