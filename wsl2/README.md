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
└── interfaces.py         # ⚠️ 已废弃
```

### 依赖注入容器 (container.py)

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

### Handlers 职责

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
4. **代码整洁** - 废弃代码明确标记，避免混淆

---

## ⚠️ 已废弃文件

| 文件 | 替代方案 | 废弃原因 |
|------|---------|---------|
| `interfaces.py` | handlers 模块 | 抽象接口层增加不必要复杂度 |
| `bailian_stt.py` | SttHandler + container | 重复封装 DashScope API |
| `bailian_realtime_stt.py` | SttHandler + container | 重复封装 DashScope API |

---

## 🚀 使用示例

### 在新网关中使用

```python
from wsl2.container import Container

class NewGateway:
    def __init__(self):
        self.container = Container()
        self.stt_handler = self.container.stt_handler()
        self.tts_handler = self.container.tts_handler()
        self.ws_handler = self.container.websocket_handler()
    
    async def handle_audio(self, audio_data):
        # 使用原生 API
        stt_client = self.container.stt_client()
        # ... 处理逻辑
        
        # 使用业务 handler
        result = self.stt_handler.process_final(text)
        # ... 处理逻辑
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

#### 旧代码
```python
from bailian_stt import BaiLianSTT

stt = BaiLianSTT(api_key="xxx")
text = stt.recognize(audio_path)
```

#### 新代码
```python
from wsl2.container import Container

container = Container()
stt_handler = container.stt_handler()

# 业务逻辑（文本处理）
cleaned_text = stt_handler.process_final(raw_text)

# 原生 API 调用（通过容器获取）
stt_client = container.stt_client()
# ... 使用 stt_client 调用 API
```

---

*最后更新：2026-03-13*
