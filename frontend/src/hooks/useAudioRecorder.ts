import { useState, useRef, useCallback } from 'react';

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);

  const requestPermission = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      setHasPermission(true);
      setError(null);
      return true;
    } catch (err: unknown) {
      setHasPermission(false);
      setError('需要麦克风权限才能使用语音助手');
      return false;
    }
  }, []);

  const startRecording = useCallback(async () => {
    if (!mediaStreamRef.current) {
      await requestPermission();
    }
    setIsRecording(true);
  }, [requestPermission]);

  const stopRecording = useCallback(() => {
    setIsRecording(false);
  }, []);

  return {
    isRecording,
    hasPermission,
    error,
    requestPermission,
    startRecording,
    stopRecording,
    mediaStream: mediaStreamRef.current
  };
}