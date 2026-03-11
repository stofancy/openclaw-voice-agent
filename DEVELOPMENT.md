# 开发文档

## 项目架构

```
audio-proxy/
├── sdk/                          # JavaScript SDK
│   └── voice-gateway.js          # 浏览器端 WebSocket SDK
├── wsl2/                         # Python 网关
│   ├── agent-gateway.py          # 主网关代码
│   └── requirements.txt          # Python 依赖
├── test-pages/                   # 测试页面
│   ├── pro-call.html             # 专业通话界面 (推荐)
│   ├── realtime-call.html        # 实时通话测试
│   ├── sdk-demo.html             # SDK 演示
│   └── simple-test.html          # 简单测试
├── docs/                         # 文档
└── logs/                         # 日志目录
```

## 核心流程

### 语音通话流程

```
用户说话
  ↓
浏览器麦克风采集 (PCM 16bit 16kHz)
  ↓
WebSocket 音频流 → 网关
  ↓
网关 VAD 检测 (音量阈值 0.3)
  ↓
检测到说话结束 (静音 1 秒)
  ↓
调用百炼 STT API
  ↓
调用 OpenClaw Agent (travel-agency)
  ↓
调用百炼 TTS API
  ↓
WebSocket 音频流 → 浏览器
  ↓
浏览器播放 TTS 音频
```

### VAD 配置参数

```python
vad_threshold = 0.3        # 音量阈值 (0-1)
silence_duration = 1.0     # 静音判定时间 (秒)
min_speech_duration = 0.5  # 最小语音时长 (秒)
```

## API 协议

### WebSocket 消息格式

**浏览器 → 网关**:

```json
// 连接测试
{ "type": "connect" }

// 音频流开始
{ "type": "audio_stream_start" }

// 音频流结束
{ "type": "audio_stream_stop" }

// 音频数据 (二进制 PCM)
<binary PCM 16bit 16kHz>
```

**网关 → 浏览器**:

```json
// 连接成功
{ "type": "connected", "timestamp": "...", "gateway": "ready" }

// 音量更新
{ "type": "volume", "volume": 0.5, "is_speaking": true }

// 状态更新
{ "type": "status", "status": "recognizing" }

// STT 识别结果
{ "type": "stt_result", "text": "...", "is_final": true }

// Agent 回复
{ "type": "agent_reply", "text": "..." }

// TTS 音频
{ "type": "audio", "data": "<base64 PCM>" }
```

## 开发指南

### 添加新功能

1. 在 `wsl2/agent-gateway.py` 添加网关逻辑
2. 在 `sdk/voice-gateway.js` 添加 SDK 方法
3. 在测试页面添加 UI
4. 编写测试
5. Git 提交

### 调试技巧

**查看实时日志**:

```bash
tail -f ~/workspaces/audio-proxy/logs/agent_gateway_*.log
```

**测试 WebSocket 连接**:

```bash
cd ~/workspaces/audio-proxy
source venv/bin/activate
python3 debug-test.py
```

**浏览器调试**:

打开 `http://localhost:8080/test-pages/pro-call.html`
按 F12 打开开发者工具

### 性能优化

1. **音频 chunk size**: 1024 samples (~64ms @ 16kHz)
2. **VAD 检测**: 简单 RMS 音量检测
3. **WebSocket**: 二进制传输 (减少开销)
4. **TTS**: 流式播放 (边接收边播放)

## 常见问题

### Q: 延迟太高怎么办？

A: 检查以下环节:
1. 网络延迟 (本地应该 < 10ms)
2. STT 识别时间 (百炼约 1-2s)
3. Agent 响应时间 (travel-agency 约 3s)
4. TTS 合成时间 (百炼约 2-3s)

优化方向:
- 使用百炼实时 STT (流式识别)
- 优化 Agent 提示词 (减少响应时间)
- TTS 流式播放

### Q: VAD 检测不准确怎么办？

A: 调整参数:
```python
vad_threshold = 0.3  # 调高更严格，调低更敏感
silence_duration = 1.0  # 调短更快响应
```

### Q: 浏览器无法播放音频？

A: 检查:
1. 音频格式是否正确 (PCM 24kHz 单声道 16bit)
2. AudioContext 是否初始化
3. 浏览器是否支持 Web Audio API

## 测试清单

- [ ] WebSocket 连接成功
- [ ] 麦克风采集正常
- [ ] 音频流发送正常
- [ ] VAD 检测准确
- [ ] STT 识别准确
- [ ] Agent 回复正常
- [ ] TTS 播放正常
- [ ] UI 动画流畅
- [ ] Mobile 端适配
- [ ] 横屏适配

## 部署

### 本地开发

```bash
# 1. 启动网关
cd wsl2
python3 agent-gateway.py

# 2. 启动 HTTP 服务器
cd ~/workspaces/audio-proxy
./start-test-server.sh

# 3. 打开浏览器
http://localhost:8080/test-pages/pro-call.html
```

### 生产环境

待实现:
- [ ] HTTPS 支持
- [ ] 反向代理 (Nginx)
- [ ] 进程管理 (systemd/supervisor)
- [ ] 日志轮转
- [ ] 监控告警

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT
