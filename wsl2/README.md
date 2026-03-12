# WSL2 模块架构说明

## 📦 新架构（2026-03-13）

### 核心组件

```
wsl2/
├── container.py          # 依赖注入容器（核心）
├── handlers/             # 业务逻辑层
│   ├── __init__.py
│   ├── stt_handler.py    # STT 业务处理
│   ├── tts_handler.py    # TTS 业务处理
│   ├── agent_handler.py  # Agent 调用处理
│   └── websocket_handler.py  # WebSocket 消息路由
├── agent-gateway.py      # 实时语音网关（主入口）
└── README.md             # 本文件
```

---

## 🔌 依赖注入容器 (container.py)

使用 `dependency-injector` 管理所有外部依赖：

```python
from wsl2.container import Container

# 创建容器
container = Container()

# 获取 handlers
stt_handler = container.stt_handler()
tts_handler = container.tts_handler()
agent_handler = container.agent_handler()
websocket_handler = container.websocket_handler()

# 获取原生客户端（如果需要）
stt_client = container.stt_client()
tts_client = container.tts_client()
```

### 容器配置

```python
container = Container()
container.config.from_dict({
    'stt': {'model': 'paraformer-realtime-v2'},
    'tts': {'model': 'qwen3-tts-instruct-flash-realtime'},
})
```

---

## 🛠️ Handlers 职责

| Handler | 职责 | 可测试性 |
|---------|------|---------|
| `SttHandler` | STT 结果清洗、验证、格式化 | ✅ 可 Mock stt_client |
| `TtsHandler` | TTS 文本预处理、响应处理 | ✅ 可 Mock tts_client |
| `AgentHandler` | Agent 消息预处理、响应处理 | ✅ 可 Mock agent_client |
| `WebSocketHandler` | 消息解析、路由、格式化 | ✅ 无外部依赖 |

### 设计原则

1. **不重复造轮子** - 直接使用 DashScope 和 websockets 原生 API
2. **业务逻辑可测试** - Handlers 不依赖具体 API 实现
3. **依赖注入** - 外部依赖通过容器管理，易于替换和 Mock
4. **代码整洁** - 无硬编码、无废弃代码

---

## 🚀 使用示例

### 在网关中使用

```python
from wsl2.container import Container
from wsl2.agent-gateway import AgentGateway

# 创建容器
container = Container()

# 创建网关（依赖注入）
gateway = AgentGateway(container=container)

# 网关内部自动获取 handlers
# self.stt_handler = container.stt_handler()
# self.tts_handler = container.tts_handler()
# self.agent_handler = container.agent_handler()
```

### 测试 Handlers

```python
import pytest
from unittest.mock import Mock
from wsl2.handlers import SttHandler

def test_stt_handler_process_final():
    # Mock stt_client
    mock_client = Mock()
    
    # 创建 handler
    handler = SttHandler(stt_client=mock_client)
    
    # 测试有效文本
    assert handler.process_final("  你好世界  ") == "你好世界"
    
    # 测试无效文本（太短）
    assert handler.process_final("哦") is None
    
    # 测试空文本
    assert handler.process_final("") is None
```

---

## 📝 迁移指南

### 从旧代码迁移到新架构

#### 旧代码（硬编码）
```python
class AgentGateway:
    def __init__(self):
        self.stt_realtime = Recognition(...)  # 硬编码
        self.tts_realtime = QwenTtsRealtime(...)  # 硬编码
```

#### 新代码（依赖注入）
```python
from wsl2.container import Container

class AgentGateway:
    def __init__(self, container: Container):
        self.stt_handler = container.stt_handler()  # 依赖注入
        self.tts_handler = container.tts_handler()  # 依赖注入
        self.agent_handler = container.agent_handler()  # 依赖注入
```

---

## ✅ 已删除废弃文件

以下文件已在 2026-03-13 重构中删除：

| 文件 | 替代方案 | 删除原因 |
|------|---------|---------|
| `audio-receiver-streaming.py` | agent-gateway.py | 功能已整合 |
| `audio-receiver.py` | agent-gateway.py | 功能已整合 |
| `bailian-gateway.py` | agent-gateway.py | 功能已整合 |
| `bailian-gateway-simple.py` | agent-gateway.py | 功能已整合 |
| `bailian-gateway-verbose.py` | agent-gateway.py | 功能已整合 |
| `bailian_realtime_stt.py` | SttHandler + container | 重复封装 |
| `bailian_stt.py` | SttHandler + container | 重复封装 |
| `test-agent-call.py` | agent-gateway.py | 功能已整合 |
| `interfaces.py` | handlers 模块 | 抽象接口层增加不必要复杂度 |

---

## 🎯 启动网关

```bash
cd ~/workspaces/audio-proxy
python -m wsl2.agent-gateway
```

或：

```bash
cd ~/workspaces/audio-proxy/wsl2
python agent-gateway.py
```

---

*最后更新：2026-03-13 - 阶段 1.5-C 重构完成*
