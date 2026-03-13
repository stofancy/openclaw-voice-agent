import { useState, useEffect } from 'react';
import { useWebRTC } from './hooks/useWebRTC';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { useAudioPlayer } from './hooks/useAudioPlayer';
import { 
  Mic, 
  Volume2, 
  Wifi,
  WifiOff,
  Loader2,
  Bot,
  User,
  Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

type ConversationStatus = 'idle' | 'recording' | 'thinking' | 'speaking';

function App() {
  const [webRTCState, webRTCActions] = useWebRTC('ws://localhost:8080');
  const {
    hasPermission,
    requestPermission,
    startRecording,
    stopRecording
  } = useAudioRecorder();
  
  const [playerState, playerActions] = useAudioPlayer();
  const { status: playerStatus } = playerState;
  
  const [conversationStatus, setConversationStatus] = useState<ConversationStatus>('idle');
  const [transcript, setTranscript] = useState<string>('');
  const [aiResponse, setAiResponse] = useState<string>('');

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
      setTranscript('');
      setAiResponse('');
    }
  };

  const handleStopRecording = async () => {
    const audioBlob = await stopRecording();
    setConversationStatus('thinking');
    
    if (audioBlob && webRTCState.isConnected) {
      try {
        const base64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
            const result = reader.result as string;
            const base64Data = result.includes(',') ? result.split(',')[1] : result;
            resolve(base64Data);
          };
          reader.onerror = reject;
          reader.readAsDataURL(audioBlob);
        });
        
        webRTCActions.sendAudioData(base64, 'webm');
      } catch (err) {
        console.error('Failed to send audio:', err);
        setConversationStatus('idle');
      }
    }
  };

  // Handle audio playback status changes
  useEffect(() => {
    if (playerStatus === 'playing') {
      setConversationStatus('speaking');
    } else if (playerStatus === 'idle' && conversationStatus === 'speaking') {
      setConversationStatus('idle');
    }
  }, [playerStatus, conversationStatus]);

  // Set up listener for AI responses
  useEffect(() => {
    if (!webRTCState.isConnected) return;
    
    webRTCActions.onAiResponse(async (audioData: string, _turnId: number) => {
      try {
        // Convert base64 to audio using FileReader
        const binaryString = atob(audioData);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const audioBlob = new Blob([bytes], { type: 'audio/wav' });
        
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

  const getStatusDisplay = () => {
    switch (conversationStatus) {
      case 'recording':
        return { text: 'Listening...', color: 'text-red-500', Icon: Mic };
      case 'thinking':
        return { text: 'Thinking...', color: 'text-amber-500', Icon: Loader2 };
      case 'speaking':
        return { text: 'Speaking...', color: 'text-green-500', Icon: Volume2 };
      default:
        return { text: 'Tap to speak', color: 'text-gray-400', Icon: Sparkles };
    }
  };

  const statusDisplay = getStatusDisplay();
  const StatusIcon = statusDisplay.Icon;

  return (
    <div className="app-container">
      <div className="chat-interface">
        {/* Header */}
        <header className="chat-header">
          <div className="logo">
            <Bot className="w-6 h-6" />
            <span>Voice Assistant</span>
          </div>
          <div className={`connection-badge ${webRTCState.isConnected ? 'connected' : 'disconnected'}`}>
            {webRTCState.isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            <span>{webRTCState.isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </header>

        {/* Messages Area */}
        <div className="messages-container">
          <AnimatePresence>
            {transcript && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="message user-message"
              >
                <div className="message-avatar">
                  <User className="w-5 h-5" />
                </div>
                <div className="message-content">
                  {transcript}
                </div>
              </motion.div>
            )}
            
            {aiResponse && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="message ai-message"
              >
                <div className="message-avatar">
                  <Bot className="w-5 h-5" />
                </div>
                <div className="message-content">
                  {aiResponse}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Voice Control Area */}
        <div className="voice-control-area">
          <div className="status-indicator">
            <motion.div 
              animate={{ 
                scale: conversationStatus === 'recording' ? [1, 1.2, 1] : 1,
              }}
              transition={{ repeat: conversationStatus === 'recording' ? Infinity : 0, duration: 1 }}
            >
              <StatusIcon className={`w-6 h-6 ${statusDisplay.color}`} />
            </motion.div>
            <span className={`status-text ${statusDisplay.color}`}>
              {statusDisplay.text}
            </span>
          </div>

          {/* Main Voice Button */}
          <motion.button
            className={`voice-button ${conversationStatus}`}
            onClick={conversationStatus === 'idle' ? handleStartRecording : handleStopRecording}
            whileTap={{ scale: 0.95 }}
            animate={{
              boxShadow: conversationStatus === 'recording' 
                ? '0 0 0 0 rgba(239, 68, 68, 0.7)' 
                : conversationStatus === 'thinking'
                ? '0 0 0 0 rgba(245, 158, 11, 0.7)'
                : conversationStatus === 'speaking'
                ? '0 0 0 0 rgba(34, 197, 94, 0.7)'
                : '0 0 20px rgba(59, 130, 246, 0.5)'
            }}
          >
            {conversationStatus === 'idle' && <Mic className="w-8 h-8" />}
            {conversationStatus === 'recording' && <div className="recording-pulse" />}
            {conversationStatus === 'thinking' && <Loader2 className="w-8 h-8 animate-spin" />}
            {conversationStatus === 'speaking' && <Volume2 className="w-8 h-8" />}
          </motion.button>

          <p className="voice-hint">
            {conversationStatus === 'idle' 
              ? 'Tap to start conversation' 
              : conversationStatus === 'recording'
              ? 'Tap to stop'
              : 'Processing...'}
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
