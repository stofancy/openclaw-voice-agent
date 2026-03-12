# 阿里 DashScope 流式 API 详尽文档

**官方文档**: https://help.aliyun.com/zh/dashscope/

---

## 📋 API 概览

阿里 DashScope (模型服务) 提供完整的多模态能力，语音相关 API 如下：

| API | 端点 | 延迟 | 说明 |
|-----|------|------|------|
| **实时语音识别** | `/api/v1/services/audio/transcription/stream` | 80-150ms | 流式 STT |
| **Qwen 流式对话** | `/api/v1/services/aigc/text-generation/generation` | 100-200ms | 流式 LLM |
| **流式语音合成** | `/api/v1/services/audio/speech` | 100-180ms | 流式 TTS |

---

## 🔑 认证

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**Dashboard**: https://dashscope.console.aliyun.com/apiKey

---

## 🎤 1. 实时语音识别 (Streaming ASR)

### 端点
```
POST https://dashscope.aliyuncs.com/api/v1/services/audio/transcription/stream
```

### WebSocket 方式 (推荐)

```python
import asyncio
import websockets
import json

uri = "wss://dashscope.aliyuncs.com/api/v1/services/audio/transcription/stream"

async with websockets.connect(uri, extra_headers={
    "Authorization": f"Bearer {API_KEY}",
    "X-DashScope-DataInspection": "enable"
}) as ws:
    # 发送配置
    await ws.send(json.dumps({
        "header": {
            "action": "start",
            "task_id": "unique-task-id",
            "streaming": "ws"
        },
        "payload": {
            "format": "pcm",
            "sample_rate": 16000,
            "enable_intermediate_result": True,
            "enable_punctuation_prediction": True
        }
    }))
    
    # 发送音频
    for chunk in audio_chunks:
        await ws.send(chunk)
    
    # 接收结果
    async for message in ws:
        result = json.loads(message)
        if result.get("payload", {}).get("result"):
            print(result["payload"]["result"]["text"])
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `format` | string | 是 | 音频格式 (pcm/wav/mp3) |
| `sample_rate` | int | 是 | 采样率 (16000/8000) |
| `enable_intermediate_result` | bool | 否 | 返回中间结果 |
| `enable_punctuation_prediction` | bool | 否 | 标点预测 |
| `enable_inverse_text_normalization` | bool | 否 | 文本逆规范化 |

### 响应格式

```json
{
  "header": {
    "action": "result",
    "task_id": "unique-task-id",
    "status_code": 20000000
  },
  "payload": {
    "result": {
      "text": "你好请测试",
      "confidence": 0.95,
      "is_final": false
    }
  }
}
```

### 状态码

| 状态码 | 说明 |
|--------|------|
| 20000000 | 成功 |
| 40000001 | 无效参数 |
| 40000002 | 认证失败 |
| 40000003 | 频率限制 |
| 50000001 | 服务器错误 |

---

## 🧠 2. Qwen 流式对话

### 端点
```
POST https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
```

### 请求格式

```python
import aiohttp
import json

url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-DashScope-SSE": "enable"
}

payload = {
    "model": "qwen-turbo",
    "input": {
        "messages": [
            {"role": "system", "content": "你是一个语音助手"},
            {"role": "user", "content": "你好"}
        ]
    },
    "parameters": {
        "result_format": "message",
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 512
    }
}

async with aiohttp.ClientSession() as session:
    async with session.post(url, headers=headers, json=payload) as resp:
        async for line in resp.content:
            if line.startswith(b"data:"):
                data = json.loads(line[5:])
                if data.get("output", {}).get("choices"):
                    content = data["output"]["choices"][0]["message"]["content"]
                    print(content, end="")
```

### 可用模型

| 模型 | 说明 | 延迟 | 成本 |
|------|------|------|------|
| `qwen-turbo` | 快速版 | ⭐⭐⭐⭐⭐ | ¥0.002/1K |
| `qwen-plus` | 平衡版 | ⭐⭐⭐⭐ | ¥0.004/1K |
| `qwen-max` | 最强版 | ⭐⭐⭐ | ¥0.02/1K |
| `qwen-long` | 长文本 | ⭐⭐⭐ | ¥0.006/1K |

### 请求参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | string | - | 模型名称 |
| `input.messages` | array | - | 对话历史 |
| `parameters.stream` | bool | false | 启用流式 |
| `parameters.temperature` | float | 0.7 | 创造性 |
| `parameters.max_tokens` | int | 512 | 最大输出 |
| `parameters.top_p` | float | 0.9 | 核采样 |
| `parameters.stop` | array | - | 停止词 |

### 响应格式 (SSE)

```
data: {"output":{"choices":[{"message":{"content":"你"},"finish_reason":"null"}]},"usage":{}}

data: {"output":{"choices":[{"message":{"content":"好"},"finish_reason":"null"}]},"usage":{}}

