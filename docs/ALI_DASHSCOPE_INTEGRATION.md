# 阿里 DashScope 流式 API 集成指南

_首选供应商 - 完整技术文档_

---

## 📋 概述

**阿里 DashScope 优势**:
- ✅ 主公账户已有余额
- ✅ 中文语音识别行业标杆
- ✅ 全链路自研 (STT+LLM+TTS)
- ✅ 实时流式 API 支持
- ✅ 文档完善，生态整合好

**延迟目标**: 250-500ms 端到端

---

## 🔑 API Key 配置

### 获取步骤

1. **访问控制台**: https://dashscope.console.aliyun.com/
2. **登录阿里云账户**
3. **开通 DashScope 服务**
   - 首次使用需开通
   - 部分模型需单独申请配额
4. **创建 API Key**
   - 进入「API-KEY 管理」
   - 点击「创建新的 API-KEY」
   - 复制并保存 (只显示一次)

### 验证余额

```bash
# 查看账户余额
curl -X GET "https://dashscope.aliyuncs.com/api/v1/account/balance" \
  -H "Authorization: Bearer $ALI_API_KEY"
```

---

## 🎯 核心 API

### 1. 实时语音识别 (Paraformer)

**模型**: `paraformer-v2`

**延迟**: 首字 150-250ms

#### 方式 A: WebSocket 实时流 (推荐)

```python
import websocket
import json
import threading

class AliRealtimeASR:
    def __init__(self, api_key):
        self.api_key = api_key
        self.ws_url = "wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1"
        
    async def connect(self):
        self.ws = websocket.WebSocket()
        self.ws.connect(self.ws_url)
        
        # 启动任务
        task_id = "task-123456"
        start_message = {
            "header": {
                "message_id": "msg-001",
                "task_id": task_id,
                "namespace": "SpeechTranscriber",
                "name": "StartTranscription"
            },
            "payload": {
                "format": "pcm",
                "sample_rate": 16000,
                "enable_intermediate_result": True,  # 中间结果
                "enable_punctuation_prediction": True,  # 标点预测
                "enable_inverse_text_normalization": True,  # 逆文本规范化
                "language": "zh-CN"
            }
        }
        self.ws.send(json.dumps(start_message))
    
    async def send_audio(self, audio_chunk):
        """发送音频数据 (PCM, 16kHz, 16bit)"""
        self.ws.send_binary(audio_chunk)
    
    async def receive_result(self):
        """接收识别结果"""
        result = json.loads(self.ws.recv())
        
        header = result.get('header', {})
        payload = result.get('payload', {})
        
        # 结果类型
        name = header.get('name')
        
        if name == 'TranscriptionResultChanged':
            # 中间结果 (可丢弃或用于实时显示)
            return {
                'type': 'intermediate',
                'text': payload.get('result', ''),
                'is_final': False
            }
        elif name == 'TranscriptionCompleted':
            # 最终结果
            return {
                'type': 'final',
                'text': payload.get('result', ''),
                'is_final': True
            }
        elif name == 'TaskFailed':
            raise Exception(f"ASR failed: {payload.get('message', '')}")
        
        return None
    
    async def close(self):
        # 停止任务
        stop_message = {
            "header": {
                "message_id": "msg-002",
                "task_id": task_id,
                "namespace": "SpeechTranscriber",
                "name": "StopTranscription"
            }
        }
        self.ws.send(json.dumps(stop_message))
        self.ws.close()
```

#### 方式 B: HTTP 批量 (简化版)

```python
import aiohttp

async def ali_batch_asr(api_key, audio_path):
    """批量语音识别 (非流式，延迟较高)"""
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/transcription"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 上传文件
    with open(audio_path, 'rb') as f:
        audio_data = f.read()
    
    payload = {
        "model": "paraformer-v2",
        "input": {"file": audio_data},
        "parameters": {
            "format": "wav",
            "sample_rate": 16000,
            "language": "zh-CN"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            result = await resp.json()
            return result.get('output', {}).get('text', '')
```

**定价**: ¥0.002/分钟

---

### 2. 流式文本生成 (Qwen)

