# Audio Proxy 实施总结

**项目**: 为 OpenClaw Agent 实现语音聊天级别的音频输入输出能力

**创建时间**: 2026-03-11

---

## 📋 需求确认

| 维度 | 要求 | 状态 |
|------|------|------|
| **延迟** | < 300ms (语音聊天级别) | ⚠️ 待实测 |
| **部署** | WSL2 + Windows 主机 | ✅ 已设计 |
| **对话模式** | 半双工 (先做) | ✅ 已实现 |
| **供应商** | Minimax (优先) / 阿里 (备选) | ✅ 已集成 |
| **使用场景** | 音视频聊天 → 智能家居 → 机器人 | ✅ 路线图 |

---

## 🏗️ 架构设计

### 方案 A (已实现): Windows 代理采集

```
┌─────────────────────────────────────────────────────────┐
│  Windows 10/11 (主机)                                    │
│  ┌─────────────────────────────────────────────────┐    │
│  │  audio-capture.py                                │    │
│  │  - 麦克风采集 (32ms 分片)                         │    │
│  │  - Silero VAD 语音检测                           │    │
│  │  - WebSocket 推送到 WSL2 (端口 8765)              │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────┘
                       │ WebSocket (20-50ms)
                       ▼
┌─────────────────────────────────────────────────────────┐
│  WSL2 (OpenClaw Agent)                                   │
│  ┌─────────────────────────────────────────────────┐    │
│  │  audio-receiver-streaming.py                     │    │
│  │  - 接收音频流                                    │    │
│  │  - 调用 Minimax API (STT+LLM+TTS)                │    │
│  │  - ffplay 播放 TTS 响应 (最小缓冲)                 │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 延迟预算

| 环节 | 目标 | 优化技巧 |
|------|------|----------|
| Windows 采集 → VAD | 10-20ms | 16-32ms 分片 |
| WebSocket 传输 | 10-30ms | 本地网络 |
| WSL2 → 云端 STT | 50-100ms | 流式 API |
| 云端 STT+LLM+TTS | 100-200ms | 并行处理 |
| TTS 播放缓冲 | 30-50ms | 首包即播 |
| **总计** | **200-400ms** | ⚠️ 可能略超 300ms |

---

## ✅ 已完成工作

### 1. 项目结构

```
~/workspaces/audio-proxy/
├── .env                              # 环境配置 (待填写 API Key)
├── README.md                         # 项目说明
├── CONFIG.md                         # API Key 配置指南
├── IMPLEMENTATION.md                 # 详细实施计划
├── docs/
│   ├── MINIMAX_STREAMING_API.md      # Minimax 流式 API 文档
│   ├── ALI_DASHSCOPE_STREAMING_API.md # 阿里 DashScope 文档
│   └── IMPLEMENTATION_SUMMARY.md     # 本文档
├── windows/
│   ├── audio-capture.py              # Windows 采集脚本
│   └── requirements.txt              # Python 依赖
└── wsl2/
    ├── audio-receiver.py             # 基础接收脚本
    ├── audio-receiver-streaming.py   # 优化流式接收脚本
    └── requirements.txt              # Python 依赖
