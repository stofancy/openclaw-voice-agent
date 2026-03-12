# Voice Gateway SDK

**位置**: `~/workspaces/audio-proxy/sdk/`

---

## 📦 SDK 组件

| 文件 | 说明 | 语言 |
|------|------|------|
| `voice-gateway.js` | 浏览器端 SDK | JavaScript |
| `voice_gateway.py` | Python 端 SDK | Python |
| `types.d.ts` | TypeScript 类型定义 | TypeScript |

---

## 🚀 快速开始 (JavaScript)

### 1. 引入 SDK

```html
<script src="voice-gateway.js"></script>
```

### 2. 初始化

```javascript
const gateway = new VoiceGateway({
    url: "ws://localhost:8765",
    onConnected: () => console.log("已连接"),
    onDisconnected: () => console.log("已断开"),
    onReply: (text) => console.log("Agent 回复:", text),
    onAudio: (audioBase64) => playAudio(audioBase64),
    onError: (error) => console.error("错误:", error)
});
```

### 3. 发送消息

```javascript
// 发送 STT 结果
gateway.sendSTTResult("你好，请用一句话介绍你自己");

// 或者直接发送文本
gateway.sendText("你好");
```

### 4. 断开连接

```javascript
gateway.disconnect();
```

---

## 🚀 快速开始 (Python)

### 1. 安装依赖

```bash
pip install websockets
```

### 2. 使用 SDK

```python
from voice_gateway import VoiceGateway

async def main():
    gateway = VoiceGateway(
        url="ws://localhost:8765",
        on_reply=lambda text: print(f"Agent: {text}"),
        on_audio=lambda audio: play_audio(audio)
    )
    
    await gateway.connect()
    await gateway.send_stt_result("你好")
    await gateway.disconnect()

import asyncio
asyncio.run(main())
```

---

## 📋 API 文档

### VoiceGateway (JavaScript)

#### 构造函数

```javascript
new VoiceGateway(options: {
    url: string,           // WebSocket URL
    onConnected?: () => void,
    onDisconnected?: () => void,
    onReply?: (text: string) => void,
    onAudio?: (audioBase64: string) => void,
    onError?: (error: Error) => void,
    onStatus?: (status: string) => void
})
```

#### 方法

| 方法 | 说明 |
|------|------|
| `connect()` | 连接网关 |
| `disconnect()` | 断开连接 |
| `sendSTTResult(text: string)` | 发送 STT 结果 |
| `sendText(text: string)` | 发送文本消息 |
| `isConnected()` | 检查连接状态 |

#### 属性

| 属性 | 说明 |
|------|------|
| `state` | 连接状态 (disconnected | connecting | connected) |
| `url` | WebSocket URL |

---

## 📊 消息格式

### 发送到网关

```json
{
    "type": "stt_result",
    "text": "识别的文本"
}
```

### 从网关接收

```json
// 状态更新
{
    "type": "status",
    "status": "processing"
}

// Agent 回复
{
    "type": "reply",
    "text": "Agent 的回复文本"
}

// 音频数据
{
    "type": "audio",
    "data": "base64 编码的 PCM 音频"
}
```

---

## ⚠️ 注意事项

1. **网关必须先运行** - 否则连接会失败
2. **音频格式** - PCM 24000Hz 单声道 16bit
3. **浏览器限制** - file:// 协议可能限制 WebSocket，建议用 HTTP 服务器

---

_最后更新：2026-03-12_
