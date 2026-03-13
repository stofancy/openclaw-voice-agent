import { useState, useRef, useCallback } from 'react';

export type AudioPlayerStatus = 'idle' | 'playing' | 'paused' | 'error';

interface AudioPlayerState {
  status: AudioPlayerStatus;
  error: string | null;
}

interface AudioPlayerActions {
  playAudio: (audioData: ArrayBuffer | Blob) => Promise<void>;
  stop: () => void;
}

export function useAudioPlayer(): [AudioPlayerState, AudioPlayerActions] {
  const [state, setState] = useState<AudioPlayerState>({
    status: 'idle',
    error: null
  });
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);
  
  const playAudio = useCallback(async (audioData: ArrayBuffer | Blob) => {
    try {
      setState(prev => ({ ...prev, status: 'playing', error: null }));
      
      // Create audio context if not exists
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      
      // Stop any currently playing audio
      if (sourceRef.current) {
        sourceRef.current.stop();
      }
      
      // Convert to ArrayBuffer if needed
      let arrayBuffer: ArrayBuffer;
      if (audioData instanceof Blob) {
        arrayBuffer = await audioData.arrayBuffer();
      } else {
        arrayBuffer = audioData;
      }
      
      // Decode audio data
      const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
      
      // Create and play source
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      source.start();
      
      sourceRef.current = source;
      
      // Handle end of playback
      source.onended = () => {
        setState(prev => ({ ...prev, status: 'idle' }));
      };
      
    } catch (error) {
      console.error('Error playing audio:', error);
      setState(prev => ({ 
        ...prev, 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Failed to play audio'
      }));
    }
  }, []);
  
  const stop = useCallback(() => {
    if (sourceRef.current) {
      sourceRef.current.stop();
      sourceRef.current = null;
    }
    setState(prev => ({ ...prev, status: 'idle' }));
  }, []);
  
  return [
    state,
    {
      playAudio,
      stop
    }
  ];
}