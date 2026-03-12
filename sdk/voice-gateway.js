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
        console.log('🎵 _playAudioBase64 调用，base64 长度:', base64Audio ? base64Audio.length : 0);
        try {
            // 解码 Base64
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            // PCM 16bit 转 Float32
            const samples = new Float32Array(bytes.length / 2);
            const dataView = new DataView(bytes.buffer);
            for (let i = 0; i < bytes.length / 2; i++) {
                const int16 = dataView.getInt16(i * 2, true); // little-endian
                samples[i] = int16 / 32768.0;
            }
            
            // 加入播放队列
            this.audioQueue.push(samples);
            console.log('   audioQueue 长度:', this.audioQueue.length);
            
            // 如果当前没有在播放，开始播放
            if (!this.isPlaying) {
                console.log('   ▶️ 开始播放队列...');
                this._playNextInQueue();
            } else {
                console.log('   ⏸️ 已在播放，加入队列等待');
            }
            
        } catch (error) {
            console.error("❌ 音频播放失败:", error);
            this.onError(new Error("音频播放失败：" + error.message));
        }
    }
    
    /**
     * 播放队列中的下一个音频片段
     * @private
     */
    _playNextInQueue() {
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            return;
        }
        
        this.isPlaying = true;
        const samples = this.audioQueue.shift();
        
        // 创建 AudioContext (首次调用时)
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 24000 // 匹配 TTS 输出采样率
            });
        }
        
        // 创建 AudioBuffer
        const audioBuffer = this.audioContext.createBuffer(1, samples.length, 24000);
        audioBuffer.getChannelData(0).set(samples);
        
        // 创建音源并播放
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.audioContext.destination);
        
        // 播放完成后播放下一个（不延迟）
        source.onended = () => {
            this._playNextInQueue();
        };
        
        source.start(0);
    }
    
    /**
     * 手动播放音频
     * @param {string} base64Audio - Base64 编码的 PCM 音频
     */
    playAudio(base64Audio) {
        // 再次检查播放状态
        if (this.isPlaying) {
            console.log('⚠️ playAudio: 正在播放，拒绝');
            return;
        }
        this._playAudioBase64(base64Audio);
    }
    
    /**
     * 停止播放
     */
    stopAudio() {
        this.audioQueue = [];
        this.isPlaying = false;
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
    }
}

// 导出（支持多种模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceGateway;
}

if (typeof window !== 'undefined') {
    window.VoiceGateway = VoiceGateway;
}