data: {"output":{"choices":[{"message":{"content":""},"finish_reason":"stop"}]},"usage":{"total_tokens":10}}
```

---

## 🔊 3. 流式语音合成 (Streaming TTS)

### 端点
```
POST https://dashscope.aliyuncs.com/api/v1/services/audio/speech
```

### 请求格式

```python
url = "https://dashscope.aliyuncs.com/api/v1/services/audio/speech"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-DashScope-Streaming": "enable"
}

payload = {
    "model": "sambert-zh-v1",
    "input": {
        "text": "你好，我是阿里语音助手"
    },
    "parameters": {
        "voice": "xiaoyun",
        "format": "mp3",
        "sample_rate": 24000,
        "volume": 50,
        "rate": 0,
        "pitch": 0
    }
}

async with aiohttp.ClientSession() as session:
    async with session.post(url, headers=headers, json=payload) as resp:
        async for chunk in resp.content.iter_chunked(4096):
            # 播放音频块
            audio_queue.put(chunk)
```

### 可用音色

| 音色 | 名称 | 风格 |
|------|------|------|
| `xiaoyun` | 小云 | 温柔女声 |
| `xiaogang` | 小刚 | 沉稳男声 |
| `xiaomei` | 小美 | 甜美少女 |
| `aixia` | 艾夏 | 新闻主播 |
| `aiqi` | 艾琪 | 客服女声 |

### 请求参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | string | - | TTS 模型 |
| `input.text` | string | - | 合成文本 |
| `parameters.voice` | string | xiaoyun | 音色 |
| `parameters.format` | string | mp3 | 输出格式 |
| `parameters.sample_rate` | int | 24000 | 采样率 |
| `parameters.volume` | int | 50 | 音量 (0-100) |
| `parameters.rate` | int | 0 | 语速 (-500~500) |
| `parameters.pitch` | int | 0 | 音调 (-500~500) |

### 可用模型

| 模型 | 说明 | 延迟 | 成本 |
|------|------|------|------|
| `sambert-zh-v1` | 中文基础 | ⭐⭐⭐⭐⭐ | ¥0.001/100 字 |
| `sambert-zh-v2` | 中文进阶 | ⭐⭐⭐⭐ | ¥0.002/100 字 |
| `cosyvoice-v1` | 情感丰富 | ⭐⭐⭐ | ¥0.005/100 字 |

---

## 🚀 端到端流式架构

### 延迟预算

```
┌─────────────────────────────────────────────────────────┐
│  环节                      │  目标延迟   │  优化技巧     │
├─────────────────────────────────────────────────────────┤
│  Windows 采集 → VAD        │  10-20ms   │  16ms 分片     │
│  WebSocket 传输            │  10-20ms   │  本地网络      │
│  WSL2 → 阿里 STT           │  80-120ms  │  实时识别      │
│  STT → Qwen (首 token)     │  100-150ms │  预填充 Prompt │
│  Qwen → TTS (首音频)       │  80-120ms  │  流式合成      │
│  TTS 播放缓冲              │  30-50ms   │  首包即播      │
├─────────────────────────────────────────────────────────┤
│  **总计**                  │  **310-480ms** │            │
└─────────────────────────────────────────────────────────┘
```

### 与 Minimax 对比

| 维度 | Minimax | 阿里 DashScope |
|------|---------|---------------|
| **STT 延迟** | 50-100ms ⭐ | 80-150ms |
| **LLM 延迟** | 100-200ms ⭐ | 100-200ms |
| **TTS 延迟** | 80-150ms ⭐ | 100-180ms |
| **中文质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **成本** | 中等 | 较低 ⭐ |
| **生态整合** | 一般 | 强 ⭐ |

---

## ⚠️ 错误处理

### 常见错误

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 40000001 | InvalidParameter | 检查请求参数 |
| 40000002 | InvalidApiKey | 检查 API Key |
| 40000003 | QuotaExhausted | 余额不足 |
| 40000004 | TooManyRequests | 频率限制 |
| 50000001 | InternalError | 服务器错误，重试 |

### 重试策略

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_dashscope(url, headers, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"API error: {resp.status}")
            return resp
```

---

## 📊 性能基准

**测试环境**: 上海 → 阿里云华东节点

| 场景 | P50 | P90 | P99 |
|------|-----|-----|-----|
| STT (5 秒音频) | 150ms | 220ms | 350ms |
| Qwen-Turbo (50 tokens) | 180ms | 280ms | 450ms |
| TTS (50 字符) | 120ms | 180ms | 300ms |
| **端到端** | **450ms** | **680ms** | **1100ms** |

---

## 🔗 相关链接

- 官方文档: https://help.aliyun.com/zh/dashscope/
- API 控制台: https://dashscope.console.aliyun.com/
- SDK 下载: https://github.com/aliyun/alibabacloud-dashscope-sdk-python
- 模型列表: https://help.aliyun.com/zh/dashscope/models/

---

_最后更新：2026-03-11_
