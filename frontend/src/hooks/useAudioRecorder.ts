import { useState, useCallback, useRef } from 'react';

// Web Speech API types
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: (event: SpeechRecognitionEvent) => void;
  onerror: (event: SpeechRecognitionErrorEvent) => void;
  start: () => void;
  stop: () => void;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  
  // Web Speech API for STT
  const speechRecognitionRef = useRef<SpeechRecognition | null>(null);
  const [transcribedText, setTranscribedText] = useState<string>('');

  const requestPermission = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setMediaStream(stream);
      setHasPermission(true);
      setError(null);
      return true;
    } catch (err: unknown) {
      setHasPermission(false);
      setError('需要麦克风权限');
      return false;
    }
  }, []);

  const openSettings = useCallback(() => {
    if (navigator.permissions) {
      navigator.permissions.query({ name: 'microphone' as PermissionName })
        .then(permissionStatus => {
          console.log('Microphone permission status:', permissionStatus.state);
        });
    }
    alert('请在浏览器设置中允许麦克风权限。\n\nChrome: 设置 > 隐私设置和安全性 > 网站设置 > 麦克风\nSafari: 设置 > Safari > 网站 > 麦克风');
  }, []);

  const startRecording = useCallback(async () => {
    if (!mediaStream) {
      const granted = await requestPermission();
      if (!granted) return;
    }
    
    // Reset audio chunks and transcribed text
    audioChunksRef.current = [];
    setTranscribedText('');
    
    // Create MediaRecorder
    if (mediaStream) {
      const mediaRecorder = new MediaRecorder(mediaStream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100); // Collect data every 100ms
    }
    
    // Start Web Speech API for real-time transcription
    const SpeechRecognitionAPI = window.SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognitionAPI) {
      const recognition = new SpeechRecognitionAPI();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'zh-CN';
      
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        if (finalTranscript) {
          setTranscribedText(prev => prev + finalTranscript);
        }
      };
      
      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.log('Speech recognition error:', event.error);
      };
      
      recognition.start();
      speechRecognitionRef.current = recognition;
    }
    
    setIsRecording(true);
  }, [requestPermission, mediaStream]);

  const stopRecording = useCallback((): Promise<{ audioBlob: Blob | null; text: string }> => {
    return new Promise((resolve) => {
      // Stop speech recognition
      if (speechRecognitionRef.current) {
        speechRecognitionRef.current.stop();
        speechRecognitionRef.current = null;
      }
      
      if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
        resolve({ audioBlob: null, text: transcribedText });
        return;
      }
      
      mediaRecorderRef.current.onstop = () => {
        // Create audio blob from chunks
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Return both audio and transcribed text
        resolve({ audioBlob, text: transcribedText });
      };
      
      mediaRecorderRef.current.stop();
    });
  }, [transcribedText]);

  return {
    isRecording,
    hasPermission,
    error,
    requestPermission,
    openSettings,
    startRecording,
    stopRecording,
    mediaStream,
    transcribedText
  };
}
