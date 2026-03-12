# AI Voice Agent 测试框架文档

---

## 📊 测试框架概览

### 后端测试框架

| 框架 | 用途 | 用例数 |
|------|------|--------|
| **asyncio + websockets** | E2E 测试 | 15 用例 |
| **asyncio + dashscope** | STT API 测试 | 3 用例 |
| **原生 Python** | 网关单元测试 | 30 用例 |
| **原生 Python** | 音量静音测试 | 12 用例 |
| **总计** | - | **60 用例** |

### 前端测试框架

| 框架 | 用途 | 用例数 | 状态 |
|------|------|--------|------|
| **Selenium** | UI 自动化 | 6 用例 | ⚠️ 需安装 |
| **原生 JS** | 单元测试 | 待实现 | ❌ |

---

## 🧪 测试文件说明

### 后端测试

| 文件 | 描述 | 运行命令 |
|------|------|----------|
| `test_e2e.py` | 端到端测试 (15 用例) | `python3 tests/test_e2e.py` |
| `test_stt.py` | STT API 测试 (3 用例) | `python3 tests/test_stt.py` |
| `test_gateway_unit.py` | 网关单元测试 (30 用例) | `python3 tests/test_gateway_unit.py` |
| `test_volume_mute.py` | 音量静音测试 (12 用例) | `python3 tests/test_volume_mute.py` |
| `test_frontend.py` | 前端功能测试 (6 用例) | `python3 tests/test_frontend.py` |
| `test_all.py` | 运行所有测试 | `python3 tests/test_all.py` |

### 前端测试

| 文件 | 描述 | 运行命令 |
|------|------|----------|
| `test_frontend.py` | Selenium UI 测试 | `pip install selenium && python3 tests/test_frontend.py` |

---

## 📋 运行测试

### 运行 Build 脚本 (推荐)

```bash
cd ~/workspaces/audio-proxy
./build.sh
```

**要求**:
- ✅ 100% 测试通过
- ✅ 80%+ 代码覆盖率

### 运行单个测试

```bash
# E2E 测试
source venv/bin/activate
python3 tests/test_e2e.py

# 网关单元测试
python3 tests/test_gateway_unit.py

# 所有测试
python3 tests/test_all.py
```

### 运行覆盖率测试

```bash
source venv/bin/activate
cd wsl2
coverage run --source=. -m pytest
coverage report -m
coverage html -d ../htmlcov
```

查看 HTML 报告：
```bash
firefox ../htmlcov/index.html
```

---

## 📊 测试覆盖率

### 当前覆盖率

| 模块 | 覆盖率 | 状态 |
|------|--------|------|
| **agent_gateway.py** | ~70% | ⚠️ 待提高 |
| **voice-gateway.js** | ~50% | ❌ 需前端测试 |
| **pro-call.html** | ~40% | ❌ 需前端测试 |
| **总计** | ~60% | ⚠️ 目标 80% |

### 覆盖率目标

| 时间 | 目标 |
|------|------|
| **短期** | 70% |
| **中期** | 80% |
| **长期** | 90% |

---

## 🔧 CI/CD 集成

### GitHub Actions (待实现)

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.14
      
      - name: Install dependencies
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
          pip install coverage pytest pytest-cov
      
      - name: Run tests
        run: |
          ./build.sh
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 📈 测试统计

### 测试用例分布

```
后端测试: 60 用例
├── E2E 测试：15 用例
├── STT API: 3 用例
├── 网关单元：30 用例
└── 音量静音：12 用例

前端测试：6 用例
└── UI 自动化：6 用例

总计：66 用例
```

### 测试通过率

| 测试套件 | 通过率 | 目标 |
|---------|--------|------|
| E2E 测试 | 100% | 100% ✅ |
| STT API | 67% | 80% ⚠️ |
| 网关单元 | 100% | 100% ✅ |
| 音量静音 | 待运行 | 100% |
| 前端 UI | 待运行 | 100% |

---

## 🎯 测试策略

### 测试金字塔

```
        /\
       /  \
      / E2E \      15 用例 (23%)
     /________\
    /  单元   \    42 用例 (64%)
   /__________\
  /   集成     \  9 用例 (13%)
 /______________\
```

### 测试原则

1. **测试驱动开发** - 先写测试，再写代码
2. **100% 核心功能覆盖** - 关键功能必须有测试
3. **自动化优先** - 能自动化的尽量自动化
4. **快速反馈** - 测试运行时间 < 5 分钟
5. **持续集成** - 每次提交都运行测试

---

## 📝 最佳实践

### 编写测试

```python
def test_example():
    """测试函数命名规范"""
    # 1. 准备数据
    expected = "hello"
    
    # 2. 执行操作
    result = some_function()
    
    # 3. 断言结果
    assert result == expected, f"期望 {expected}, 实际 {result}"
```

### 测试命名

- ✅ `test_vad_threshold()` - 测试 VAD 阈值
- ✅ `test_tts_playing_flag()` - 测试 TTS 播放标志
- ❌ `test1()`, `test_abc()` - 无意义命名

### 断言消息

```python
# ✅ 好的断言
test("VAD 阈值=0.2", gateway.vad_threshold == 0.2, f"实际值：{gateway.vad_threshold}")

# ❌ 不好的断言
assert gateway.vad_threshold == 0.2
```

---

## 🔍 调试测试

### 查看详细输出

```bash
# 详细模式
python3 -m pytest tests/ -v

# 只运行失败的测试
python3 -m pytest tests/ --last-failed

# 停止在第一个失败
python3 -m pytest tests/ -x
```

### 覆盖率分析

```bash
# 生成 HTML 报告
coverage html -d htmlcov

# 在浏览器中查看
firefox htmlcov/index.html
```

---

_最后更新：2026-03-12 13:00_
