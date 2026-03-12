#!/bin/bash
# 启动语音网关（守护进程模式）

LOG_DIR="$HOME/workspaces/audio-proxy/logs"
PID_FILE="$HOME/workspaces/audio-proxy/gateway.pid"

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "✅ 网关已在运行 (PID: $OLD_PID)"
        exit 0
    else
        echo "⚠️  检测到旧 PID 文件，清理中..."
        rm -f "$PID_FILE"
    fi
fi

# 启动网关
cd "$HOME/workspaces/audio-proxy"
source venv/bin/activate
cd wsl2

nohup python3 agent-gateway.py > "$LOG_DIR/agent-gateway.log" 2>&1 &
NEW_PID=$!

echo $NEW_PID > "$PID_FILE"

echo "✅ 网关已启动 (PID: $NEW_PID)"
echo "📋 日志：$LOG_DIR/agent-gateway.log"
echo ""
echo "等待 3 秒启动..."
sleep 3

# 验证是否成功
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ 网关运行正常"
    echo "🔌 WebSocket: ws://localhost:8765"
    echo "🌐 测试页面：http://localhost:8080/test-pages/pro-call.html"
else
    echo "❌ 网关启动失败"
    rm -f "$PID_FILE"
    exit 1
fi
