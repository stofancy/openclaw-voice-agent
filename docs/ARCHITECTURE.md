# Voice Gateway 详细架构设计文档

**版本**: v3.0 (最终版)  
**日期**: 2026-03-13  
**状态**: 正式设计

---

## 1. 项目概述

### 1.1 目标
为 OpenClaw Agent (travel-agency) 实现基于 WebRTC 的语音对话能力。

### 1.2 约束
- **模式**: 半双工 (用户说话时 AI 不说话，AI 说话时用户不听)
- **延迟**: < 3s 端到端
- **技术栈**: WebRTC + 阿里百炼 + OpenClaw Agent

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              浏览器                                    │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  WebRTC API + webrtc-adapter                                    │ │
│  │  - getUserMedia: 麦克风采集                                     │ │
│  │  - RTCPeerConnection: 建立 WebRTC 连接                          │ │
│  │  - RTCRtpSender: 发送音频                                       │ │
│  │  - RTCRtpReceiver: 接收音频                                      │ │
│  │  - 内置 VAD/AEC/ANS                                            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ RTP 音频流
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Python 后端 (aiortc)                           │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  aiortc (WebRTC 服务端)                                         │ │
│  │  - 接收浏览器 RTP 音频流                                         │ │
│  │  - 发送音频给浏览器                                              │ │
│  │  - 处理 ICE/STUN/TURN                                           │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                    ↑                                   │
│                                    │ 音频数据                          │
│                                    ▼                                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  STT Service (阿里百炼)                                          │ │
│  │  - speech-realtime-v2                                           │ │
│  │  - 音频 → 文本                                                  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                    ↑                                   │
│                                    │ 文本                              │
│                                    ▼                                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Agent Service (OpenClaw travel-agency)                         │ │
│  │  - 文本 → 文本 (对话)                                           │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                    ↑                                   │
│                                    │ 文本                              │
│                                    ▼                                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  TTS Service (阿里百炼)                                          │ │
│  │  - cosyvoice-v2                                                 │ │
│  │  - 文本 → 音频                                                  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ RTP 音频流
                                     ▼
                              (返回浏览器播放)
```

---

## 3. 技术选型

### 3.1 前端

| 库 | 用途 | 版本 |
|-----|------|------|
| WebRTC API | 浏览器原生，无需安装 | - |
| webrtc-adapter | 浏览器兼容性 | ^9.0.0 |
| React | UI 框架 | ^18.0.0 |

### 3.2 后端

| 库 | 用途 | 版本 |
|-----|------|------|
| aiortc | WebRTC 服务端 | ^1.14.0 |
| dashscope | 阿里百炼 SDK | ^1.20.0 |
| websockets | WebSocket 信令 | ^14.0 |

---

## 4. 模块设计

### 4.1 前端模块

```
frontend/
├── src/
│   ├── components/
│   │   └── VoiceChat.tsx       # 主组件
│   │
│   ├── hooks/
│   │   ├── useWebRTC.ts       # WebRTC Hook
│   │   └── useAudioRecorder.ts # 录音 Hook
│   │
│   ├── services/
│   │   └── webrtc.ts          # WebRTC 服务
│   │
│   └── App.tsx
│
└── package.json
```

#### 4.1.1 useWebRTC Hook

```typescript
interface UseWebRTCReturn {
  localStream: MediaStream | null;
  remoteStream: MediaStream | null;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  sendAudio: (audioData: ArrayBuffer) => void;
}
```

### 4.2 后端模块

```
backend/
├── voice_gateway/
│   ├── __init__.py
│   ├── main.py                 # 入口
│   ├── webrtc_server.py       # aiortc WebRTC 服务
│   ├── stt_service.py         # 阿里 STT
│   ├── tts_service.py         # 阿里 TTS
│   ├── agent_client.py        # OpenClaw Agent 调用
│   ├── protocol.py            # 消息协议
│   └── config.py              # 配置
│
└── requirements.txt
```

#### 4.2.1 WebRTC Server

```python
class WebRTCServer:
    async def start(self, host: str, port: int):
        """启动 WebRTC 服务器"""
        
    async def handle_offer(self, offer: RTCSessionDescription) -> RTCSessionDescription:
        """处理 SDP Offer，返回 Answer"""
        
    async def handle_ice_candidate(self, candidate: RTCIceCandidate):
        """处理 ICE Candidate"""
