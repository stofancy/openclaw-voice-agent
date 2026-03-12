# 流式音频 API 对比文档

_最后更新：2026-03-11_

---

## 📊 概述

流式 API vs 批量 API 的延迟对比：

| 模式 | STT 延迟 | TTS 延迟 | 端到端 |
|------|---------|---------|--------|
| **批量** | 等说完上传 → 500-2000ms | 等生成完下载 → 300-800ms | 1-3 秒 ❌ |
| **流式** | 边说边识别 → 100-300ms | 边生成边播放 → 100-200ms | 200-500ms ✅ |

**结论**: 语音聊天必须用流式 API

---

## 🎯 Minimax 流式 API

### 1. 流式语音识别 (Streaming ASR)

**文档**: https://platform.minimaxi.com/document/guides/asr

**端点**:
```
POST https://api.minimax.chat/v1/asr_stream
```

**请求格式** (WebSocket):
```python
# 连接 WebSocket
ws = websocket.WebSocket()
ws.connect("wss://api.minimax.chat/v1/asr_stream?api_key=YOUR_KEY")

# 发送配置帧
ws.send(json.dumps({
    "sample_rate": 16000,
    "format": "pcm",
    "language": "zh-CN"
}).encode())

# 发送音频帧 (每帧 20-40ms)
ws.send(audio_chunk)

# 接收识别结果
result = ws.recv()
# {"text": "你好", "is_final": false}
```

**响应格式**:
```json
{
  "text": "当前识别的文本",
  "is_final": false,
  "confidence": 0.95
}
```

**延迟**:
- 首字延迟：100-200ms
- 实时率：< 0.3 (处理 1 秒音频需 <300ms)

---

### 2. 流式文本生成 (Streaming Chat)

**文档**: https://platform.minimaxi.com/document/guides/chat

**端点**:
```
POST https://api.minimax.chat/v1/text/chatcompletion_stream
```

**请求格式**:
```python
import aiohttp

async with aiohttp.ClientSession() as session:
    async with session.post(
        "https://api.minimax.chat/v1/text/chatcompletion_stream",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "abab6.5s-chat",
            "messages": [{"role": "user", "content": "你好"}],
            "stream": True,
            "use_standard_stream": True  # 使用标准 SSE 格式
        }
    ) as resp:
        async for line in resp.content:
            if line.startswith(b"data: "):
                data = json.loads(line[6:])
                content = data["choices"][0]["delta"]["content"]
                print(content, end="")  # 流式输出
```

**响应格式** (SSE):
```
data: {"choices": [{"delta": {"content": "你"}}]}
data: {"choices": [{"delta": {"content": "好"}}]}
data: {"choices": [{"delta": {"content": "，"}}]}
data: [DONE]
```

**延迟**:
- 首 token: 100-300ms
- 生成速度：50-100 tokens/秒

---

### 3. 流式语音合成 (Streaming TTS)

**文档**: https://platform.minimaxi.com/document/guides/tts

**端点**:
```
POST https://api.minimax.chat/v1/t2a_stream
```

**请求格式**:
```python
async with aiohttp.ClientSession() as session:
    async with session.post(
        "https://api.minimax.chat/v1/t2a_stream",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "speech-01",
            "text": "你好，欢迎使用语音助手",
            "voice_id": "female-shaonv",
            "format": "mp3",
            "stream": True
        }
    ) as resp:
        # 流式读取音频数据
        async for chunk in resp.content.iter_chunked(4096):
            # 直接送到播放器
            await play_audio_chunk(chunk)
```

**响应格式**:
- 原始音频流 (MP3/PCM)
- Content-Type: audio/mpeg

**延迟**:
- 首包延迟：100-200ms
- 播放延迟：几乎实时

---

### 4. Minimax 全流式管道

