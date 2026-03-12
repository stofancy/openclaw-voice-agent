#!/bin/bash
#
# 网关看门狗脚本 - 自动监控并重启网关
# 只通过看门狗启动网关，避免冲突
#

LOG_DIR="$HOME/workspaces/audio-proxy/logs"
PID_FILE="$HOME/workspaces/audio-proxy/gateway.pid"
CHECK_INTERVAL=10  # 每 10 秒检查一次

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_DIR/watchdog.log"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

start_gateway() {
    log "🚀 启动网关..."
    
    # 先清理旧进程（如果有）
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            log "⚠️  发现旧进程 (PID: $OLD_PID)，停止中..."
            kill $OLD_PID 2>/dev/null
            sleep 2
        fi
        rm -f "$PID_FILE"
    fi
    
    # 确保端口空闲
    fuser -k 8765/tcp 2>/dev/null
    sleep 1
    
    cd "$HOME/workspaces/audio-proxy"
    source venv/bin/activate
    cd wsl2
    
    # 启动网关
    nohup python3 agent-gateway.py > "../logs/agent-gateway-$(date +%Y%m%d_%H%M%S).log" 2>&1 &
    GATEWAY_PID=$!
    
    echo $GATEWAY_PID > "$PID_FILE"
    log "✅ 网关已启动 (PID: $GATEWAY_PID)"
    
    # 等待 3 秒验证启动
    sleep 3
    if ps -p $GATEWAY_PID > /dev/null 2>&1; then
        log "✅ 网关运行正常"
        return 0
    else
        log "❌ 网关启动失败"
        rm -f "$PID_FILE"
        return 1
    fi
}

check_gateway() {
    # 检查 PID 文件
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            # 进程在运行
            return 0
        else
            log "⚠️  网关进程已死 (PID: $OLD_PID)"
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    
    # 检查是否有进程在运行
    if pgrep -f "agent-gateway.py" > /dev/null 2>&1; then
        RUNNING_PID=$(pgrep -f "agent-gateway.py" | head -1)
        log "⚠️  发现未管理的网关进程 (PID: $RUNNING_PID)，接管中..."
        echo $RUNNING_PID > "$PID_FILE"
        return 0
    fi
    
    return 1
}

# 主循环
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "🐕 网关看门狗启动"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 初始启动
if ! check_gateway; then
    start_gateway
fi

# 持续监控
while true; do
    sleep $CHECK_INTERVAL
    
    if ! check_gateway; then
        log "⚠️  网关未运行，尝试重启..."
        start_gateway
    fi
done
