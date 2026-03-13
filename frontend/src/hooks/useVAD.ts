import { useRef, useCallback, useEffect } from 'react';

interface VADOptions {
  silenceThreshold?: number;
  silenceDuration?: number;
  onSpeechEnd?: () => void;
}

export function useVAD(options: VADOptions = {}) {
  const { silenceThreshold = 0.01, silenceDuration = 1000, onSpeechEnd } = options;
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const silenceStartRef = useRef<number | null>(null);
  const animationRef = useRef<number | null>(null);

  const startVAD = useCallback(async (stream: MediaStream) => {
    streamRef.current = stream;
    audioContextRef.current = new AudioContext();
    analyserRef.current = audioContextRef.current.createAnalyser();
    const source = audioContextRef.current.createMediaStreamSource(stream);
    source.connect(analyserRef.current);
    analyserRef.current.fftSize = 256;

    const detect = () => {
      if (!analyserRef.current) return;
      const data = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(data);
      const volume = data.reduce((a, b) => a + b, 0) / data.length / 255;
      
      if (volume < silenceThreshold) {
        if (!silenceStartRef.current) {
          silenceStartRef.current = Date.now();
        } else if (Date.now() - silenceStartRef.current > silenceDuration) {
          onSpeechEnd?.();
          silenceStartRef.current = null;
        }
      } else {
        silenceStartRef.current = null;
      }
      animationRef.current = requestAnimationFrame(detect);
    };
    detect();
  }, [silenceThreshold, silenceDuration, onSpeechEnd]);

  const stopVAD = useCallback(() => {
    if (animationRef.current) cancelAnimationFrame(animationRef.current);
    if (audioContextRef.current) audioContextRef.current.close();
    audioContextRef.current = null;
    analyserRef.current = null;
  }, []);

  useEffect(() => {
    return () => stopVAD();
  }, [stopVAD]);

  return { startVAD, stopVAD };
}