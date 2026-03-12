/**
 * Voice Gateway SDK - JavaScript 浏览器版本
 * 
 * @example
 * const gateway = new VoiceGateway({
 *     url: "ws://localhost:8765",
 *     onReply: (text) => console.log("Agent:", text)
 * });
 * await gateway.connect();
 * await gateway.sendSTTResult("你好");
 */
class VoiceGateway {
    /**
     * 创建 VoiceGateway 实例
     * @param {Object} options - 配置选项
     * @param {string} options.url - WebSocket URL
     * @param {Function} options.onConnected - 连接成功回调
     * @param {Function} options.onDisconnected - 断开连接回调
     * @param {Function} options.onReply - 收到回复回调
     * @param {Function} options.onAudio - 收到音频回调
     * @param {Function} options.onError - 错误回调
     * @param {Function} options.onStatus - 状态更新回调
     * @param {boolean} options.autoPlayAudio - 自动播放音频 (默认 true)
     */
    constructor(options = {}) {
        this.url = options.url || "ws://localhost:8765";
        this.onConnected = options.onConnected || (() => {});
        this.onDisconnected = options.onDisconnected || (() => {});
        this.onReply = options.onReply || (() => {});
        this.onAudio = options.onAudio || (() => {});
        this.onError = options.onError || (() => {});
        this.onStatus = options.onStatus || (() => {});
        this.autoPlayAudio = options.autoPlayAudio !== false; // 默认自动播放
        
        this.ws = null;
        this.state = "disconnected";
        this.audioContext = null;
        this.audioQueue = [];
        this.isPlaying = false;
    }
    
    /**
     * 连接网关
     * @returns {Promise<void>}
     */
    connect() {
        return new Promise((resolve, reject) => {
            if (this.state === "connected") {
                resolve();
                return;
            }
            
            if (this.state === "connecting") {
                reject(new Error("已在连接中"));
                return;
            }
            
            this.state = "connecting";
            
            try {
                this.ws = new WebSocket(this.url);
                
                this.ws.onopen = () => {
                    this.state = "connected";
                    console.log("✅ VoiceGateway 连接成功");
                    this.onConnected();
                    resolve();
                };
                
                this.ws.onerror = (error) => {
                    this.state = "disconnected";
                    console.error("❌ VoiceGateway 连接失败:", error);
                    this.onError(new Error("WebSocket 连接失败"));
                    reject(new Error("WebSocket 连接失败"));
                };
                
                this.ws.onclose = (event) => {
                    this.state = "disconnected";
                    console.log(`🔴 VoiceGateway 连接关闭 (code=${event.code})`);
                    this.ws = null;
                    this.onDisconnected();
                };
                
                this.ws.onmessage = (event) => {
                    this._handleMessage(event.data);
                };
                
            } catch (error) {
                this.state = "disconnected";
                console.error("❌ VoiceGateway 异常:", error);
                this.onError(error);
                reject(error);
            }
        });
    }
    
    /**
     * 断开连接
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.state = "disconnected";
    }
    
    /**
     * 处理接收到的消息
     * @private
     * @param {string} data - 原始消息数据
     */
    _handleMessage(data) {
        try {
            const message = JSON.parse(data);
            
            switch (message.type) {
                case "status":
                    this.onStatus(message.status);
                    break;
                    
                case "reply":
                    if (message.text) {
                        this.onReply(message.text);
                    }
                    break;
                    
                case "audio":
                    if (message.data) {
                        this.onAudio(message.data);
                        if (this.autoPlayAudio) {
                            this._playAudioBase64(message.data);
                        }
                    }
                    break;
                    
                default:
                    console.log("📥 收到未知消息类型:", message.type);
            }
            
        } catch (error) {
            console.error("❌ 解析消息失败:", error);
        }
    }
    
    /**
     * 发送 STT 识别结果
     * @param {string} text - 识别的文本
     */
    sendSTTResult(text) {
        this._send({
            type: "stt_result",
            text: text
        });
    }
    
    /**
     * 发送文本消息
     * @param {string} text - 要发送的文本
     */
    sendText(text) {
        this._send({
            type: "text",
            text: text
        });
    }
    
    /**
     * 发送原始消息
     * @param {Object} data - 消息数据
     */
    send(data) {
        this._send(data);
    }
    
    /**
     * 内部发送方法
     * @private
     * @param {Object} data - 消息数据
     */
    _send(data) {
        if (this.state !== "connected") {
            console.warn("⚠️ 未连接，无法发送消息");
            return;
        }
        
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error("❌ WebSocket 未就绪");
            return;
        }
        
