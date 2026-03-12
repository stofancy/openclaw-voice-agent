# Minimax 流式 API 详尽文档

**官方文档**: https://platform.minimaxi.com/document

---

## 📋 API 概览

Minimax 提供完整的流式音频处理能力，支持**端到端流式**以实现最低延迟。

| API | 端点 | 延迟 | 说明 |
|-----|------|------|------|
| **流式 STT** | `/v1/asr_stream` | 50-100ms | 边说边识别 |
| **流式 LLM** | `/v1/text/chatcompletion_stream` | 100-200ms | 流式输出 |
| **流式 TTS** | `/v1/t2a_stream` | 80-150ms | 边生成边播放 |

---

## 🔑 认证

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**请求头必填**:
- `Authorization`: Bearer 令牌
- `Content-Type`: application/json

---

## 🎤 1. 流式 STT (Speech-to-Text)

### 端点
```
POST https://api.minimax.chat/v1/asr_stream
```

### 请求格式

**WebSocket 连接** (推荐):
```python
import websockets
import json

uri = "wss://api.minimax.chat/v1/asr_stream"
async with websockets.connect(uri, extra_headers={
    "Authorization": f"Bearer {API_KEY}"
}) as ws:
    # 发送配置
    await ws.send(json.dumps({
        "type": "config",
        "sample_rate": 16000,
        "format": "pcm",
        "encoding": "raw"
    }))
    
    # 发送音频分片
    for chunk in audio_chunks:
        await ws.send(chunk)
    
    # 接收识别结果
    async for message in ws:
        result = json.loads(message)
        if result.get("type") == "transcript":
            print(result["text"])
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sample_rate` | int | 是 | 采样率 (16000/8000) |
| `format` | string | 是 | 音频格式 (pcm/raw) |
| `encoding` | string | 是 | 编码 (raw/base64) |
| `language` | string | 否 | 语言 (zh-CN/en-US) |
| `enable_punctuation` | bool | 否 | 是否添加标点 |

### 响应格式

```json
{
  "type": "transcript",
  "text": "你好请测试语音助手",
  "is_final": false,
  "confidence": 0.95,
  "offset_ms": 1200
}
```

| 字段 | 说明 |
|------|------|
| `type` | 消息类型 (transcript/error) |
| `text` | 识别文本 |
| `is_final` | 是否最终结果 |
| `confidence` | 置信度 (0-1) |
| `offset_ms` | 时间偏移 |

### 延迟优化技巧

1. **音频分片**: 16-32ms (推荐 20ms)
2. **VAD 集成**: 检测到语音立即发送，无需等待说完
3. **增量结果**: 使用 `is_final: false` 的中间结果

---

## 🧠 2. 流式 LLM (Chat Completion)

### 端点
```
POST https://api.minimax.chat/v1/text/chatcompletion_stream
```

### 请求格式

```python
import aiohttp

url = "https://api.minimax.chat/v1/text/chatcompletion_stream"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "abab6.5s-chat",
    "messages": [
        {"role": "user", "content": "你好"}
    ],
    "stream": True,
    "temperature": 0.7,
    "max_tokens": 512
}

async with aiohttp.ClientSession() as session:
    async with session.post(url, headers=headers, json=payload) as resp:
        async for line in resp.content:
            if line.startswith(b"data: "):
                data = json.loads(line[6:])
                if data["choices"][0]["finish_reason"] != "stop":
                    content = data["choices"][0]["delta"]["content"]
                    print(content, end="")
```

### 请求参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | string | - | 模型 (abab6.5s-chat) |
| `messages` | array | - | 对话历史 |
| `stream` | bool | false | 启用流式 |
| `temperature` | float | 0.7 | 创造性 (0-2) |
| `max_tokens` | int | 512 | 最大输出 |
| `top_p` | float | 0.9 | 核采样 |

### 响应格式 (SSE)

```
data: {"id":"chat-xxx","choices":[{"delta":{"content":"你"},"finish_reason":null}]}

data: {"id":"chat-xxx","choices":[{"delta":{"content":"好"},"finish_reason":null}]}

data: {"id":"chat-xxx","choices":[{"delta":{},"finish_reason":"stop"}]}
```

