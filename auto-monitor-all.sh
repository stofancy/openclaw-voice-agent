#!/bin/bash
# 全自动监控脚本 - 同时监控网关日志和 HTTP 服务器

echo "============================================================"
echo "📊 AI Voice Agent 全自动监控中心"
echo "============================================================"
echo ""
echo "启动时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

LOG_DIR="$HOME/workspaces/audio-proxy/logs"

# 检查服务
echo -e "${CYAN}━━━ 服务状态 ━━━${NC}"

# 网关
if pgrep -f "agent-gateway.py" > /dev/null; then
    GATEWAY_PID=$(pgrep -f "agent-gateway.py" | head -1)
    echo -e "${GREEN}✅ 语音网关${NC} (PID: $GATEWAY_PID)"
else
    echo -e "${RED}❌ 语音网关未运行${NC}"
    echo "   启动：cd ~/workspaces/audio-proxy && ./start-gateway.sh"
fi

# HTTP
if pgrep -f "http.server 8080" > /dev/null; then
    HTTP_PID=$(pgrep -f "http.server 8080")
    echo -e "${GREEN}✅ HTTP 服务器${NC} (PID: $HTTP_PID)"
    echo -e "   ${CYAN}http://localhost:8080/test-pages/pro-call.html${NC}"
else
    echo -e "${RED}❌ HTTP 服务器未运行${NC}"
fi

echo ""
echo -e "${CYAN}━━━ 实时日志监控 ━━━${NC}"
echo "按 Ctrl+C 停止"
echo ""

# 找到最新日志
LATEST_LOG=$(ls -t "$LOG_DIR"/agent_gateway*.log 2>/dev/null | head -1)

if [ -n "$LATEST_LOG" ]; then
    echo -e "${YELLOW}日志文件：${LATEST_LOG}${NC}"
    echo ""
    
    # 实时监控
    tail -n 100 -f "$LATEST_LOG" | while IFS= read -r line; do
        # 高亮显示
        if [[ $line == *"❌"* ]] || [[ $line == *"FAIL"* ]] || [[ $line == *"错误"* ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ $line == *"✅"* ]] || [[ $line == *"PASS"* ]] || [[ $line == *"成功"* ]]; then
            echo -e "${GREEN}$line${NC}"
        elif [[ $line == *"⚠️"* ]] || [[ $line == *"WARN"* ]]; then
            echo -e "${YELLOW}$line${NC}"
        elif [[ $line == *"🌐"* ]] || [[ $line == *"📞"* ]] || [[ $line == *"🎤"* ]] || [[ $line == *"🔊"* ]]; then
            echo -e "${CYAN}$line${NC}"
        elif [[ $line == *"🗣️"* ]] || [[ $line == *"🤖"* ]] || [[ $line == *"📝"* ]]; then
            echo -e "${BLUE}$line${NC}"
        elif [[ $line == *"browser"* ]] || [[ $line == *"BROWSER"* ]]; then
            echo -e "${YELLOW}$line${NC}"
        else
            echo "$line"
        fi
    done
else
    echo -e "${RED}未找到日志文件${NC}"
fi