**模型**: `qwen-turbo` (快) / `qwen-plus` (强)

**延迟**: 首 token 150-350ms

#### 流式调用

```python
import aiohttp
import json

async def ali_streaming_chat(api_key, user_text):
    """Qwen 流式对话"""
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {"role": "system", "content": "你是一个语音助手，回复要简洁口语化。"},
                {"role": "user", "content": user_text}
            ]
        },
        "parameters": {
            "stream": True,  # 启用流式
            "incremental_output": True  # 增量输出
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            async for line in resp.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data:'):
                    data_str = line[5:]
                    if data_str == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        content = data['output']['choices'][0]['message']['content']
                        yield content  # 流式返回
                    except (json.JSONDecodeError, KeyError):
                        continue
```

**定价**:
- qwen-turbo: ¥0.002/1K tokens
- qwen-plus: ¥0.02/1K tokens

---

### 3. 流式语音合成 (Sambert)

**模型**: `sambert-zh-v1` (自然女声) / `sambert-zh-v2` (更新)

**延迟**: 首包 150-250ms

#### 方式 A: WebSocket 实时流

```python
import websocket
import json

class AliStreamingTTS:
    def __init__(self, api_key):
        self.api_key = api_key
        self.ws_url = "wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1"
        
    async def connect(self):
        self.ws = websocket.WebSocket()
        self.ws.connect(self.ws_url)
    
    async def synthesize(self, text):
        """合成语音并流式播放"""
        task_id = "tts-task-123"
        
        # 启动任务
        start_message = {
            "header": {
                "message_id": "msg-001",
                "task_id": task_id,
                "namespace": "SpeechSynthesizer",
                "name": "StartSynthesis"
            },
            "payload": {
                "text": text,
                "voice": "sambert-zh-v1",
                "format": "mp3",
                "sample_rate": 16000,
                "volume": 50,
                "rate": 0,  # 语速 -5~5
                "pitch": 0  # 音调 -5~5
            }
        }
        self.ws.send(json.dumps(start_message))
        
        # 接收音频流
        while True:
            audio_chunk = self.ws.recv_binary()
            if len(audio_chunk) == 0:
                break
            
            # 直接送到播放器
            yield audio_chunk
    
    async def close(self):
        self.ws.close()
```

#### 方式 B: HTTP 流式 (简化)

```python
import aiohttp

async def ali_http_tts(api_key, text):
    """HTTP 流式 TTS"""
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sambert-zh-v1",
        "input": {"text": text},
        "parameters": {
            "format": "mp3",
            "sample_rate": 16000
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload, stream=True) as resp:
            async for chunk in resp.content.iter_chunked(4096):
                yield chunk
```

**定价**: ¥0.001/100 字符

---

## 🔄 完整流式管道

