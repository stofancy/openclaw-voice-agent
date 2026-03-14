# 测试架构重构方案

**项目**: audio-proxy  
**版本**: v1.0  
**日期**: 2026-03-14  
**作者**: Claude (子代理)

---

## 1. 目标目录结构

```
audio-proxy/
├── backend/                    # 后端代码
│   └── voice_gateway/
│       ├── __init__.py
│       ├── config.py
│       ├── webrtc_server.py
│       ├── stt_service.py
│       ├── tts_service.py
│       └── agent_client.py
├── frontend/                   # 前端代码
│   └── src/
│       ├── hooks/
│       │   ├── useWebRTC.ts
│       │   ├── useWebSocket.ts
│       │   └── useVAD.ts
│       └── components/
├── test/                       # 测试目录（重构后）
│   ├── conftest.py             # 共享 fixtures
│   ├── pytest.ini              # pytest 配置
│   ├── unit/                   # 单元测试（<1秒）
│   │   ├── __init__.py
│   │   ├── test_config.py      # 配置单元测试
│   │   ├── test_stt_service.py # STT 服务 mock 测试
│   │   ├── test_tts_service.py # TTS 服务 mock 测试
│   │   └── test_message_handler.py # 消息处理单元测试
│   ├── integration/            # 集成测试（<10秒）
│   │   ├── __init__.py
│   │   ├── conftest.py         # 集成测试 fixtures
│   │   ├── test_websocket.py   # WebSocket 集成测试
│   │   ├── test_us01_auto_connect.py
│   │   ├── test_us02_manual_reconnect.py
│   │   ├── test_us04_vad.py
│   │   ├── test_us10_microphone_permission.py
│   │   ├── test_us11_network_disconnect.py
│   │   └── test_us12_ai_service_error.py
│   └── e2e/                    # 端到端测试（<60秒）
│       ├── __init__.py
│       ├── conftest.py         # E2E 测试 fixtures
│       ├── test_us03_recording.py      # 需要浏览器
│       ├── test_us05_audio_echo.py     # 音频回环
│       ├── test_us06_conversation.py   # 对话流程
│       └── test_full_workflow.py       # 完整工作流
├── scripts/                    # 工具脚本
│   └── debug/                  # 调试脚本（从根目录移动）
│       ├── debug_stt_simple.py
│       ├── debug_stt_test.py
│       └── debug_tts_stt_loop.py
├── pytest.ini                  # pytest 配置（根目录）
└── requirements-test.txt       # 测试依赖
```

---

## 2. 文件迁移清单

### 2.1 测试文件迁移

| 源文件 | 目标位置 | 操作 | 说明 |
|--------|---------|------|------|
| `test/test_us01_auto_connect.py` | `test/integration/test_us01_auto_connect.py` | 移动 | 集成测试 |
| `test/test_us02_manual_reconnect.py` | `test/integration/test_us02_manual_reconnect.py` | 移动 | 集成测试 |
| `test/test_us03_recording.py` | `test/e2e/test_us03_recording.py` | 移动 | E2E 测试（需浏览器） |
| `test/test_us04_vad.py` | `test/integration/test_us04_vad.py` | 移动 | 集成测试 |
| `test/test_us10_microphone_permission.py` | `test/integration/test_us10_microphone_permission.py` | 移动 | 集成测试 |
| `test/test_us11_network_disconnect.py` | `test/integration/test_us11_network_disconnect.py` | 移动 | 集成测试 |
| `test/test_us12_ai_service_error.py` | `test/integration/test_us12_ai_service_error.py` | 移动 | 集成测试 |
| `test/integration_test.py` | `test/integration/test_backend_server.py` | 移动+重命名 | 合并重复文件 |
| `integration_test.py` (根目录) | 删除 | 删除 | 与 test/integration_test.py 重复 |
| `test_us05.py` | `test/e2e/test_us05_audio_echo.py` | 移动+重命名 | E2E 测试 |
| `test_us05_e2e.py` | 合并到 `test/e2e/test_us05_audio_echo.py` | 合并 | 内容重复 |
| `test_us06.py` | `test/e2e/test_us06_conversation.py` | 移动+重命名 | E2E 测试 |
| `test_us06_e2e.py` | 合并到 `test/e2e/test_us06_conversation.py` | 合并 | 内容重复 |
| `test/conftest.py` | `test/conftest.py` | 保留 | 共享 fixtures |

### 2.2 调试脚本迁移