```

#### 4.2.2 STT Service

```python
class STTService:
    def __init__(self, api_key: str):
        self.client = dashscope.audio.asr
        
    async def recognize(self, audio_bytes: bytes) -> str:
        """将音频转为文本"""
        
    async def recognize_stream(self, audio_stream) -> AsyncIterator[str]:
        """流式识别"""
```

#### 4.2.3 TTS Service

```python
class TTSService:
    def __init__(self, api_key: str):
        self.client = dashscope.audio.tts
        
    async def synthesize(self, text: str) -> bytes:
        """将文本转为音频"""
        
    async def synthesize_stream(self, text: str) -> AsyncIterator[bytes]:
        """流式合成"""
```

#### 4.2.4 Agent Client

```python
class AgentClient:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        
    async def chat(self, text: str) -> str:
        """发送消息给 Agent，返回回复"""
```

---

## 5. 信令流程

### 5.1 连接建立

```
浏览器                              后端
  |                                   |
  |-------- SDP Offer -------------->| (1)
  |                                   |
  |<------- SDP Answer --------------| (2)
  |                                   |
  |------- ICE Candidates ----------->| (3)
  |                                   |
  |<------ ICE Candidates ------------| (4)
  |                                   |
  |========= RTP 音频流 ============>| (5)
  |                                   |
  |<========= RTP 音频流 ===========| (6)
```

### 5.2 消息协议

#### WebSocket 信令消息

```json
// 客户端 → 服务端
{ "type": "offer", "sdp": "..." }
{ "type": "answer", "sdp": "..." }
{ "type": "ice-candidate", "candidate": "..." }

// 服务端 → 客户端
{ "type": "ready" }
{ "type": "error", "message": "..." }
```

---

## 6. 音频流程

### 6.1 用户说话

```
浏览器麦克风
    │
    ▼
WebRTC 编码 (Opus)
    │
    ▼
RTP 发送 (aiortc)
    │
    ▼
后端接收 RTP
    │
    ▼
阿里 STT (speech-realtime-v2)
    │
    ▼
文本
```

### 6.2 AI 说话

```
文本 (Agent 回复)
    │
    ▼
阿里 TTS (cosyvoice-v2)
    │
    ▼
音频数据
    │
    ▼
RTP 发送 (aiortc)
    │
    ▼
浏览器接收 RTP
    │
    ▼
WebRTC 解码 (Opus)
    │
    ▼
浏览器扬声器
```

---

## 7. 部署

### 7.1 端口

| 端口 | 协议 | 说明 |
|------|------|------|
| 8000 | HTTP | 信令服务器 (WebSocket) |
| 8001 | UDP | WebRTC 媒体传输 |

### 7.2 环境变量

```bash
# 阿里百炼
DASHSCOPE_API_KEY=sk-xxxx

# OpenClaw
OPENCLAW_ENDPOINT=http://localhost:8080

# 服务
LISTEN_HOST=0.0.0.0
LISTEN_PORT=8000
```

---

## 8. 待实现功能

| 优先级 | 功能 | 说明 |
|--------|------|------|
| P0 | WebRTC 连接 | 浏览器与后端建立连接 |
| P0 | 音频采集/播放 | 麦克风和扬声器 |
| P0 | STT 集成 | 阿里实时语音识别 |
| P0 | TTS 集成 | 阿里语音合成 |
| P0 | Agent 集成 | OpenClaw Agent 调用 |
| P1 | 断线重连 | 网络不稳定时 |
| P1 | 状态显示 | 正在录音/正在思考/正在说话 |
| P2 | 音量显示 | 实时音量波形 |

---

## 9. 参考项目

- **aiortc**: Python WebRTC 实现
- **AlwaysReddy**: LLM 语音助手架构参考
- **JARVIS**: 本地语音助手参考

---

## 10. 下一步

- [ ] 创建项目骨架
- [ ] 实现 WebRTC 信令服务器
- [ ] 实现 STT/TTS 服务
- [ ] 集成 OpenClaw Agent
- [ ] 前端 React 组件

---

*文档版本: 3.0*  
*最后更新: 2026-03-13*
