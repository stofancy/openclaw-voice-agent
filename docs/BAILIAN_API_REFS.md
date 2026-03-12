# 百炼 API 参考文档

_主公提供的官方文档链接_

---

## 📋 API 参考链接

### 主页面
- **API 总览**: https://bailian.console.aliyun.com/cn-beijing/?tab=api#/api

### 实时多模态相关

1. **qwen3-omni-flash-realtime (主模型)**
   - https://bailian.console.aliyun.com/cn-beijing/?type=model&url=2922854

2. **qwen3-omni-flash-realtime (音频)**
   - https://bailian.console.aliyun.com/cn-beijing/?type=model&url=2922855

3. **实时语音合成**
   - https://bailian.console.aliyun.com/cn-beijing/?type=model&url=2949956

---

## 🔧 WebSocket 端点 (已验证)

```
wss://dashscope.aliyuncs.com/api-ws/v1/realtime
```

**连接头**:
```
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

---

## 📝 事件类型 (待确认)

根据类似 OpenAI Realtime API 的设计，可能的事件类型：

### 客户端 → 服务端

| 事件类型 | 说明 |
|---------|------|
| `session.update` | 更新会话配置 |
| `conversation.item.create` | 创建对话项 |
| `conversation.item.truncate` | 截断对话 |
| `input_audio_buffer.append` | 添加音频数据 |
| `input_audio_buffer.commit` | 提交音频缓冲 |
| `input_audio_buffer.clear` | 清空音频缓冲 |
| `response.create` | 创建响应 |
| `response.cancel` | 取消响应 |

### 服务端 → 客户端

| 事件类型 | 说明 |
|---------|------|
| `session.created` | 会话已创建 |
| `session.updated` | 会话已更新 |
| `conversation.item.created` | 对话项已创建 |
| `input_audio_buffer.committed` | 音频缓冲已提交 |
| `input_audio_buffer.speech_started` | 语音开始 |
| `input_audio_buffer.speech_stopped` | 语音结束 |
| `response.created` | 响应已创建 |
| `response.output_text.done` | 文本输出完成 |
| `response.audio.done` | 音频输出完成 |
| `response.done` | 响应完成 |
| `error` | 错误 |

---

## 🎯 调用流程 (推测)

### 文本对话流程

```
1. 连接 WebSocket
   ↓
2. 接收 session.created
   ↓
3. 发送 conversation.item.create (用户消息)
   ↓
4. 发送 response.create
   ↓
5. 接收 response.created
   ↓
6. 接收 response.output_text.delta (流式文本)
   ↓
7. 接收 response.output_text.done
   ↓
8. 接收 response.done
```

### 音频对话流程

```
1. 连接 WebSocket
   ↓
2. 接收 session.created
   ↓
3. 循环发送 input_audio_buffer.append (音频数据)
   ↓
4. 接收 input_audio_buffer.speech_started
   ↓
5. 发送 input_audio_buffer.commit (或自动)
   ↓
6. 接收 input_audio_buffer.speech_stopped
   ↓
7. 自动触发 response.create (如果 configured)
   ↓
8. 接收 response.output_text.done
   ↓
9. 接收 response.audio.delta (流式音频)
   ↓
10. 接收 response.audio.done
   ↓
11. 接收 response.done
```

---

## ⚠️ 待确认事项

### 1. 正确的消息格式

需要查看主公提供的文档中的代码示例：

```json
// 可能的格式 A
{
  "type": "conversation.item.create",
  "item": {
    "type": "message",
    "role": "user",
    "content": [{"type": "text", "text": "你好"}]
  }
}

// 可能的格式 B
{
  "type": "input_text",
  "text": "你好"
}

// 可能的格式 C
{
  "type": "user_message",
  "content": "你好"
}
```

### 2. 响应格式

```json
// 可能的响应
{
  "type": "response.output_text.done",
  "output": "你好！有什么可以帮助你的？"
}

// 或
{
  "type": "response.done",
  "response": {
    "output": "你好！有什么可以帮助你的？"
  }
}
```

### 3. 音频格式

- **输入**: PCM16 (16kHz, 16-bit, 单声道) ✅ 已确认
- **输出**: PCM24 (24kHz, ?-bit) ✅ 已确认

---

## 📎 下一步

1. **主公查看文档中的代码示例**
2. **告诉我正确的**:
   - 消息格式
   - 事件类型
   - 调用流程
3. **我更新测试代码**
4. **重新测试**

---

_等待主公提供文档详情..._
