# 阶段一实现总结：流式 STT + 实时字幕

**完成时间**: 2026-03-12  
**状态**: ✅ 已完成

---

## 🎯 实现目标

- ✅ 后端：STT 增量结果通过 WebSocket 实时推送给前端
- ✅ 前端：React 组件实时接收并显示字幕
- ✅ 效果：用户说话时，字幕实时出现（边说话边显示）
- ✅ AI 回复：同时支持字幕显示

---

## 📝 修改内容

### 后端修改 (`wsl2/agent-gateway.py`)

#### 1. STT 回调增强
```python
class STTCallback(ASRRealtimeCallback):
    def on_event(self, response: str) -> None:
        # 增量识别结果（流式）
        elif event_type == 'recognizer.result.increment':
            text = data.get('result', {}).get('text', '')
            # 流式推送给前端（实时字幕）
            if self.gateway:
                asyncio.create_task(self.gateway.send_subtitle_to_clients(text, 'user', is_final=False))
        
        # 完成识别结果
        elif event_type == 'recognizer.result.completed':
            text = data.get('result', {}).get('text', '')
            # 推送最终结果给前端
            if self.gateway:
                asyncio.create_task(self.gateway.send_subtitle_to_clients(text, 'user', is_final=True))
```

#### 2. 新增字幕推送方法
```python
async def send_subtitle_to_clients(self, text: str, role: str, is_final: bool = False) -> None:
    """发送字幕到客户端（流式）
    
    Args:
        text: 字幕文本
        role: 角色 ('user' 或 'ai')
        is_final: 是否为最终结果
    """
    await self.send_to_clients_async({
        "type": "subtitle",
        "role": role,
        "text": text,
        "is_final": is_final,
        "timestamp": datetime.now().isoformat()
    })
```

#### 3. AI 回复字幕支持
```python
# 发送 Agent 回复 (兼容旧格式 + 新字幕格式)
await self.send_to_clients_async({
    "type": "reply",
    "text": reply
})
# 同时发送 AI 字幕
await self.send_subtitle_to_clients(reply, 'ai', is_final=True)
```

---

### 前端修改 (`frontend/src/App.tsx`)

#### 1. 新增字幕接口
```typescript
interface Subtitle {
  id: number
  role: 'user' | 'ai'
  text: string
  isFinal: boolean
  timestamp: string
}
```

#### 2. WebSocket 消息处理
```typescript
// 处理字幕事件（流式 STT/LLM）
if (data.type === 'subtitle') {
  const { role, text, is_final, timestamp } = data
  setSubtitles(prev => {
    // 查找相同角色的最后一条字幕
    const lastIndex = prev.findIndex(s => s.role === role && !s.isFinal)
    if (lastIndex !== -1) {
      // 更新现有字幕
      const updated = [...prev]
      if (is_final) {
        updated[lastIndex] = { ...updated[lastIndex], text, isFinal: true }
      } else {
        updated[lastIndex] = { ...updated[lastIndex], text }
      }
      return updated
    } else {
      // 添加新字幕
      return [...prev, {
        id: subtitleIdRef.current++,
        role,
        text,
        isFinal: is_final ?? false,
        timestamp: timestamp ?? new Date().toISOString()
      }]
    }
  })
}
```

#### 3. 字幕 UI 组件
```tsx
<section className="subtitle-section">
  <h2>📝 实时字幕</h2>
  <div className="subtitles">
    {subtitles.map(subtitle => (
      <div 
        key={subtitle.id} 
        className={`subtitle ${subtitle.role} ${subtitle.isFinal ? 'final' : 'streaming'}`}
      >
        <span className="subtitle-role">
          {subtitle.role === 'user' ? '👤 你' : '🤖 AI'}
        </span>
        <span className="subtitle-text">
          {subtitle.text}
          {!subtitle.isFinal && <span className="cursor">▋</span>}
        </span>
      </div>
    ))}
  </div>
</section>
```

---

### 样式修改 (`frontend/src/App.css`)

新增字幕样式：
- `.subtitle-section` - 字幕区域容器
- `.subtitle.user` - 用户字幕（蓝色主题）
- `.subtitle.ai` - AI 字幕（绿色主题）
- `.subtitle.streaming` - 流式字幕（脉冲动画）
- `.cursor` - 光标闪烁动画

---

## 📊 字幕消息格式

### WebSocket 消息类型：`subtitle`

```json
{
  "type": "subtitle",
  "role": "user",
  "text": "你好，我想查询",
  "is_final": false,
  "timestamp": "2026-03-12T21:30:00.000Z"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | 固定为 `"subtitle"` |
| `role` | string | 角色：`"user"` 或 `"ai"` |
| `text` | string | 字幕文本内容 |
| `is_final` | boolean | 是否为最终结果 |
| `timestamp` | string | ISO 8601 时间戳 |

---

## 🎬 工作流程

### 用户说话流程
```
1. 用户说话 → 麦克风采集音频
2. 音频流 → VAD 检测 → 发送 STT
3. STT 增量识别 → 推送字幕 (is_final=false)
4. 前端实时更新用户字幕（带光标闪烁）
5. 说话结束 → STT 最终结果 → 推送字幕 (is_final=true)
6. 前端标记字幕为最终状态
```

### AI 回复流程
```
1. STT 完成 → 发送 Agent
2. Agent 回复 → 推送 AI 字幕 (is_final=true)
3. 前端显示 AI 字幕（绿色主题）
4. 同时播放 TTS 音频
```

---

## 🧪 测试方法

### 1. 启动网关
```bash
cd ~/workspaces/audio-proxy/wsl2
python3 agent-gateway.py
```

### 2. 构建并启动前端
```bash
cd ~/workspaces/audio-proxy/frontend
npm run build
npm run preview  # 或部署到 Web 服务器
```

### 3. 打开浏览器
访问：http://localhost:4173（或部署地址）

### 4. 测试步骤
1. 点击"📞 连接"按钮
2. 允许麦克风权限
3. 说话测试字幕显示
4. 观察字幕实时更新效果

---

## ✅ 验收标准

- [x] 用户说话时，字幕实时出现（增量更新）
- [x] 字幕带流式光标效果（▋闪烁）
- [x] 说话结束后，字幕标记为最终状态
- [x] AI 回复时，显示 AI 字幕（绿色主题）
- [x] 用户/AI 字幕视觉区分明显
- [x] 兼容旧格式消息（reply, stt_result）

---

## 🔄 下一步：阶段二

**流式 LLM + AI 字幕打字机效果**

目标：
- AI 回复流式返回（非完整文本）
- 前端打字机效果逐字显示
- 字幕与 TTS 音频同步

---

_阶段一完成，等待主公检阅后进入阶段二_
