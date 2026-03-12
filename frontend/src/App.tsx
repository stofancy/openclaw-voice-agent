import { useState, useEffect, useRef } from 'react'
import './App.css'

interface LogEntry {
  id: number
  level: 'info' | 'warn' | 'error'
  message: string
  timestamp: string
}

interface Subtitle {
  id: number
  role: 'user' | 'ai'
  text: string
  isFinal: boolean
  timestamp: string
}

function App() {
  const [status, setStatus] = useState<string>('准备就绪')
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [isMuted, setIsMuted] = useState<boolean>(false)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [subtitles, setSubtitles] = useState<Subtitle[]>([])
  
  // 使用 useRef 避免在 effect 中依赖 ws
  const wsRef = useRef<WebSocket | null>(null)
  const subtitleIdRef = useRef<number>(0)

  const addLog = (level: 'info' | 'warn' | 'error', message: string) => {
    setLogs(prev => [...prev.slice(-99), {
      id: Date.now(),
      level,
      message,
      timestamp: new Date().toISOString()
    }])
  }

  const connectWebSocket = () => {
    try {
      const websocket = new WebSocket('ws://localhost:8765')
      
      websocket.onopen = () => {
        setIsConnected(true)
        addLog('info', '✅ WebSocket 已连接')
        setStatus('已连接')
        wsRef.current = websocket
        setWs(websocket)
      }
      
      websocket.onclose = () => {
        setIsConnected(false)
        addLog('warn', '⚠️ WebSocket 已断开')
        setStatus('已断开')
        wsRef.current = null
        setWs(null)
      }
      
      websocket.onerror = () => {
        addLog('error', '❌ WebSocket 错误')
        setStatus('连接错误')
      }
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          addLog('info', `📥 收到：${data.type}`)
          
          // ========== 新消息类型（授权格式）==========
          
          // STT 增量结果（用户字幕 - 流式）
          if (data.type === 'stt_partial' && data.text) {
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'user' && !s.isFinal)
              if (lastIndex !== -1) {
                // 更新现有字幕
                const updated = [...prev]
                updated[lastIndex] = { ...updated[lastIndex], text: data.text, isFinal: false }
                return updated
              } else {
                // 添加新字幕
                return [...prev, {
                  id: subtitleIdRef.current++,
                  role: 'user',
                  text: data.text,
                  isFinal: false,
                  timestamp: data.timestamp ?? new Date().toISOString()
                }]
              }
            })
          }
          
          // STT 最终结果（用户字幕 - 确认）
          if (data.type === 'stt_final' && data.text) {
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'user' && !s.isFinal)
              if (lastIndex !== -1) {
                // 更新现有字幕为最终状态
                const updated = [...prev]
                updated[lastIndex] = { ...updated[lastIndex], text: data.text, isFinal: true }
                return updated
              } else {
                // 添加新字幕
                return [...prev, {
                  id: subtitleIdRef.current++,
                  role: 'user',
                  text: data.text,
                  isFinal: true,
                  timestamp: data.timestamp ?? new Date().toISOString()
                }]
              }
            })
          }
          
          // LLM 流式 token（AI 字幕 - 打字机效果）
          if (data.type === 'llm_token' && data.text) {
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'ai' && !s.isFinal)
              if (lastIndex !== -1) {
                // 追加 token 到现有字幕
                const updated = [...prev]
                updated[lastIndex] = { 
                  ...updated[lastIndex], 
                  text: updated[lastIndex].text + data.text,
                  isFinal: false 
                }
                return updated
              } else {
                // 添加新字幕
                return [...prev, {
                  id: subtitleIdRef.current++,
                  role: 'ai',
                  text: data.text,
                  isFinal: false,
                  timestamp: data.timestamp ?? new Date().toISOString()
                }]
              }
            })
          }
          
          // LLM 完整回复（AI 字幕 - 完成）
          if (data.type === 'llm_complete' && data.text) {
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'ai' && !s.isFinal)
              if (lastIndex !== -1) {
                // 更新现有字幕为最终状态
                const updated = [...prev]
                updated[lastIndex] = { ...updated[lastIndex], text: data.text, isFinal: true }
                return updated
              } else {
                // 添加新字幕
                return [...prev, {
                  id: subtitleIdRef.current++,
                  role: 'ai',
                  text: data.text,
                  isFinal: true,
                  timestamp: data.timestamp ?? new Date().toISOString()
                }]
              }
            })
          }
          
          // TTS 开始播放（字幕高亮）
          if (data.type === 'tts_start') {
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'ai' && !s.isFinal)
              if (lastIndex !== -1) {
                const updated = [...prev]
                updated[lastIndex] = { ...updated[lastIndex], isFinal: true }
                return updated
              }
              return prev
            })
            addLog('info', '🔊 TTS 开始播放')
          }
          
          // TTS 播放结束（取消高亮）
          if (data.type === 'tts_end') {
            addLog('info', '✅ TTS 播放结束')
          }
          
          // ========== 兼容旧格式 ==========
          
          // 处理回复事件（兼容旧格式）
          if (data.type === 'reply' && data.text) {
            setStatus(`🤖 Agent: ${data.text}`)
            // 也添加为 AI 字幕
            setSubtitles(prev => [...prev, {
              id: subtitleIdRef.current++,
              role: 'ai',
              text: data.text,
              isFinal: true,
              timestamp: new Date().toISOString()
            }])
          }
          
          // 处理 STT 结果（兼容旧格式）
          if (data.type === 'stt_result' && data.text) {
            setSubtitles(prev => [...prev, {
              id: subtitleIdRef.current++,
              role: 'user',
              text: data.text,
              isFinal: true,
              timestamp: new Date().toISOString()
            }])
          }
          
          // 处理字幕事件（兼容旧格式）
          if (data.type === 'subtitle') {
            const { role, text, is_final, timestamp } = data
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === role && !s.isFinal)
              if (lastIndex !== -1) {
                const updated = [...prev]
                if (is_final) {
                  updated[lastIndex] = { ...updated[lastIndex], text, isFinal: true }
                } else {
                  updated[lastIndex] = { ...updated[lastIndex], text }
                }
                return updated
              } else {
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
        } catch {
          addLog('warn', `原始消息：${event.data}`)
        }
      }
      
    } catch (error) {
      addLog('error', `连接失败：${error}`)
    }
  }

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      setWs(null)
      addLog('info', '已断开连接')
    }
  }

  const testMic = async () => {
    try {
      setStatus('正在请求麦克风权限...')
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      setStatus('✅ 麦克风工作正常！')
      addLog('info', '麦克风测试成功')
      
      // 停止所有轨道
      stream.getTracks().forEach(track => track.stop())
    } catch (error) {
      setStatus(`❌ 麦克风失败：${error}`)
      addLog('error', `麦克风错误：${error}`)
    }
  }

  const testSpeaker = () => {
    setStatus('正在播放测试音...')
    addLog('info', '播放测试音')
    
    const audioContext = new AudioContext()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)
    
    oscillator.frequency.value = 440
    oscillator.type = 'sine'
    gainNode.gain.value = 0.3
    
    oscillator.start()
    
    setTimeout(() => {
      oscillator.stop()
      setStatus('✅ 扬声器工作正常！')
      addLog('info', '扬声器测试成功')
    }, 1000)
  }

  const toggleMic = () => {
    setIsMuted(!isMuted)
    addLog('info', isMuted ? '取消静音' : '已静音')
  }

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      addLog('info', '应用已加载')
    }, 0)
    
    return () => {
      clearTimeout(timeoutId)
      if (wsRef.current) wsRef.current.close()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="app">
      <header>
        <h1>🎤 AI 语音通话</h1>
        <p>基于 WebRTC + WebSocket</p>
      </header>

      <main>
        <section className="status-section">
          <div className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
            {status}
          </div>
        </section>

        {/* 流式字幕区域 */}
        <section className="subtitle-section">
          <h2>📝 实时字幕</h2>
          <div className="subtitles">
            {subtitles.length === 0 ? (
              <div className="subtitle-empty">暂无字幕</div>
            ) : (
              subtitles.map(subtitle => (
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
              ))
            )}
          </div>
        </section>

        <section className="controls">
          {!isConnected ? (
            <button className="btn btn-connect" onClick={connectWebSocket}>
              📞 连接
            </button>
          ) : (
            <>
              <button className="btn btn-hangup" onClick={disconnectWebSocket}>
                📴 挂断
              </button>
              <button className="btn btn-mic" onClick={toggleMic}>
                {isMuted ? '🎤 取消静音' : '🔇 静音'}
              </button>
            </>
          )}
        </section>

        <section className="test-section">
          <h2>硬件测试</h2>
          <div className="test-buttons">
            <button onClick={testMic}>测试麦克风</button>
            <button onClick={testSpeaker}>测试扬声器</button>
          </div>
        </section>

        <section className="logs-section">
          <h2>日志 ({logs.length})</h2>
          <div className="logs">
            {logs.map(log => (
              <div key={log.id} className={`log ${log.level}`}>
                <span className="timestamp">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="message">{log.message}</span>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
