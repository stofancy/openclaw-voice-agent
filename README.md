# AI Voice Agent - Real-time Voice Call System

📞 像打电话一样和 AI 旅行助手对话

## 功能特性

- ✅ 实时语音通话
- ✅ 自动语音识别 (STT)
- ✅ AI Agent 对话
- ✅ 语音合成 (TTS)
- ✅ Mobile First UI
- ✅ 动态字幕显示

## 快速开始

### 1. 启动语音网关

```bash
cd wsl2
python3 agent-gateway.py
```

### 2. 启动测试服务器

```bash
cd ~/workspaces/audio-proxy
./start-test-server.sh
```

### 3. 打开浏览器

- SDK 演示：http://localhost:8080/test-pages/sdk-demo.html
- 实时通话：http://localhost:8080/test-pages/realtime-call.html

## 项目结构

```
audio-proxy/
├── sdk/                      # JavaScript SDK
│   └── voice-gateway.js      # 浏览器端 SDK
├── wsl2/                     # 网关代码
│   └── agent-gateway.py      # Python 语音网关
├── test-pages/               # 测试页面
│   ├── sdk-demo.html         # SDK 演示
│   ├── realtime-call.html    # 实时通话
│   └── simple-test.html      # 简单测试
├── docs/                     # 文档
└── logs/                     # 日志目录
```

## 技术栈

- **前端**: HTML5, CSS3, JavaScript, Web Audio API
- **后端**: Python 3.12, websockets
- **AI 服务**: 阿里百炼 (STT + LLM + TTS)
- **Agent**: OpenClaw travel-agency

## 开发

```bash
# 安装依赖
cd wsl2
pip install -r requirements.txt

# 运行测试
python3 debug-test.py
```

## 许可证

MIT
