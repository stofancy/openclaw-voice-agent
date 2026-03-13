import React, { useEffect, useRef } from 'react';

interface AudioVolumeIndicatorProps {
  mediaStream: MediaStream | null;
  isRecording: boolean;
}

export const AudioVolumeIndicator: React.FC<AudioVolumeIndicatorProps> = ({
  mediaStream,
  isRecording
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>(0);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  useEffect(() => {
    if (!isRecording || !mediaStream || !canvasRef.current) {
      // Clear canvas when not recording or no stream
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
      }
      return;
    }

    // Create audio context and analyser
    const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
    audioContextRef.current = new AudioContext();
    analyserRef.current = audioContextRef.current.createAnalyser();
    analyserRef.current.fftSize = 256;
    
    // Create source from media stream
    sourceRef.current = audioContextRef.current.createMediaStreamSource(mediaStream);
    sourceRef.current.connect(analyserRef.current);

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      if (!analyserRef.current || !ctx) return;
      
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      analyserRef.current.getByteFrequencyData(dataArray);

      // Calculate average volume
      let sum = 0;
      for (let i = 0; i < bufferLength; i++) {
        sum += dataArray[i];
      }
      const average = sum / bufferLength;
      
      // Normalize to 0-1 range
      const normalizedVolume = Math.min(average / 255, 1);
      
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw volume bar
      const barHeight = normalizedVolume * canvas.height;
      const barWidth = canvas.width;
      
      // Create gradient
      const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
      gradient.addColorStop(0, '#4CAF50'); // Green for low volume
      gradient.addColorStop(0.5, '#FFEB3B'); // Yellow for medium
      gradient.addColorStop(1, '#F44336'); // Red for high
      
      ctx.fillStyle = gradient;
      ctx.fillRect(0, canvas.height - barHeight, barWidth, barHeight);
      
      animationFrameRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animationFrameRef.current);
      if (sourceRef.current) {
        sourceRef.current.disconnect();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [mediaStream, isRecording]);

  return (
    <div className="volume-indicator">
      <canvas 
        ref={canvasRef} 
        width={40} 
        height={100}
        style={{ display: isRecording ? 'block' : 'none' }}
      />
    </div>
  );
};