```

### 2. 核心代码

| 文件 | 功能 | 状态 |
|------|------|------|
| `windows/audio-capture.py` | 麦克风采集 + VAD + WebSocket | ✅ 完成 |
| `wsl2/audio-receiver.py` | 基础接收 + 批量 API 调用 | ✅ 完成 |
| `wsl2/audio-receiver-streaming.py` | 优化流式 + 延迟统计 | ✅ 完成 |

### 3. API 文档

| 文档 | 内容 | 状态 |
|------|------|------|
| `MINIMAX_STREAMING_API.md` | Minimax 流式 STT/LLM/TTS | ✅ 完成 |
| `ALI_DASHSCOPE_STREAMING_API.md` | 阿里 DashScope 流式 API | ✅ 完成 |

### 4. 配置文件

| 文件 | 说明 | 状态 |
|------|------|------|
| `.env` | 环境变量配置 | ✅ 完成 (待填写 Key) |
| `windows/requirements.txt` | Windows 依赖 | ✅ 完成 |
| `wsl2/requirements.txt` | WSL2 依赖 | ✅ 完成 |

---

## 📝 待办事项

### Phase 1: 环境准备 (30 分钟)

- [ ] **1.1 获取 Minimax API Key**
  ```
  访问：https://platform.minimaxi.com/
  注册 → 控制台 → API Keys → 创建 Key
  记录：MINIMAX_API_KEY + MINIMAX_GROUP_ID
  ```

- [ ] **1.2 配置 .env 文件**
  ```bash
  cd ~/workspaces/audio-proxy
  nano .env
  # 替换 YOUR_MINIMAX_API_KEY_HERE 为实际 Key
  ```

- [ ] **1.3 安装依赖**
  ```bash
  # WSL2
  cd ~/workspaces/audio-proxy/wsl2
  pip install -r requirements.txt
  
  # Windows (PowerShell)
  cd \path\to\audio-proxy\windows
  pip install -r requirements.txt
  ```

- [ ] **1.4 配置 Windows 防火墙**
  ```powershell
  # PowerShell 管理员
  New-NetFirewallRule -DisplayName "WSL2 Audio" -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow
  ```

---

### Phase 2: API 测试 (15 分钟)

- [ ] **2.1 运行延迟测试**
  ```bash
  cd ~/workspaces/audio-proxy
  python3 test-api-latency.py
  ```

- [ ] **2.2 验证延迟**
  - 目标：< 300ms
  - 如果 > 500ms，考虑优化或切换供应商

---

### Phase 3: 端到端测试 (30 分钟)

- [ ] **3.1 启动 WSL2 接收端**
  ```bash
  cd ~/workspaces/audio-proxy/wsl2
  python3 audio-receiver-streaming.py
  ```

- [ ] **3.2 启动 Windows 采集端** (Windows PowerShell)
  ```powershell
  cd \path\to\audio-proxy\windows
  python audio-capture.py
  ```

- [ ] **3.3 测试语音对话**
  - 对着麦克风说话
  - 观察日志输出
  - 验证 TTS 播放
  - 记录端到端延迟

---

### Phase 4: OpenClaw 集成 (2-3 小时)

- [ ] **4.1 创建 OpenClaw Skill**
  ```
  ~/.openclaw/extensions/audio-skill/
  ├── SKILL.md
  ├── listen.sh
  └── speak.sh
  ```

- [ ] **4.2 集成到 Agent 工作流**
  - Agent 可以调用 `listen()` 获取用户输入
  - Agent 可以调用 `speak(text)` 输出语音

---

## 📊 供应商对比

| 维度 | Minimax | 阿里 DashScope |
|------|---------|---------------|
| **STT 延迟** | 50-100ms ⭐ | 80-150ms |
| **LLM 延迟** | 100-200ms | 100-200ms |
| **TTS 延迟** | 80-150ms ⭐ | 100-180ms |
| **中文质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **成本** | 中等 | 较低 ⭐ |
| **生态整合** | 一般 | 强 ⭐ |
| **推荐场景** | 语音聊天 ⭐ | 智能家居 |

---

## 🚨 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 延迟 > 300ms | 中 | 高 | 使用流式 API + 并行处理 |
| WSL2 音频采集失败 | 低 | 高 | 备选 Windows 代理方案 |
| API Key 余额不足 | 低 | 中 | 先测试免费额度 |
| 网络不稳定 | 中 | 中 | 添加重试机制 |

---

## 📈 下一步优化

### 短期 (1-2 周)

1. **真流式 STT**: WebSocket 实时传输，不等说完
2. **LLM → TTS 管道**: 第一个 token 就开始 TTS
3. **VAD 优化**: 更准确的语音检测

### 中期 (1 月)

1. **全双工支持**: 回声消除 + 打断处理
2. **本地 VAD 模型**: Silero 量化版
3. **多供应商切换**: 自动选择最优 API

### 长期 (3 月+)

1. **视觉集成**: 摄像头 + Gemini 多模态
2. **本地小模型**: 离线基础能力
3. **机器人集成**: GPIO + 执行器

---

## 🔗 相关链接

- **Minimax 平台**: https://platform.minimaxi.com/
- **阿里 DashScope**: https://dashscope.console.aliyun.com/
- **Silero VAD**: https://github.com/snakers4/silero-vad
- **OpenClaw 文档**: https://docs.openclaw.ai

---

## 📞 联系与支持

遇到问题？

1. 查看 `CONFIG.md` 配置指南
2. 查看 API 文档 (`docs/` 目录)
3. 运行 `test-api-latency.py` 诊断
4. 记录问题到 `docs/ISSUES.md`

---

_最后更新：2026-03-11_

**当前状态**: ✅ 代码就绪，待 API Key 配置和实测