```python
async def minimax_full_stream(audio_input):
    """
    全流式处理：音频输入 → STT → LLM → TTS → 音频输出
    """
    
    # 1. 流式 STT (WebSocket)
    stt_ws = await websocket.connect("wss://api.minimax.chat/v1/asr_stream")
    
    # 2. 流式 LLM (SSE)
    llm_session = aiohttp.ClientSession()
    
    # 3. 流式 TTS (HTTP Streaming)
    tts_session = aiohttp.ClientSession()
    
    # 音频采集 → STT
    async for audio_chunk in audio_input:
        await stt_ws.send(audio_chunk)
        
        # 接收部分识别结果
        stt_result = await stt_ws.recv()
        if stt_result['is_final']:
            # 发送到 LLM
            async with llm_session.post(
                "https://api.minimax.chat/v1/text/chatcompletion_stream",
                json={"messages": [{"role": "user", "content": stt_result['text']}]}
            ) as resp:
                # 流式接收 LLM 输出
                async for line in resp.content:
                    if line.startswith(b"data: "):
                        content = parse_sse(line)
                        
                        # 累积到一定长度后发送到 TTS
                        tts_buffer += content
                        if len(tts_buffer) > 20:  # 每 20 字发送一次
                            async with tts_session.post(
                                "https://api.minimax.chat/v1/t2a_stream",
                                json={"text": tts_buffer}
                            ) as tts_resp:
                                async for audio_chunk in tts_resp.content:
                                    await play_audio(audio_chunk)
                            tts_buffer = ""
```

**端到端延迟**: 200-400ms ✅

---

## 🎯 阿里 DashScope 流式 API

### 1. 实时语音识别 (Real-time ASR)

**文档**: https://help.aliyun.com/zh/dashscope/developer-reference/real-time-speech-recognition

**端点** (WebSocket):
```
wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1
```

**请求格式**:
```python
import websocket
import json

# 连接
ws = websocket.WebSocket()
ws.connect("wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1")

# 发送任务启动消息
ws.send(json.dumps({
    "header": {
        "message_id": "unique-id-123",
        "task_id": "task-456",
        "namespace": "SpeechTranscriber",
        "name": "StartTranscription"
    },
    "payload": {
        "format": "pcm",
        "sample_rate": 16000,
        "enable_intermediate_result": True,
        "enable_punctuation_prediction": True
    }
}))

# 发送音频数据
ws.send_binary(audio_chunk)

# 接收结果
result = json.loads(ws.recv())
# {
#   "header": {"name": "TranscriptionResultChanged"},
#   "payload": {"result": "你好", "is_final": False}
# }
```

**响应类型**:
- `TranscriptionResultChanged`: 中间结果
- `TranscriptionCompleted`: 最终结果
- `TaskFailed`: 错误

**延迟**:
- 首字延迟：150-250ms
- 实时率：< 0.3

---

### 2. 流式文本生成 (Qwen Streaming)

**文档**: https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-streaming

**端点**:
```
POST https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
```

**请求格式**:
```python
import dashscope
from dashscope import Generation

# 方式 1: SDK
responses = Generation.call(
    model="qwen-turbo",
    messages=[{"role": "user", "content": "你好"}],
    stream=True,
    incremental_output=True  # 增量输出
)

for response in responses:
    print(response.output.choices[0].message.content, end="")

# 方式 2: HTTP
async with aiohttp.ClientSession() as session:
    async with session.post(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "qwen-turbo",
            "input": {"messages": [{"role": "user", "content": "你好"}]},
            "parameters": {"stream": True}
        }
    ) as resp:
        async for line in resp.content:
            if line.startswith(b"data:"):
                data = json.loads(line[5:])
                content = data["output"]["choices"][0]["message"]["content"]
                print(content, end="")
```

**延迟**:
- 首 token: 150-350ms
- 生成速度：40-80 tokens/秒

---

### 3. 流式语音合成 (Streaming TTS)

**文档**: https://help.aliyun.com/zh/dashscope/developer-reference/text-to-speech-streaming

**端点** (WebSocket):
```
wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1
```

**请求格式**:
```python
# 连接
ws = websocket.WebSocket()
ws.connect("wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1")

# 启动任务
ws.send(json.dumps({
    "header": {
        "message_id": "unique-id",
        "task_id": "tts-task-id",
        "namespace": "SpeechSynthesizer",
        "name": "StartSynthesis"
    },
    "payload": {
        "text": "你好，欢迎使用",
        "voice": "sambert-zh-v1",
        "format": "mp3",
        "sample_rate": 16000
    }
}))

# 接收音频流
while True:
    audio_chunk = ws.recv_binary()
    await play_audio(audio_chunk)
```

