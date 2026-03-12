# 阿里云百炼实时多模态 API 文档

_最后更新：2026-03-11_

---

## 📋 概述

**平台**: 阿里云百炼 (Bailian)

**模型**: `qwen3-omni-flash-realtime`

**特性**:
- 🎤 原生实时音频对话
- 👁️ 视觉 + 音频多模态
- ⚡ 低延迟流式处理
- 🔌 WebSocket 实时连接

---

## 🔗 官方文档

### 实时多模态模型
- **模型详情**: https://bailian.console.aliyun.com/cn-beijing/?tab=model#/model-market/detail/qwen3-omni-flash-realtime

### 实时语音合成 (TTS)
- **文档**: https://bailian.console.aliyun.com/cn-beijing/?tab=doc#/doc/?type=model&url=2938790
- **API**: WebSocket 实时流

### 实时语音识别 (STT)
- **文档**: https://bailian.console.aliyun.com/cn-beijing/?tab=api#/api/?type=model&url=2983776
- **API**: WebSocket 实时流

---

## 🔑 认证方式

### API Key

**获取位置**:
1. 访问：https://bailian.console.aliyun.com/
2. 登录阿里云
3. 进入「API Key 管理」
4. 创建/复制 API Key

**环境变量**:
```bash
ALI_BAILIAN_API_KEY=sk-xxx  # 百炼平台的 API Key
```

---

## 🎯 实时多模态模型 API

### 端点 (正确的 WebSocket 端点)

```
wss://dashscope.aliyuncs.com/api-ws/v1/realtime
```

**注意**: 这是百炼实时多模态的统一接入点，STT/LLM/TTS 都通过这个端点

### 连接参数

```python
import websocket
import json

# 连接 WebSocket
ws = websocket.WebSocket()
ws.connect("wss://bailian.cn-beijing.aliyuncs.com/ws/v1",
           header={
               "Authorization": f"Bearer {API_KEY}",
               "Content-Type": "application/json"
           })
```

### 请求格式

```json
{
  "model": "qwen3-omni-flash-realtime",
  "input": {
    "audio": "base64_encoded_audio_data",
    "image": "base64_encoded_image_data"  // 可选
  },
  "parameters": {
    "stream": true,
    "incremental_output": true,
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

### 响应格式

```json
{
  "output": {
    "text": "识别的文本",
    "audio": "base64_encoded_audio_response",  // TTS 音频
    "choices": [{
      "message": {
        "role": "assistant",
        "content": "回复内容"
      }
    }]
  },
  "usage": {
    "input_tokens": 100,
    "output_tokens": 50
  }
}
```

---

## 🎤 实时语音识别 (STT)

### WebSocket 端点

```
wss://bailian.cn-beijing.aliyuncs.com/ws/v1/asr
```

### 连接流程

```python
import websocket
import json
import base64

class RealtimeASR:
    def __init__(self, api_key):
        self.api_key = api_key
        self.ws_url = "wss://bailian.cn-beijing.aliyuncs.com/ws/v1/asr"
        
    def connect(self):
        self.ws = websocket.WebSocket()
        self.ws.connect(self.ws_url, header={
            "Authorization": f"Bearer {self.api_key}"
        })
        
        # 发送配置
        config = {
            "format": "pcm",
            "sample_rate": 16000,
            "language": "zh-CN",
            "enable_intermediate_result": True
        }
        self.ws.send(json.dumps(config))
    
    def send_audio(self, audio_chunk):
        """发送 PCM 音频数据"""
        self.ws.send_binary(audio_chunk)
    
    def receive_result(self):
        """接收识别结果"""
        result = json.loads(self.ws.recv())
        return {
            'text': result.get('output', {}).get('text', ''),
            'is_final': result.get('is_final', False)
        }
    
    def close(self):
        self.ws.close()
```

### 定价

- **实时语音识别**: ¥0.002/分钟
- **免费额度**: 新用户可能有体验包

---

## 🔊 实时语音合成 (TTS)

### WebSocket 端点

```
wss://bailian.cn-beijing.aliyuncs.com/ws/v1/tts
```

### 连接流程

```python
class RealtimeTTS:
    def __init__(self, api_key):
        self.api_key = api_key
        self.ws_url = "wss://bailian.cn-beijing.aliyuncs.com/ws/v1/tts"
        
    def connect(self):
        self.ws = websocket.WebSocket()
        self.ws.connect(self.ws_url, header={
            "Authorization": f"Bearer {self.api_key}"
        })
    
    def synthesize(self, text):
        """合成语音"""
        config = {
            "text": text,
            "voice": "default",  # 可选音色
            "format": "pcm",
            "sample_rate": 16000
        }
        self.ws.send(json.dumps(config))
        
        # 接收音频流
        while True:
            audio_chunk = self.ws.recv_binary()
            if len(audio_chunk) == 0:
                break
            yield audio_chunk
    
    def close(self):
        self.ws.close()
