#!/bin/bash
# 网关保活脚本 - 每分钟检查一次，如果挂了自动重启

LOG_DIR="$HOME/workspaces/audio-proxy/logs"
PID_FILE="$HOME/workspaces/audio-proxy/gateway.pid"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_DIR/gateway-keepalive.log"
}

check_and_restart() {
    # 检查是否有 PID 文件
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            # 进程在运行
            return 0
        else
            log "⚠️  网关进程已死 (PID: $OLD_PID)，清理 PID 文件..."
            rm -f "$PID_FILE"
        fi
    fi
    
    # 检查是否有进程在运行
    if pgrep -f "agent-gateway.py" > /dev/null 2>&1; then
        RUNNING_PID=$(pgrep -f "agent-gateway.py" | head -1)
        log "✅ 网关已在运行 (PID: $RUNNING_PID)"
        echo $RUNNING_PID > "$PID_FILE"
        return 0
    fi
    
    # 启动网关
    log "🚀 启动网关..."
    cd "$HOME/workspaces/audio-proxy"
    source venv/bin/activate
    cd wsl2
    
    nohup python3 agent-gateway.py > "$LOG_DIR/agent-gateway-$(date +%Y%m%d_%H%M%S).log" 2>&1 &
    NEW_PID=$!
    
    echo $NEW_PID > "$PID_FILE"
    log "✅ 网关已启动 (PID: $NEW_PID)"
    
    # 验证启动
    sleep 3
    if ps -p $NEW_PID > /dev/null 2>&1; then
        log "✅ 网关运行正常"
        return 0
    else
        log "❌ 网关启动失败"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 主循环
log "━━━ 网关保活服务启动 ━━━"

while true; do
    check_and_restart
    sleep 60  # 每分钟检查一次
done
