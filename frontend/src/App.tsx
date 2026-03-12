import { useState, useEffect } from 'react'
import './App.css'

interface LogEntry {
  id: number
  level: 'info' | 'warn' | 'error'
  message: string
  timestamp: string
}

function App() {
  const [status, setStatus] = useState<string>('准备就绪')
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [isMuted, setIsMuted] = useState<boolean>(false)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)
  
  // 使用 useRef 避免在 effect 中依赖 ws
  const wsRef = ws

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
      }
      
      websocket.onclose = () => {
        setIsConnected(false)
        addLog('warn', '⚠️ WebSocket 已断开')
        setStatus('已断开')
      }
      
      websocket.onerror = () => {
        addLog('error', '❌ WebSocket 错误')
        setStatus('连接错误')
      }
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          addLog('info', `📥 收到：${data.type}`)
          
          if (data.type === 'reply' && data.text) {
            setStatus(`🤖 Agent: ${data.text}`)
          }
        } catch {
          addLog('warn', `原始消息：${event.data}`)
        }
      }
      
      setWs(websocket)
    } catch (error) {
      addLog('error', `连接失败：${error}`)
    }
  }

  const disconnectWebSocket = () => {
    if (ws) {
      ws.close()
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
      if (wsRef) wsRef.close()
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