```

### 定价

- **实时语音合成**: ¥0.001/100 字符
- **免费额度**: 新用户可能有体验包

---

## 🔄 完整实时管道

### 架构

```
浏览器音频 → WSL2 → 百炼实时 API → 音频回复
    ↓          ↓          ↓           ↓
  采集      转发     STT+LLM+TTS    播放
```

### 代码示例

```python
import asyncio
import websocket
import json
import base64
import aiohttp

class BailianRealtimePipeline:
    def __init__(self, api_key):
        self.api_key = api_key
        self.ws_url = "wss://bailian.cn-beijing.aliyuncs.com/ws/v1"
        
    async def connect(self):
        """连接到实时多模态模型"""
        self.ws = websocket.WebSocket()
        self.ws.connect(self.ws_url, header={
            "Authorization": f"Bearer {self.api_key}"
        })
        
        # 发送模型配置
        config = {
            "model": "qwen3-omni-flash-realtime",
            "parameters": {
                "stream": True,
                "incremental_output": True,
                "temperature": 0.7
            }
        }
        self.ws.send(json.dumps(config))
    
    async def process_audio(self, audio_chunks):
        """
        处理音频流
        
        Args:
            audio_chunks: 音频分片迭代器
        
        Yields:
            文本回复 + 音频回复
        """
        # 发送音频
        async for chunk in audio_chunks:
            # 发送音频数据
            self.ws.send_binary(chunk)
            
            # 非阻塞接收结果
            try:
                self.ws.settimeout(0.1)
                result = json.loads(self.ws.recv())
                
                output = result.get('output', {})
                text = output.get('text', '')
                audio = output.get('audio', '')
                
                if text:
                    print(f"识别：{text}")
                
                if audio:
                    # 解码并播放音频
                    audio_data = base64.b64decode(audio)
                    yield audio_data
                    
            except:
                continue
    
    async def close(self):
        self.ws.close()


# 使用示例
async def main():
    pipeline = BailianRealtimePipeline(api_key="YOUR_KEY")
    await pipeline.connect()
    
    # 模拟音频输入
    async def audio_generator():
        for i in range(100):
            yield b'\x00' * 1024  # PCM 数据
            await asyncio.sleep(0.032)  # 32ms
    
    async for audio_response in pipeline.process_audio(audio_generator()):
        # 播放回复音频
        await play_audio(audio_response)
    
    await pipeline.close()

asyncio.run(main())
```

---

## 📊 延迟预算

| 环节 | 目标延迟 | 说明 |
|------|---------|------|
| 浏览器采集 → WSL2 | 10-30ms | WebSocket 本地传输 |
| WSL2 → 百炼 API | 50-100ms | 网络往返 |
| 百炼实时处理 | 100-200ms | STT+LLM+TTS 一体化 |
| 音频返回 → 播放 | 10-30ms | 本地播放 |
| **端到端** | **170-360ms** | ✅ < 500ms 目标 |

---

## ⚠️ 注意事项

### 1. 音频格式

- **格式**: PCM (无头)
- **采样率**: 16kHz 或 24kHz
- **位深**: 16-bit
- **声道**: 单声道

### 2. WebSocket 心跳

```python
# 定期发送 ping 保持连接
async def heartbeat(ws):
    while True:
        await asyncio.sleep(30)
        ws.ping()
```

### 3. 错误处理

```python
try:
    # API 调用
    pass
except websocket.WebSocketException as e:
    # 重连逻辑
    await reconnect()
except Exception as e:
    # 其他错误
    logger.error(f"Error: {e}")
```

---

## 📎 参考链接

- **百炼控制台**: https://bailian.console.aliyun.com/
- **模型广场**: https://bailian.console.aliyun.com/cn-beijing/?tab=model
- **实时多模态**: `qwen3-omni-flash-realtime`
- **实时 STT**: https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=2983776
- **实时 TTS**: https://bailian.console.aliyun.com/?tab=doc#/doc/?type=model&url=2938790

---

_文档持续更新中..._