**HTTP 流式替代方案**:
```python
async with aiohttp.ClientSession() as session:
    async with session.post(
        "https://dashscope.aliyuncs.com/api/v1/services/audio/speech",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "sambert-zh-v1",
            "input": {"text": "你好"},
            "parameters": {"format": "mp3"}
        },
        stream=True
    ) as resp:
        async for chunk in resp.content.iter_chunked(4096):
            await play_audio(chunk)
```

**延迟**:
- 首包延迟：150-250ms
- 播放：几乎实时

---

### 4. 阿里全流式管道

```python
async def ali_full_stream(audio_input):
    """
    阿里全流式处理
    """
    
    # 1. 实时 ASR (WebSocket)
    asr_ws = await websocket.connect(
        "wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1"
    )
    
    # 2. Qwen 流式生成 (SSE)
    llm_session = aiohttp.ClientSession()
    
    # 3. TTS (WebSocket 或 HTTP Streaming)
    tts_ws = await websocket.connect(
        "wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1"
    )
    
    # 启动 ASR 任务
    await asr_ws.send(json.dumps({
        "header": {"namespace": "SpeechTranscriber", "name": "StartTranscription"},
        "payload": {"sample_rate": 16000}
    }))
    
    # 音频采集 → ASR
    async for audio_chunk in audio_input:
        await asr_ws.send_binary(audio_chunk)
        
        # 接收识别结果
        result = json.loads(await asr_ws.recv())
        if result['header']['name'] == 'TranscriptionResultChanged':
            text = result['payload']['result']
            
            # 发送到 LLM
            async with llm_session.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                json={"model": "qwen-turbo", "input": {"messages": [{"role": "user", "content": text}]}}
            ) as resp:
                async for line in resp.content:
                    if line.startswith(b"data:"):
                        content = parse_sse(line)
                        
                        # 发送到 TTS
                        await tts_ws.send(json.dumps({
                            "header": {"namespace": "SpeechSynthesizer", "name": "StartSynthesis"},
                            "payload": {"text": content, "voice": "sambert-zh-v1"}
                        }))
                        
                        # 接收并播放音频
                        audio = await tts_ws.recv_binary()
                        await play_audio(audio)
```

**端到端延迟**: 250-500ms ⚠️

---

## 📊 供应商对比总结

| 维度 | Minimax | 阿里 DashScope |
|------|---------|---------------|
| **STT 延迟** | 100-200ms ✅ | 150-250ms |
| **LLM 延迟** | 100-300ms ✅ | 150-350ms |
| **TTS 延迟** | 100-200ms ✅ | 150-250ms |
| **端到端** | 200-400ms ✅ | 250-500ms ⚠️ |
| **中文质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **API 友好度** | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **文档质量** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **定价** | 中等 | 较低 |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🚀 推荐实现方案

### Minimax 全流式 (推荐)

```python
# 使用 Minimax 流式 API 的完整实现
# 见：../wsl2/audio-receiver-streaming.py
```

### 关键优化点

1. **WebSocket 长连接** - 避免重复握手
2. **增量处理** - 每 20 字发送 TTS，不等完整回复
3. **音频缓冲** - 预缓冲 100ms 音频再播放
4. **并发处理** - STT/LLM/TTS 并行流水线

---

## 📎 参考链接

### Minimax
- 开放平台：https://platform.minimaxi.com/
- API 文档：https://platform.minimaxi.com/document
- 流式 ASR: https://platform.minimaxi.com/document/guides/asr
- 流式 Chat: https://platform.minimaxi.com/document/guides/chat
- 流式 TTS: https://platform.minimaxi.com/document/guides/tts

### 阿里 DashScope
- 控制台：https://dashscope.console.aliyun.com/
- API 文档：https://help.aliyun.com/zh/dashscope/
- 实时 ASR: https://help.aliyun.com/zh/dashscope/developer-reference/real-time-speech-recognition
- Qwen 流式：https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-streaming
- 流式 TTS: https://help.aliyun.com/zh/dashscope/developer-reference/text-to-speech-streaming

---

_文档持续更新中..._
