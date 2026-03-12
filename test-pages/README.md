# 语音网关测试页面

**位置**: `~/workspaces/audio-proxy/test-pages/`

---

## 📋 测试页面列表

| 文件 | 说明 | 用途 |
|------|------|------|
| `simple-test.html` | 简单连接测试 | 测试 WebSocket 连接 |
| `mic-test.html` | 麦克风测试 | 测试音频采集 + WebSocket |
| `full-test.html` | 完整功能测试 | STT → Agent → TTS 端到端 |

---

## 🚀 快速开始

### 1. 启动网关

```bash
cd ~/workspaces/audio-proxy/wsl2
python3 agent-gateway.py
```

### 2. 打开测试页面

```bash
# 在浏览器中打开
file:///home/ztmdsbt/workspaces/audio-proxy/test-pages/simple-test.html
```

### 3. 测试连接

- 点击"连接"按钮
- 观察状态变化
- 发送测试消息

---

## 📊 WebSocket 配置

| 参数 | 值 |
|------|-----|
| **URL** | `ws://localhost:8765` |
| **协议** | WebSocket |
| **消息格式** | JSON |

---

## 🧪 测试用例

### 测试 1: WebSocket 连接

```javascript
ws = new WebSocket("ws://localhost:8765");
ws.onopen = () => console.log("✅ 连接成功");
ws.onerror = (e) => console.log("❌ 连接失败", e);
```

### 测试 2: 发送 STT 结果

```javascript
ws.send(JSON.stringify({
    type: "stt_result",
    text: "你好，请用一句话介绍你自己"
}));
```

### 测试 3: 接收回复

```javascript
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    console.log("收到:", data);
    // data.type: "status" | "reply" | "audio"
};
```

---

## ⚠️ 注意事项

1. **网关必须先运行** - 否则连接会失败
2. **浏览器可能限制 file://** - 建议用 HTTP 服务器
3. **麦克风需要 HTTPS 或 localhost** - 本地测试没问题

---

_最后更新：2026-03-12_
