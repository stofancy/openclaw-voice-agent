import { useState, useEffect } from 'react';
import './App.css';
import { useWebRTC } from './hooks/useWebRTC';
import { VoiceConnectionStatus } from './components/VoiceConnectionStatus';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { useAudioPlayer } from './hooks/useAudioPlayer';
import { AudioVolumeIndicator } from './components/AudioVolumeIndicator';

type ConversationStatus = 'idle' | 'recording' | 'thinking' | 'playing';

function App() {
  const [webRTCState, webRTCActions] = useWebRTC('ws://localhost:8080');
  const {
    isRecording,
    hasPermission,
    error: recorderError,
    requestPermission,
    startRecording,
    stopRecording,
    mediaStream
  } = useAudioRecorder();
  
  const [playerState, playerActions] = useAudioPlayer();
  const { status: playerStatus, error: playerError } = playerState;
  
  const [conversationStatus, setConversationStatus] = useState<ConversationStatus>('idle');
  
  const handleRetry = () => {
    webRTCActions.connect();
  };

  // Auto-request microphone permission when connected
  useEffect(() => {
    if (webRTCState.isConnected && hasPermission === null) {
      requestPermission();
    }
  }, [webRTCState.isConnected, hasPermission, requestPermission]);

  const handleStartRecording = async () => {
    if (hasPermission === null) {
      await requestPermission();
    }
    if (hasPermission) {
      startRecording();
      setConversationStatus('recording');
    }
  };

  const handleStopRecording = async () => {
    const audioBlob = await stopRecording();
    setConversationStatus('thinking');
    
    // Send audio to backend for STT processing
    if (audioBlob && webRTCState.isConnected) {
      try {
        // Convert blob to base64
        const arrayBuffer = await audioBlob.arrayBuffer();
        const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
        
        // Send via WebSocket to backend for STT -> Agent -> TTS
        webRTCActions.sendAudioData(base64, 'webm');
      } catch (err) {
        console.error('Failed to send audio:', err);
      }
    }
  };

  // Handle audio playback status changes
  useEffect(() => {
    if (playerStatus === 'playing') {
      setConversationStatus('playing');
    } else if (playerStatus === 'idle') {
      setConversationStatus('idle');
    } else if (playerError) {
      setConversationStatus('idle');
    }
  }, [playerStatus, playerError]);

  // Set up listener for AI audio responses
  useEffect(() => {
    if (!webRTCState.isConnected) return;
    
    // Use the onAiResponse callback from useWebRTC
    webRTCActions.onAiResponse(async (audioData: string, _turnId: number) => {
      try {
        // Convert base64 to audio blob
        const binaryString = atob(audioData);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const audioBlob = new Blob([bytes], { type: 'audio/webm' });
        
        // Play the audio
        const arrayBuffer = await audioBlob.arrayBuffer();
        await playerActions.playAudio(arrayBuffer);
      } catch (err) {
        console.error('Error playing AI response:', err);
        setConversationStatus('idle');
      }
    });
    
    webRTCActions.onAiFinished(() => {
      setConversationStatus('idle');
    });
  }, [webRTCState.isConnected, webRTCActions, playerActions]);

  const getConversationStatusText = () => {
    switch (conversationStatus) {
      case 'idle':
        return '等待中';
      case 'recording':
        return '正在录音...';
      case 'thinking':
        return '正在思考...';
      case 'playing':
        return '正在播放...';
      default:
        return '等待中';
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Voice Gateway</h1>
        <VoiceConnectionStatus 
          isConnected={webRTCState.isConnected}
          isConnecting={webRTCState.isConnecting}
          error={webRTCState.error}
          onRetry={handleRetry}
        />
        <p>实时语音通话系统</p>
        
        {/* Recording Controls */}
        <div className="recording-controls">
          {recorderError && (
            <div className="error-message">{recorderError}</div>
          )}
          {!hasPermission && hasPermission !== null && (
            <button onClick={requestPermission} className="permission-button">
              允许麦克风访问
            </button>
          )}
          {hasPermission && (
            <button 
              onClick={isRecording ? handleStopRecording : handleStartRecording}
              className={`recording-button ${isRecording ? 'recording' : ''}`}
            >
              {isRecording ? '停止录音' : '开始录音'}
            </button>
          )}
        </div>

        {/* Conversation Status */}
        <div className="conversation-status">
          <div className="status-text">{getConversationStatusText()}</div>
          {conversationStatus === 'recording' && (
            <AudioVolumeIndicator 
              mediaStream={mediaStream} 
              isRecording={isRecording} 
            />
          )}
        </div>
        
        {/* Playback Error */}
        {playerError && (
          <div className="error-message">播放失败: {playerError}</div>
        )}
      </header>
    </div>
  );
}

export default App;