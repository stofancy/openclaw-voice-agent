#!/bin/bash
# 自动监控脚本 - 实时查看网关和 HTTP 服务器日志

echo "============================================================"
echo "📊 AI Voice Agent 自动监控"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志目录
LOG_DIR="$HOME/workspaces/audio-proxy/logs"

# 检查服务状态
echo -e "${BLUE}检查服务状态...${NC}"
echo ""

# 检查网关
if pgrep -f "agent-gateway.py" > /dev/null; then
    echo -e "${GREEN}✅ 语音网关运行中${NC}"
    GATEWAY_PID=$(pgrep -f "agent-gateway.py")
    echo "   PID: $GATEWAY_PID"
else
    echo -e "${RED}❌ 语音网关未运行${NC}"
fi

# 检查 HTTP 服务器
if pgrep -f "http.server 8080" > /dev/null; then
    echo -e "${GREEN}✅ HTTP 服务器运行中${NC}"
    HTTP_PID=$(pgrep -f "http.server 8080")
    echo "   PID: $HTTP_PID"
    echo "   URL: http://localhost:8080/test-pages/pro-call.html"
else
    echo -e "${RED}❌ HTTP 服务器未运行${NC}"
fi

echo ""
echo "============================================================"
echo "📋 实时日志监控 (按 Ctrl+C 停止)"
echo "============================================================"
echo ""

# 显示最新日志文件
LATEST_LOG=$(ls -t "$LOG_DIR"/agent_gateway_*.log 2>/dev/null | head -1)

if [ -n "$LATEST_LOG" ]; then
    echo -e "${YELLOW}日志文件：${LATEST_LOG}${NC}"
    echo ""
    echo -e "${YELLOW}等待用户连接和通话...${NC}"
    echo ""
    echo "-----------------------------------------------------------"
    
    # 实时监控日志
    tail -n 50 -f "$LATEST_LOG" | while read line; do
        # 高亮显示重要信息
        if [[ $line == *"❌"* ]] || [[ $line == *"错误"* ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ $line == *"✅"* ]] || [[ $line == *"成功"* ]]; then
            echo -e "${GREEN}$line${NC}"
        elif [[ $line == *"📞"* ]] || [[ $line == *"🎤"* ]] || [[ $line == *"🔊"* ]]; then
            echo -e "${YELLOW}$line${NC}"
        elif [[ $line == *"🗣️"* ]] || [[ $line == *"🤖"* ]]; then
            echo -e "${BLUE}$line${NC}"
        else
            echo "$line"
        fi
    done
else
    echo -e "${RED}未找到日志文件${NC}"
    echo "请先启动网关：cd ~/workspaces/audio-proxy/wsl2 && python3 agent-gateway.py"
fi