| 源文件 | 目标位置 | 操作 | 说明 |
|--------|---------|------|------|
| `debug_stt_simple.py` | `scripts/debug/debug_stt_simple.py` | 移动 | 保留有用脚本 |
| `debug_stt_test.py` | `scripts/debug/debug_stt_test.py` | 移动 | 保留有用脚本 |
| `debug_stt_real_audio.py` | `scripts/debug/debug_stt_real_audio.py` | 移动 | 保留有用脚本 |
| `debug_tts_stt_loop.py` | `scripts/debug/debug_tts_stt_loop.py` | 移动 | 保留有用脚本 |
| `debug_tts_stt_loop_v2.py` | 删除 | 删除 | 版本迭代，保留最新 |
| `debug_tts_stt_loop_v3.py` | `scripts/debug/debug_tts_stt_loop.py` | 移动+覆盖 | 最新版本 |

### 2.3 新增文件

| 文件路径 | 说明 |
|----------|------|
| `test/unit/test_config.py` | 配置单元测试 |
| `test/unit/test_stt_service.py` | STT 服务 mock 测试 |
| `test/unit/test_tts_service.py` | TTS 服务 mock 测试 |
| `test/unit/test_message_handler.py` | 消息处理单元测试 |
| `test/integration/conftest.py` | 集成测试 fixtures（WebSocket 服务器） |
| `test/e2e/conftest.py` | E2E 测试 fixtures（浏览器） |
| `test/fixtures/` | 测试数据（音频文件等） |
| `requirements-test.txt` | 测试依赖 |

---

## 3. pytest 配置

### 3.1 pytest.ini（根目录）

```ini
[tool:pytest]
asyncio_mode = auto
addopts = --tb=short -v

# 测试目录
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 标记定义
markers =
    unit: Unit tests (fast, mocked, <1s)
    integration: Integration tests (needs services, <10s)
    e2e: End-to-end tests (needs browser, <60s)
    slow: Slow tests (>10s)
    websocket: Tests requiring WebSocket server
    browser: Tests requiring browser environment

# 超时配置
timeout = 60
timeout_method = signal

# 忽略目录
norecursedirs = 
    .git
    .venv
    venv
    node_modules
    frontend/node_modules
    scripts/debug

# 覆盖率
addopts = 
    --tb=short
    -v
    --strict-markers
```

### 3.2 运行配置

```bash
# 运行所有测试
pytest test/

# 只运行单元测试
pytest test/unit/ -m unit

# 只运行集成测试
pytest test/integration/ -m integration

# 只运行 E2E 测试
pytest test/e2e/ -m e2e

# 排除慢测试
pytest test/ -m "not slow"

# 排除需要浏览器的测试
pytest test/ -m "not browser"

# 并行运行（需要 pytest-xdist）
pytest test/unit/ -n auto
```

---

## 4. Mock 策略

### 4.1 WebSocket Mock

```python
# test/unit/conftest.py
import pytest
from unittest.mock import Mock, AsyncMock, patch

@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock(return_value='{"type": "ready"}')
    ws.close = AsyncMock()
    return ws

@pytest.fixture
def mock_websocket_server(mock_websocket):
    """Mock WebSocket server."""
    with patch('websockets.serve') as mock_serve:
        mock_serve.return_value = AsyncMock()
        yield mock_serve
```

### 4.2 浏览器 API Mock

```python
# test/e2e/conftest.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_mediarecorder():
    """Mock MediaRecorder API."""
    recorder = Mock()
    recorder.start = Mock()
    recorder.stop = Mock()
    recorder.ondataavailable = None
    recorder.onstop = None
    return recorder

@pytest.fixture
def mock_navigator(mock_mediarecorder):
    """Mock navigator.mediaDevices."""
    with patch('frontend.src.hooks.useRecording.navigator') as mock_nav:
        mock_nav.mediaDevices.getUserMedia = Mock(return_value=Mock())
        mock_nav.mediaDevices.enumerateDevices = Mock(return_value=[])
        yield mock_nav
```

### 4.3 音频数据 Fixture

```python
# test/conftest.py
import pytest
import os

@pytest.fixture
def sample_audio_wav():
    """Load sample WAV audio file."""
    path = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_1sec.wav')
    with open(path, 'rb') as f:
        return f.read()

@pytest.fixture
def sample_audio_pcm():
    """Load sample PCM audio data."""
    path = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_1sec.pcm')
    with open(path, 'rb') as f:
        return f.read()
```

### 4.4 服务 Mock

```python
# test/unit/test_stt_service.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.voice_gateway.stt_service import STTService

@pytest.fixture
def mock_stt_service():
    """Mock STT service."""
    service = Mock(spec=STTService)
    service.transcribe = AsyncMock(return_value="Hello, this is a test")
    return service
```

---

## 5. 实施步骤

### Phase 1: 准备工作（30 分钟）

1. **创建目录结构**
   ```bash
   mkdir -p test/unit test/integration test/e2e test/fixtures scripts/debug
   ```

