import { useState, useCallback, useRef } from 'react';

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

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
    
    // Reset audio chunks
    audioChunksRef.current = [];
    
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
    
    setIsRecording(true);
  }, [requestPermission, mediaStream]);

  const stopRecording = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
        resolve(null);
        return;
      }
      
      mediaRecorderRef.current.onstop = () => {
        // Create audio blob from chunks
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Note: Do NOT stop the audio tracks - they can be reused for next recording
        // Only stop the MediaRecorder
        
        setIsRecording(false);
        resolve(audioBlob);
      };
      
      mediaRecorderRef.current.stop();
    });
  }, []);

  return {
    isRecording,
    hasPermission,
    error,
    requestPermission,
    openSettings,
    startRecording,
    stopRecording,
    mediaStream
  };
}
