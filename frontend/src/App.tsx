import { useState, useEffect, useRef, useCallback } from 'react'
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

// 性能优化：配置常量
const CONFIG = {
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,
  MAX_LOGS: 99,
  MAX_SUBTITLES: 10,
  WS_URL: 'ws://localhost:8765',
} as const

function App() {
  // 核心状态管理
  const [callState, setCallState] = useState<CallState>('idle')
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [isMuted, setIsMuted] = useState<boolean>(false)
  const [errorMessage, setErrorMessage] = useState<string>('')
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [subtitles, setSubtitles] = useState<Subtitle[]>([])
  const [retryCount, setRetryCount] = useState<number>(0)
  
  // WebSocket 引用
  const wsRef = useRef<WebSocket | null>(null)
  const subtitleIdRef = useRef<number>(0)
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null)
  const retryCountRef = useRef<number>(0)

  // 添加日志 - 性能优化：使用 useCallback 避免重创建
  const addLog = useCallback((level: 'info' | 'warn' | 'error', message: string) => {
    setLogs(prev => {
      const newLogs = [...prev, {
        id: Date.now(),
        level,
        message,
        timestamp: new Date().toISOString()
      }]
      // 限制日志数量，避免内存泄漏
      return newLogs.slice(-CONFIG.MAX_LOGS)
    })
  }, [])

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

  // 连接 WebSocket - 增强错误处理 + 自动重试
  const connectWebSocket = useCallback(() => {
    // 清理之前的重连定时器
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
    
    setCallState('connecting')
    setErrorMessage('')
    
    try {
      const websocket = new WebSocket(CONFIG.WS_URL)
      
      websocket.onopen = () => {
        setIsConnected(true)
        setCallState('listening')
        setRetryCount(0)
        retryCountRef.current = 0
        addLog('info', '✅ WebSocket 已连接')
        wsRef.current = websocket
      }
      
      websocket.onclose = (event) => {
        setIsConnected(false)
        wsRef.current = null
        
        // 网络断开重连逻辑（自动重试 3 次）
        if (retryCountRef.current < CONFIG.MAX_RETRIES && callState !== 'idle') {
          retryCountRef.current += 1
          setRetryCount(retryCountRef.current)
          
          const delay = CONFIG.RETRY_DELAY * retryCountRef.current
          addLog('warn', `🔄 网络断开，${delay/1000}s 后重试 (${retryCountRef.current}/${CONFIG.MAX_RETRIES})`)
          
          reconnectTimerRef.current = setTimeout(() => {
            addLog('info', `🔄 第 ${retryCountRef.current} 次重连...`)
            connectWebSocket()
          }, delay)
        } else {
          setCallState('idle')
          if (retryCountRef.current >= CONFIG.MAX_RETRIES) {
            setErrorMessage('连接失败，已达最大重试次数')
            addLog('error', `❌ 重连失败 ${CONFIG.MAX_RETRIES} 次，请手动重试`)
          } else {
            addLog('warn', '⚠️ WebSocket 已断开')
          }
        }
      }
      
      websocket.onerror = (error) => {
        setCallState('error')
        setErrorMessage('连接错误')
        addLog('error', '❌ WebSocket 错误')
        console.error('WebSocket error:', error)
      }
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          // 错误处理：后端发送的错误消息
          if (data.type === 'error') {
            const errorMsg = data.message || '未知错误'
            addLog('error', `❌ ${errorMsg}`)
            
            if (data.recoverable) {
              setErrorMessage(`${errorMsg} (可自动恢复)`)
            } else {
              setErrorMessage(errorMsg)
            }
            return
          }
          
          // TTS 降级处理：显示文本提示
          if (data.type === 'tts_fallback') {
            addLog('warn', `📝 TTS 降级：${data.reason}`)
            setSubtitles(prev => {
              const newSubtitles = [...prev, {
                id: subtitleIdRef.current++,
                role: 'ai',
                text: data.text || '',
                isFinal: true,
                timestamp: new Date().toISOString()
              }]
              // 限制字幕数量，避免内存泄漏
              return newSubtitles.slice(-CONFIG.MAX_SUBTITLES)
            })
            return
          }
          
          addLog('info', `📥 收到：${data.type}`)
          
          // STT 增量结果
          if (data.type === 'stt_partial' && data.text) {
            setCallState('listening')
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'user' && !s.isFinal)
              if (lastIndex !== -1) {
                const updated = [...prev]
                updated[lastIndex] = { ...updated[lastIndex], text: data.text, isFinal: false }
                return updated.slice(-CONFIG.MAX_SUBTITLES)
              }
              const newSubtitles = [...prev, {
                id: subtitleIdRef.current++,
                role: 'user',
                text: data.text,
                isFinal: false,
                timestamp: data.timestamp ?? new Date().toISOString()
              }]
              return newSubtitles.slice(-CONFIG.MAX_SUBTITLES)
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
                return updated.slice(-CONFIG.MAX_SUBTITLES)
              }
              const newSubtitles = [...prev, {
                id: subtitleIdRef.current++,
                role: 'user',
                text: data.text,
                isFinal: true,
                timestamp: data.timestamp ?? new Date().toISOString()
              }]
              return newSubtitles.slice(-CONFIG.MAX_SUBTITLES)
            })
          }
          
          // LLM 流式 token
          if (data.type === 'llm_token' && data.token) {
            setCallState('speaking')
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'ai' && !s.isFinal)
              if (lastIndex !== -1) {
                const updated = [...prev]
                updated[lastIndex] = { 
                  ...updated[lastIndex], 
                  text: updated[lastIndex].text + data.token,
                  isFinal: false 
                }
                return updated.slice(-CONFIG.MAX_SUBTITLES)
              }
              const newSubtitles = [...prev, {
                id: subtitleIdRef.current++,
                role: 'ai',
                text: data.token,
                isFinal: false,
                timestamp: data.timestamp ?? new Date().toISOString()
              }]
              return newSubtitles.slice(-CONFIG.MAX_SUBTITLES)
            })
          }
          
          // LLM 完整回复
          if (data.type === 'llm_complete' && data.text) {
            setSubtitles(prev => {
              const lastIndex = prev.findIndex(s => s.role === 'ai' && !s.isFinal)
              if (lastIndex !== -1) {
                const updated = [...prev]
                updated[lastIndex] = { ...updated[lastIndex], text: data.text, isFinal: true }
                return updated.slice(-CONFIG.MAX_SUBTITLES)
              }
              const newSubtitles = [...prev, {
                id: subtitleIdRef.current++,
                role: 'ai',
                text: data.text,
                isFinal: true,
                timestamp: data.timestamp ?? new Date().toISOString()
              }]
              return newSubtitles.slice(-CONFIG.MAX_SUBTITLES)
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
                return updated.slice(-CONFIG.MAX_SUBTITLES)
              }
              return prev.slice(-CONFIG.MAX_SUBTITLES)
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
            setSubtitles(prev => {
              const newSubtitles = [...prev, {
                id: subtitleIdRef.current++,
                role: 'ai',
                text: data.text,
                isFinal: true,
                timestamp: new Date().toISOString()
              }]
              return newSubtitles.slice(-CONFIG.MAX_SUBTITLES)
            })
          }
          
          if (data.type === 'stt_result' && data.text) {
            setSubtitles(prev => {
              const newSubtitles = [...prev, {
                id: subtitleIdRef.current++,
                role: 'user',
                text: data.text,
                isFinal: true,
                timestamp: new Date().toISOString()
              }]
              return newSubtitles.slice(-CONFIG.MAX_SUBTITLES)
            })
          }
        } catch (parseError) {
          addLog('warn', `解析失败：${parseError instanceof Error ? parseError.message : '未知'}`)
        }
      }
      
    } catch (error) {
      setCallState('error')
      setErrorMessage(error instanceof Error ? error.message : '连接失败')
      addLog('error', `连接失败：${error}`)
    }
  }, [addLog, callState])

  // 断开连接 - 清理重连定时器
  const disconnectWebSocket = useCallback(() => {
    // 清理重连定时器
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setIsConnected(false)
    setCallState('idle')
    setRetryCount(0)
    retryCountRef.current = 0
    setSubtitles(prev => prev.slice(-CONFIG.MAX_SUBTITLES))
    addLog('info', '已断开连接')
  }, [addLog])

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

  // 组件卸载时清理 - 防止内存泄漏
  useEffect(() => {
    return () => {
      // 清理 WebSocket
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      // 清理重连定时器
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
    }
  }, [])

  return (
    <div className="app">
      {/* 顶部状态栏 */}
      <header className="status-bar">
        <div className={`status-indicator ${callState}`}>
          {getStatusText()}
          {retryCount > 0 && (
            <span className="retry-badge">重试 {retryCount}/{CONFIG.MAX_RETRIES}</span>
          )}
        </div>
      </header>

      {/* 中央语音动画区域 - GPU 加速优化 */}
      <main className="voice-container">
        <div className={`voice-animation ${callState}`}>
          <div className="voice-circle gpu-accelerated">
            <div className="voice-ring ring-1 gpu-accelerated"></div>
            <div className="voice-ring ring-2 gpu-accelerated"></div>
            <div className="voice-ring ring-3 gpu-accelerated"></div>
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

        {/* 错误提示 - 友好错误消息 */}
        {callState === 'error' && errorMessage && (
          <div className="error-banner gpu-accelerated">
            <span className="error-icon">⚠️</span>
            <span className="error-message">{errorMessage}</span>
            <button 
              className="error-dismiss"
              onClick={() => setErrorMessage('')}
            >
              ✕
            </button>
          </div>
        )}

        {/* 实时字幕 - 渲染优化 */}
        {subtitles.length > 0 && (
          <div className="subtitle-overlay">
            <div className="subtitles-scroll">
              {subtitles.slice(-3).map(subtitle => (
                <div 
                  key={subtitle.id} 
                  className={`subtitle-item ${subtitle.role} ${subtitle.isFinal ? 'final' : 'streaming'} gpu-accelerated`}
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
