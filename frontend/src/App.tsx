import { useState, useEffect, useRef } from 'react'
import './App.css'

// 定义状态类型
type CallState = 'idle' | 'connecting' | 'listening' | 'processing' | 'speaking' | 'error'

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
  // 核心状态管理
  const [callState, setCallState] = useState<CallState>('idle')
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [isMuted, setIsMuted] = useState<boolean>(false)
  const [errorMessage, setErrorMessage] = useState<string>('')
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [subtitles, setSubtitles] = useState<Subtitle[]>([])
  
  // WebSocket 引用
  const wsRef = useRef<WebSocket | null>(null)
  const subtitleIdRef = useRef<number>(0)

  // 添加日志
  const addLog = (level: 'info' | 'warn' | 'error', message: string) => {
    setLogs(prev => [...prev.slice(-99), {
      id: Date.now(),
      level,
      message,
      timestamp: new Date().toISOString()
    }])
  }

  // 获取状态显示文本
  const getStatusText = (): string => {
    switch (callState) {
      case 'idle': return '准备就绪'
      case 'connecting': return '🟢 连接中'
      case 'listening': return '🎤 说话中'
      case 'processing': return '⚙️ 处理中'
      case 'speaking': return '🤖 AI 回复'
      case 'error': return `❌ ${errorMessage}`
      default: return '未知状态'
    }
  }

  // 连接 WebSocket
  const connectWebSocket = () => {
    setCallState('connecting')
    setErrorMessage('')
    
    try {
      const websocket = new WebSocket('ws://localhost:8765')
      
      websocket.onopen = () => {
        setIsConnected(true)
        setCallState('listening')
        addLog('info', '✅ WebSocket 已连接')
        wsRef.current = websocket
      }
      
      websocket.onclose = () => {
        setIsConnected(false)
        setCallState('idle')
        addLog('warn', '⚠️ WebSocket 已断开')
        wsRef.current = null
      }
      
      websocket.onerror = () => {
        setCallState('error')
        setErrorMessage('连接错误')
        addLog('error', '❌ WebSocket 错误')
      }
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          addLog('info', `📥 收到：${data.type}`)
          
          // STT 增量结果
          if (data.type === 'stt_partial' && data.text) {
            setCallState('listening')
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'user' && !s.isFinal)
              if (lastIndex !== -1) {
                const updated = [...prev]
                updated[lastIndex] = { ...updated[lastIndex], text: data.text, isFinal: false }
                return updated
              }
              return [...prev, {
                id: subtitleIdRef.current++,
                role: 'user',
                text: data.text,
                isFinal: false,
                timestamp: data.timestamp ?? new Date().toISOString()
              }]
            })
          }
          
          // STT 最终结果
          if (data.type === 'stt_final' && data.text) {
            setCallState('processing')
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'user' && !s.isFinal)
              if (lastIndex !== -1) {
                const updated = [...prev]
                updated[lastIndex] = { ...updated[lastIndex], text: data.text, isFinal: true }
                return updated
              }
              return [...prev, {
                id: subtitleIdRef.current++,
                role: 'user',
                text: data.text,
                isFinal: true,
                timestamp: data.timestamp ?? new Date().toISOString()
              }]
            })
          }
          
          // LLM 流式 token
          if (data.type === 'llm_token' && data.text) {
            setCallState('speaking')
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'ai' && !s.isFinal)
              if (lastIndex !== -1) {
                const updated = [...prev]
                updated[lastIndex] = { 
                  ...updated[lastIndex], 
                  text: updated[lastIndex].text + data.text,
                  isFinal: false 
                }
                return updated
              }
              return [...prev, {
                id: subtitleIdRef.current++,
                role: 'ai',
                text: data.text,
                isFinal: false,
                timestamp: data.timestamp ?? new Date().toISOString()
              }]
            })
          }
          
          // LLM 完整回复
          if (data.type === 'llm_complete' && data.text) {
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'ai' && !s.isFinal)
              if (lastIndex !== -1) {
                const updated = [...prev]
                updated[lastIndex] = { ...updated[lastIndex], text: data.text, isFinal: true }
                return updated
              }
              return [...prev, {
                id: subtitleIdRef.current++,
                role: 'ai',
                text: data.text,
                isFinal: true,
                timestamp: data.timestamp ?? new Date().toISOString()
              }]
            })
          }
          
          // TTS 开始播放
          if (data.type === 'tts_start') {
            setCallState('speaking')
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
          
          // TTS 播放结束
          if (data.type === 'tts_end') {
            setCallState('listening')
            addLog('info', '✅ TTS 播放结束')
          }
          
          // 兼容旧格式
          if (data.type === 'reply' && data.text) {
            setCallState('speaking')
            setSubtitles(prev => [...prev, {
              id: subtitleIdRef.current++,
              role: 'ai',
              text: data.text,
              isFinal: true,
              timestamp: new Date().toISOString()
            }])
          }
          
          if (data.type === 'stt_result' && data.text) {
            setSubtitles(prev => [...prev, {
              id: subtitleIdRef.current++,
              role: 'user',
              text: data.text,
              isFinal: true,
              timestamp: new Date().toISOString()
            }])
          }
        } catch {
          addLog('warn', `原始消息：${event.data}`)
        }
      }
      
    } catch (error) {
      setCallState('error')
      setErrorMessage(error instanceof Error ? error.message : '连接失败')
      addLog('error', `连接失败：${error}`)
    }
  }

  // 断开连接
  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      setIsConnected(false)
      setCallState('idle')
      setSubtitles([])
      addLog('info', '已断开连接')
    }
  }

  // 切换静音
  const toggleMic = () => {
    setIsMuted(!isMuted)
    addLog('info', isMuted ? '取消静音' : '已静音')
  }

  // 错误恢复
  const retryConnection = () => {
    setCallState('idle')
    setErrorMessage('')
    connectWebSocket()
  }

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  return (
    <div className="app">
      {/* 顶部状态栏 */}
      <header className="status-bar">
        <div className={`status-indicator ${callState}`}>
          {getStatusText()}
        </div>
      </header>

      {/* 中央语音动画区域 */}
      <main className="voice-container">
        <div className={`voice-animation ${callState}`}>
          <div className="voice-circle">
            <div className="voice-ring ring-1"></div>
            <div className="voice-ring ring-2"></div>
            <div className="voice-ring ring-3"></div>
            <div className="voice-icon">
              {callState === 'listening' && '🎤'}
              {callState === 'speaking' && '🤖'}
              {callState === 'processing' && '⚙️'}
              {callState === 'connecting' && '🟢'}
              {callState === 'error' && '❌'}
              {callState === 'idle' && '📞'}
            </div>
          </div>
        </div>

        {/* 实时字幕 */}
        {subtitles.length > 0 && (
          <div className="subtitle-overlay">
            <div className="subtitles-scroll">
              {subtitles.slice(-3).map(subtitle => (
                <div 
                  key={subtitle.id} 
                  className={`subtitle-item ${subtitle.role} ${subtitle.isFinal ? 'final' : 'streaming'}`}
                >
                  <span className="subtitle-role">
                    {subtitle.role === 'user' ? '👤' : '🤖'}
                  </span>
                  <span className="subtitle-text">{subtitle.text}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* 底部控制栏 */}
      <footer className="controls-bar">
        {!isConnected ? (
          <button 
            className="control-btn btn-connect" 
            onClick={connectWebSocket}
            disabled={callState === 'connecting'}
          >
            <span className="btn-icon">📞</span>
            <span className="btn-text">
              {callState === 'connecting' ? '连接中...' : '开始通话'}
            </span>
          </button>
        ) : (
          <>
            <button 
              className={`control-btn btn-mic ${isMuted ? 'muted' : ''}`} 
              onClick={toggleMic}
            >
              <span className="btn-icon">{isMuted ? '🎤' : '🔇'}</span>
              <span className="btn-text">{isMuted ? '取消静音' : '静音'}</span>
            </button>
            
            <button 
              className="control-btn btn-hangup" 
              onClick={disconnectWebSocket}
            >
              <span className="btn-icon">📴</span>
              <span className="btn-text">挂断</span>
            </button>
            
            {callState === 'error' && (
              <button 
                className="control-btn btn-retry" 
                onClick={retryConnection}
              >
                <span className="btn-icon">🔄</span>
                <span className="btn-text">重试</span>
              </button>
            )}
          </>
        )}
      </footer>

      {/* 日志面板（可折叠） */}
      <details className="logs-panel">
        <summary>📋 日志 ({logs.length})</summary>
        <div className="logs">
          {logs.map(log => (
            <div key={log.id} className={`log ${log.level}`}>
              <span className="log-time">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span className="log-msg">{log.message}</span>
            </div>
          ))}
        </div>
      </details>
    </div>
  )
}

export default App
