import React from 'react';

interface VoiceConnectionStatusProps {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  onRetry: () => void;
}

export const VoiceConnectionStatus: React.FC<VoiceConnectionStatusProps> = ({
  isConnected,
  isConnecting,
  error,
  onRetry
}) => {
  // 初始状态：既没有连接也没有正在连接，且没有错误
  if (!isConnected && !isConnecting && !error) {
    return (
      <div className="connection-status waiting">
        等待连接
      </div>
    );
  }
  
  if (isConnecting) {
    return (
      <div className="connection-status connecting">
        正在连接...
      </div>
    );
  }
  
  if (isConnected) {
    return (
      <div className="connection-status connected">
        已连接
      </div>
    );
  }
  
  // 显示错误信息或断开连接状态，并提供重连按钮
  return (
    <div className="connection-status disconnected">
      {error ? (
        <span>{error}</span>
      ) : (
        <span>连接已断开</span>
      )}
      <button 
        className="retry-button"
        onClick={onRetry}
      >
        重连
      </button>
    </div>
  );
};