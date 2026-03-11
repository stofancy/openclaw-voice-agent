#!/bin/bash
# 简单日志查看器 - 显示最新网关日志

LOG_DIR="$HOME/workspaces/audio-proxy/logs"
LATEST_LOG=$(ls -t "$LOG_DIR"/agent_gateway_*.log 2>/dev/null | head -1)

if [ -n "$LATEST_LOG" ]; then
    echo "📋 最新日志：$LATEST_LOG"
    echo ""
    echo "=== 最新 50 行 ==="
    tail -50 "$LATEST_LOG"
    echo ""
    echo "=== 实时追踪 (Ctrl+C 停止) ==="
    tail -f "$LATEST_LOG"
else
    echo "❌ 未找到日志文件"
fi