        try {
            this.ws.send(JSON.stringify(data));
        } catch (error) {
            console.error("❌ 发送失败:", error);
            this.onError(error);
        }
    }
    
    /**
     * 检查是否已连接
     * @returns {boolean}
     */
    isConnected() {
        return this.state === "connected" && 
               this.ws && 
               this.ws.readyState === WebSocket.OPEN;
    }
    
    /**
     * 播放 Base64 音频数据 (PCM 24kHz 单声道 16bit)
     * @private
     * @param {string} base64Audio - Base64 编码的 PCM 音频
     */
    _playAudioBase64(base64Audio) {
        const logPrefix = `[TTS #${this.audioQueue.length + 1}]`;
        console.log(`${logPrefix} 🎵 _playAudioBase64 调用，base64 长度:`, base64Audio ? base64Audio.length : 0);
        
        try {
            // 解码 Base64
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            console.log(`${logPrefix}    Base64 解码后 bytes:`, bytes.length);
            
            // PCM 16bit 转 Float32
            const samples = new Float32Array(bytes.length / 2);
            const dataView = new DataView(bytes.buffer);
            for (let i = 0; i < bytes.length / 2; i++) {
                const int16 = dataView.getInt16(i * 2, true); // little-endian
                samples[i] = int16 / 32768.0;
            }
            console.log(`${logPrefix}    PCM 转 Float32 samples:`, samples.length);
            
            // 加入播放队列
            this.audioQueue.push(samples);
            console.log(`${logPrefix}    audioQueue 长度:`, this.audioQueue.length);
            
            // 如果当前没有在播放，开始播放
            if (!this.isPlaying) {
                console.log(`${logPrefix}    ▶️ 开始播放队列...`);
                this._playNextInQueue();
            } else {
                console.log(`${logPrefix}    ⏸️ 已在播放，加入队列等待`);
            }
            
        } catch (error) {
            console.error(`${logPrefix} ❌ 音频播放失败:`, error);
            this.onError(new Error("音频播放失败：" + error.message));
        }
    }
    
    /**
     * 播放队列中的下一个音频片段
     * @private
     */
    _playNextInQueue() {
        console.log(`[播放] _playNextInQueue 调用，queue 长度:`, this.audioQueue.length);
        
        if (this.audioQueue.length === 0) {
            console.log(`[播放] 队列为空，停止播放`);
            this.isPlaying = false;
            return;
        }
        
        this.isPlaying = true;
        const samples = this.audioQueue.shift();
        console.log(`[播放] 取出 samples 长度:`, samples.length);
        console.log(`[播放] 预计播放时长:`, (samples.length / 24000).toFixed(3), '秒');
        
        // 创建 AudioContext (首次调用时)
        if (!this.audioContext) {
            console.log(`[播放] 创建 AudioContext (24kHz)`);
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 24000 // 匹配 TTS 输出采样率
            });
        }
        
        // 恢复 AudioContext（如果被挂起）
        if (this.audioContext.state === 'suspended') {
            console.log(`[播放] AudioContext 被挂起，恢复中...`);
            this.audioContext.resume().then(() => {
                console.log(`[播放] AudioContext 已恢复`);
            });
        }
        
        // 创建 AudioBuffer
        const audioBuffer = this.audioContext.createBuffer(1, samples.length, 24000);
        
        // 使用 copyToChannel 填充数据（MDN 推荐方式）
        audioBuffer.copyToChannel(samples, 0);
        console.log(`[播放] 创建 AudioBuffer:`, audioBuffer.length, 'samples');
        
        // 创建音源并播放
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.audioContext.destination);
        
        console.log(`[播放] ▶️ 开始播放...`);
        console.log(`[播放] AudioContext 状态:`, this.audioContext.state);
        
        // 播放状态监听
        source.onended = () => {
            console.log(`[播放] ✅ 播放完成`);
            this._playNextInQueue();
        };
        
        source.onerror = (error) => {
            console.error(`[播放] ❌ 播放错误:`, error);
            this._playNextInQueue();
        };
        
        source.start(0);
    }
    
    /**
     * 手动播放音频
     * @param {string} base64Audio - Base64 编码的 PCM 音频
     */
    playAudio(base64Audio) {
        console.log(`[playAudio] 调用，base64 长度:`, base64Audio ? base64Audio.length : 0);
        console.log(`[playAudio] isPlaying:`, this.isPlaying);
        console.log(`[playAudio] audioQueue 长度:`, this.audioQueue.length);
        
        this._playAudioBase64(base64Audio);
    }
    
    /**
     * 停止播放
     */
    stopAudio() {
        console.log('[stopAudio] 停止播放...');
        
        // 清空队列
        this.audioQueue = [];
        console.log('[stopAudio] 队列已清空');
        
        // 停止播放
        this.isPlaying = false;
        console.log('[stopAudio] isPlaying = false');
        
        // 关闭 AudioContext
        if (this.audioContext) {
            console.log('[stopAudio] 关闭 AudioContext...');
            this.audioContext.close().then(() => {
                console.log('[stopAudio] AudioContext 已关闭');
            }).catch(err => {
                console.error('[stopAudio] 关闭 AudioContext 失败:', err);
            });
            this.audioContext = null;
        }
        
        console.log('[stopAudio] 停止完成');
    }
}

// 导出（支持多种模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceGateway;
}

if (typeof window !== 'undefined') {
    window.VoiceGateway = VoiceGateway;
}
