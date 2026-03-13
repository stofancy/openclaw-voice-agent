import sys
import os
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from wsl2.agent_gateway import AgentGateway
from dependency_injector import containers, providers

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestContainer(containers.DeclarativeContainer):
    """测试专用的依赖注入容器"""
    
    config = providers.Configuration()
    
    # Mock STT 客户端 - 使用 MagicMock 支持更多操作
    stt_client = providers.Singleton(MagicMock)
    
    # Mock TTS 客户端 - 使用 MagicMock 支持更多操作
    tts_client = providers.Singleton(MagicMock)
    
    # Mock WebSocket 客户端工厂
    websocket_client = providers.Factory(Mock)
    
    # Mock handlers - 使用 Singleton 确保同一个实例
    stt_handler = providers.Singleton(Mock)
    tts_handler = providers.Singleton(Mock)
    agent_handler = providers.Singleton(Mock)
    websocket_handler = providers.Singleton(Mock)


@pytest.fixture
def gateway():
    """Create a real AgentGateway instance with mocked dependencies for testing"""
    # Create test container with all mocks
    container = TestContainer()
    
    # Configure the handler instances that will be used by the gateway
    stt_handler_mock = container.stt_handler()
    tts_handler_mock = container.tts_handler()
    agent_handler_mock = container.agent_handler()
    
    # Configure handler methods to return reasonable values
    stt_handler_mock.process_increment = Mock(side_effect=lambda x: x)
    stt_handler_mock.process_final = Mock(side_effect=lambda x: x)
    # Preprocess text: convert Chinese periods to English periods for sentence splitting
    tts_handler_mock.preprocess_text = Mock(side_effect=lambda x: x.replace('。', '.') if x else None)
    agent_handler_mock.preprocess_message = Mock(side_effect=lambda x: x if x else None)
    agent_handler_mock.process_response = Mock(side_effect=lambda x: x if x else None)
    
    # Configure STT client mock
    stt_client_mock = container.stt_client()
    stt_client_mock.stop = Mock()
    
    # Configure TTS client mock with all necessary methods
    tts_client_mock = container.tts_client()
    tts_client_mock.connect = Mock()
    tts_client_mock.update_session = Mock()
    tts_client_mock.append_text = Mock()
    tts_client_mock.finish = Mock()
    
    # Create gateway with test container
    gateway = AgentGateway(container=container)
    
    # Override any remaining attributes that tests expect
    gateway.clients = set()
    
    return gateway


@pytest.fixture
def gateway_module():
    """Provide access to the agent_gateway module for testing module-level functions"""
    import wsl2.agent_gateway as gateway_mod
    return gateway_mod


@pytest.fixture(autouse=True)
def cleanup_event_loop():
    """清理事件循环，防止污染"""
    try:
        # 检查当前是否有事件循环
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，不要尝试清理
            yield
            return
    except RuntimeError:
        # 没有事件循环，直接返回
        yield
        return
    
    # 有事件循环但未运行，进行清理
    yield
    
    # 清理所有待处理的任务
    try:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        # 运行一次事件循环以完成取消操作
        if not loop.is_closed():
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except (RuntimeError, ValueError):
        # 如果事件循环已经关闭或出现问题，忽略错误
        pass