### 延迟优化技巧

1. **预填充 Prompt**: 在 STT 完成前预加载系统提示
2. **流式拼接**: 收到第一个 token 就开始 TTS
3. **短回复**: 限制 `max_tokens` 减少等待

---

## 🔊 3. 流式 TTS (Text-to-Speech)

### 端点
```
POST https://api.minimax.chat/v1/t2a_stream
```

### 请求格式

```python
url = "https://api.minimax.chat/v1/t2a_stream"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "speech-01",
    "text": "你好，我是语音助手",
    "voice_id": "female-shaonv",
    "format": "mp3",
    "stream": True
}

async with aiohttp.ClientSession() as session:
    async with session.post(url, headers=headers, json=payload) as resp:
        async for chunk in resp.content.iter_chunked(4096):
            # 直接播放音频块
            audio_queue.put(chunk)
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | 模型 (speech-01) |
| `text` | string | 是 | 要合成的文本 |
| `voice_id` | string | 是 | 音色 ID |
| `format` | string | 否 | 输出格式 (mp3/wav/pcm) |
| `stream` | bool | 否 | 启用流式 |
| `speed` | float | 1.0 | 语速 (0.5-2.0) |

### 可用音色

| 音色 ID | 名称 | 风格 |
|--------|------|------|
| `female-shaonv` | 少女 | 甜美活泼 |
| `female-yan` | 御姐 | 成熟优雅 |
| `male-qa` | 青年男声 | 沉稳专业 |
| `male-elder` | 大叔 | 磁性厚重 |
| `child` | 儿童 | 可爱童声 |

### 响应格式

**二进制流**:
```
[MP3 数据块 1][MP3 数据块 2][MP3 数据块 3]...
```

### 延迟优化技巧

1. **首包播放**: 收到第一个音频块立即开始播放
2. **小分片**: 使用 4KB 分片减少缓冲
3. **预加载音色**: 常用音色保持连接池

---

## 🚀 端到端流式架构

### 延迟预算 (优化后)

```
┌─────────────────────────────────────────────────────────┐
│  环节                      │  目标延迟   │  优化技巧     │
├─────────────────────────────────────────────────────────┤
│  Windows 采集 → VAD        │  10-20ms   │  16ms 分片     │
│  WebSocket 传输            │  10-20ms   │  本地网络      │
│  WSL2 → Minimax STT        │  50-80ms   │  流式识别      │
│  STT → LLM (首 token)      │  80-120ms  │  预填充 Prompt │
│  LLM → TTS (首音频)        │  60-100ms  │  流式合成      │
│  TTS 播放缓冲              │  30-50ms   │  首包即播      │
├─────────────────────────────────────────────────────────┤
│  **总计**                  │  **240-390ms** │            │
└─────────────────────────────────────────────────────────┘
```

### 关键优化点

1. **并行处理**: STT 未完成时预加载 LLM context
2. **流式拼接**: 第一个 LLM token → 立即 TTS
3. **VAD 预测**: 检测到停顿立即触发，不等完全静音

---

## ⚠️ 错误处理

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 401 | 认证失败 | 检查 API Key |
| 400 | 请求格式错误 | 检查参数 |
| 429 | 频率限制 | 降低请求频率 |
| 500 | 服务器错误 | 重试 |

### 重试策略

```python
async def call_with_retry(func, max_retries=3):
    for i in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if i == max_retries - 1:
                raise
            await asyncio.sleep(2 ** i)  # 指数退避
```

---

## 📊 性能基准

**测试环境**: 上海 → 阿里云华东节点

| 场景 | P50 | P90 | P99 |
|------|-----|-----|-----|
| STT (5 秒音频) | 120ms | 180ms | 300ms |
| LLM (50 tokens) | 150ms | 250ms | 400ms |
| TTS (50 字符) | 100ms | 150ms | 250ms |
| **端到端** | **370ms** | **580ms** | **950ms** |

---

## 🔗 相关链接

- 官方文档: https://platform.minimaxi.com/document
- API 控制台: https://platform.minimaxi.com/console
- SDK 下载: https://github.com/MiniMax-AI

---

_最后更新：2026-03-11_