```python
import asyncio
import aiohttp
import websocket
import json
import tempfile
import subprocess

class AliFullStreamingPipeline:
    """
    阿里全流式管道:
    音频输入 → Paraformer STT → Qwen LLM → Sambert TTS → 播放
    """
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.http_session = None
        
    async def initialize(self):
        self.http_session = aiohttp.ClientSession()
    
    async def close(self):
        if self.http_session:
            await self.http_session.close()
    
    async def process(self, audio_chunks):
        """
        处理音频流
        
        Args:
            audio_chunks: 音频分片迭代器
        
        Yields:
            识别文本 + 播放音频
        """
        # ========== 1. 实时 STT ==========
        asr_ws = websocket.WebSocket()
        asr_ws.connect("wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1")
        
        # 启动 ASR 任务
        asr_ws.send(json.dumps({
            "header": {
                "message_id": "msg-001",
                "task_id": "asr-task-123",
                "namespace": "SpeechTranscriber",
                "name": "StartTranscription"
            },
            "payload": {
                "format": "pcm",
                "sample_rate": 16000,
                "enable_intermediate_result": True
            }
        }))
        
        # 发送音频 + 接收结果
        full_text = ""
        async for chunk in audio_chunks:
            asr_ws.send_binary(chunk)
            
            # 非阻塞接收结果
            try:
                asr_ws.settimeout(0.1)
                result = json.loads(asr_ws.recv())
                if result['header']['name'] == 'TranscriptionCompleted':
                    full_text = result['payload']['result']
                    break
            except:
                continue
        
        if not full_text:
            return
        
        print(f"识别结果：{full_text}")
        
        # ========== 2. 流式 LLM ==========
        llm_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        tts_buffer = ""
        async with self.http_session.post(
            llm_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "qwen-turbo",
                "input": {"messages": [{"role": "user", "content": full_text}]},
                "parameters": {"stream": True}
            }
        ) as resp:
            async for line in resp.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data:'):
                    content = parse_sse(line)
                    if content:
                        tts_buffer += content
                        
                        # 每 20 字发送 TTS
                        if len(tts_buffer) >= 20:
                            await self.stream_tts(tts_buffer)
                            tts_buffer = ""
        
        # 发送剩余文本
        if tts_buffer:
            await self.stream_tts(tts_buffer)
    
    async def stream_tts(self, text):
        """流式 TTS 并播放"""
        tts_url = "https://dashscope.aliyuncs.com/api/v1/services/audio/speech"
        
        async with self.http_session.post(
            tts_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "sambert-zh-v1",
                "input": {"text": text},
                "parameters": {"format": "mp3"}
            },
            stream=True
        ) as resp:
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                async for chunk in resp.content.iter_chunked(4096):
                    f.write(chunk)
                audio_path = f.name
            
            # 播放
            proc = subprocess.Popen(
                ['ffplay', '-autoexit', '-nodisp', '-loglevel', 'quiet', audio_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            await asyncio.get_event_loop().run_in_executor(None, proc.wait)
            
            # 清理
            import os
            os.unlink(audio_path)


def parse_sse(line):
    """解析 SSE 格式"""
    if line.startswith('data:'):
        data_str = line[5:]
        if data_str == '[DONE]':
            return None
        try:
            data = json.loads(data_str)
            return data['output']['choices'][0]['message']['content']
        except:
            return None
    return None


# 使用示例
async def main():
    pipeline = AliFullStreamingPipeline(api_key="YOUR_KEY")
    await pipeline.initialize()
    
    # 模拟音频输入
    async def audio_generator():
        for i in range(100):
            yield b'\x00' * 1024  # 静音 PCM
            await asyncio.sleep(0.032)  # 32ms
    
    await pipeline.process(audio_generator())
    await pipeline.close()

asyncio.run(main())
```

---

## 📊 延迟预算

| 环节 | 目标 | 实测 |
|------|------|------|
| WebSocket 传输 | 10-30ms | ___ ms |
| Paraformer STT | 150-250ms | ___ ms |
| Qwen LLM (首 token) | 150-350ms | ___ ms |
| Sambert TTS (首包) | 150-250ms | ___ ms |
| 播放缓冲 | 50-100ms | ___ ms |
| **端到端** | **250-500ms** | ___ ms |

---

## ⚠️ 常见问题

### 问题 1: WebSocket 连接失败

```
websocket._exceptions.WebSocketConnectionClosedException
```

**解决**:
- 检查网络连通性
- 确认 API Key 有效
- 检查防火墙设置

### 问题 2: API 返回 400

```json
{"code": "InvalidParameter", "message": "Invalid sample_rate"}
```

**解决**:
- 确保音频格式正确 (PCM, 16kHz, 16bit, 单声道)
- 检查 WAV 头格式

### 问题 3: TTS 播放有杂音

**解决**:
- 检查音频采样率匹配 (16kHz)
- 确保 PCM 格式正确
- 尝试调整 `volume` 参数

---

## 📎 参考链接

- **控制台**: https://dashscope.console.aliyun.com/
- **API 文档**: https://help.aliyun.com/zh/dashscope/
- **Paraformer**: https://help.aliyun.com/zh/dashscope/developer-reference/real-time-speech-recognition
- **Qwen**: https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-streaming
- **Sambert TTS**: https://help.aliyun.com/zh/dashscope/developer-reference/text-to-speech-streaming

---

_文档持续更新中..._