2. **更新 pytest.ini**
   - 添加 markers 配置
   - 配置超时和忽略目录

3. **创建 requirements-test.txt**
   ```
   pytest>=7.0.0
   pytest-asyncio>=0.21.0
   pytest-timeout>=2.1.0
   pytest-cov>=4.0.0
   pytest-xdist>=3.0.0
   websockets>=11.0
   httpx>=0.24.0
   ```

### Phase 2: 文件迁移（60 分钟）

1. **移动测试文件**
   - 按清单移动文件到对应目录
   - 更新导入路径

2. **合并重复文件**
   - 合并 test_us05.py 和 test_us05_e2e.py
   - 合并 test_us06.py 和 test_us06_e2e.py
   - 删除根目录 integration_test.py

3. **移动调试脚本**
   - 移动 debug_*.py 到 scripts/debug/
   - 删除重复版本（v2, v3）

### Phase 3: 添加标记（30 分钟）

1. **标记单元测试**
   ```python
   @pytest.mark.unit
   def test_config_loading():
       ...
   ```

2. **标记集成测试**
   ```python
   @pytest.mark.integration
   @pytest.mark.websocket
   async def test_websocket_connection():
       ...
   ```

3. **标记 E2E 测试**
   ```python
   @pytest.mark.e2e
   @pytest.mark.browser
   async def test_recording():
       ...
   ```

### Phase 4: 创建 Mock 和 Fixtures（60 分钟）

1. **创建 test/unit/conftest.py**
   - WebSocket mock
   - 服务 mock

2. **创建 test/integration/conftest.py**
   - WebSocket 服务器 fixture
   - 随机端口分配

3. **创建 test/e2e/conftest.py**
   - 浏览器 API mock
   - 音频数据 fixture

### Phase 5: 补充单元测试（90 分钟）

1. **创建 test/unit/test_config.py**
   - 配置加载测试
   - 环境变量测试

2. **创建 test/unit/test_stt_service.py**
   - STT 服务 mock 测试
   - 错误处理测试

3. **创建 test/unit/test_tts_service.py**
   - TTS 服务 mock 测试

4. **创建 test/unit/test_message_handler.py**
   - 消息处理单元测试

### Phase 6: 验证和优化（30 分钟）

1. **运行所有测试**
   ```bash
   pytest test/ -v
   ```

2. **验证分类**
   ```bash
   pytest test/unit/ -m unit
   pytest test/integration/ -m integration
   pytest test/e2e/ -m e2e
   ```

3. **检查运行时间**
   - 单元测试 < 1 秒
   - 集成测试 < 10 秒
   - E2E 测试 < 60 秒

---

## 6. 风险评估

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| 文件移动导致导入错误 | 高 | 中 | 使用 IDE 重构工具，批量更新导入路径 |
| 合并文件丢失测试用例 | 中 | 中 | 合并前对比文件内容，确保无遗漏 |
| 标记遗漏导致分类错误 | 低 | 中 | 代码审查时重点检查标记 |
| Mock 不完善导致测试失败 | 中 | 高 | 先实现核心 mock，逐步完善 |
| 运行时间未达标 | 低 | 中 | 使用 pytest-timeout 强制超时 |
| 向后兼容性问题 | 低 | 低 | 保留根目录 pytest.ini，支持旧路径 |

---

## 7. 预计工时

| 步骤 | 预计时间 | 实际时间 |
|------|---------|----------|
| Phase 1: 准备工作 | 30 分钟 | - |
| Phase 2: 文件迁移 | 60 分钟 | - |
| Phase 3: 添加标记 | 30 分钟 | - |
| Phase 4: Mock 和 Fixtures | 60 分钟 | - |
| Phase 5: 补充单元测试 | 90 分钟 | - |
| Phase 6: 验证和优化 | 30 分钟 | - |
| **总计** | **5 小时** | - |

---

## 8. 向后兼容性

### 8.1 保留的支持

- 根目录 `pytest.ini` 保留，支持 `pytest test/` 运行所有测试
- 原有测试路径继续有效（通过软链接或兼容层）

### 8.2 迁移指南

```bash
# 旧方式（仍然支持）
pytest test/test_us01_auto_connect.py

# 新方式（推荐）
pytest test/integration/test_us01_auto_connect.py -m integration
```

---

## 9. 验收标准

- [ ] 所有文件按清单迁移完成
- [ ] 无恒真 assertion
- [ ] 所有测试有正确的 pytest.mark
- [ ] 单元测试运行时间 < 1 秒
- [ ] 集成测试运行时间 < 10 秒
- [ ] E2E 测试运行时间 < 60 秒
- [ ] 可按标记独立运行测试类别
- [ ] 代码覆盖率 > 80%

---

*方案设计完成，等待 Architect review。*
