import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { useWebRTC } from './hooks/useWebRTC';
import { VoiceConnectionStatus } from './components/VoiceConnectionStatus';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { useAudioPlayer } from './hooks/useAudioPlayer';

function App() {
  const [webRTCState, webRTCActions] = useWebRTC('ws://localhost:8765');
  const {
    isRecording,
    hasPermission,
    error: recorderError,
    requestPermission,
    startRecording,
    stopRecording,
    mediaStream
  } = useAudioRecorder();
  
  const {
    isPlaying,
    playStatus,
    error: playerError,
    playAudio,
    stopAudio
  } = useAudioPlayer();
  
  const [playbackStatus, setPlaybackStatus] = useState<'idle' | 'playing' | 'completed' | 'error'>('idle');
  const [conversationActive, setConversationActive] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  
  const handleRetry = () => {
    webRTCActions.connect();
  };

  const handleStartRecording = async () => {
    if (hasPermission === null) {
      await requestPermission();
    }
    if (hasPermission) {
      startRecording();
      setConversationActive(true);
    }
  };

  // Handle audio playback status changes
  useEffect(() => {
    if (isPlaying) {
      setPlaybackStatus('playing');
    } else if (playStatus === 'completed') {
      setPlaybackStatus('completed');
      // US-06: AI 播放完成后自动准备下一轮录音
      if (conversationActive) {
        // Automatically prepare for next round of recording
        setTimeout(() => {
          if (hasPermission && !isRecording) {
            startRecording();
          }
        }, 500); // Small delay to ensure smooth transition
      }
    } else if (playerError) {
      setPlaybackStatus('error');
    }
  }, [isPlaying, playStatus, playerError, conversationActive, hasPermission, isRecording, startRecording]);

  // Handle WebRTC messages
  useEffect(() => {
    if (!webRTCState.isConnected || !mediaStream) {
      return;
    }

    const handleAudioData = async (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'audio-response') {
          // Convert base64 audio data to ArrayBuffer
          const binaryString = atob(data.audio);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const audioBlob = new Blob([bytes], { type: 'audio/opus' });
          await playAudio(audioBlob);
        }
      } catch (error) {
        console.error('Error handling audio response:', error);
      }
    };

    // This would need to be connected to the actual WebSocket
    // For now, we'll simulate the connection through the existing hooks
    
  }, [webRTCState.isConnected, mediaStream, playAudio]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

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
              onClick={isRecording ? stopRecording : handleStartRecording}
              className={`recording-button ${isRecording ? 'recording' : ''}`}
            >
              {isRecording ? '停止录音' : '开始录音'}
            </button>
          )}
          {isRecording && <div className="recording-indicator">● 录音中...</div>}
        </div>

        {/* Playback Status */}
        <div className="playback-status">
          {playbackStatus === 'playing' && (
            <div className="playing-indicator">正在播放...</div>
          )}
          {playbackStatus === 'completed' && (
            <div className="completed-indicator">等待中</div>
          )}
          {playbackStatus === 'error' && (
            <div className="error-message">播放失败: {playerError}</div>
          )}
          {playbackStatus === 'idle' && (
            <div className="idle-indicator">等待中</div>
          )}
        </div>
        
        {/* Conversation Status */}
        {conversationActive && (
          <div className="conversation-status">
            多轮对话进行中...
          </div>
        )}
      </header>
    </div>
  );
}

export default App;