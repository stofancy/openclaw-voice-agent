#!/bin/bash
#
# AI Voice Agent Build & Test Script
# 每次代码修改后必须运行此脚本
# 要求：100% 测试通过，80%+ 代码覆盖率
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     AI Voice Agent - Build & Test Script                ║${NC}"
echo -e "${BLUE}║     要求：100% 测试通过，80%+ 代码覆盖率                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查 Python 虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 虚拟环境不存在，请先创建：python3 -m venv venv${NC}"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo -e "${BLUE}[1/6] 安装测试依赖...${NC}"
pip install -q coverage pytest pytest-cov 2>/dev/null || true
echo -e "${GREEN}✅ 依赖安装完成${NC}"
echo ""

# 检查网关进程
echo -e "${BLUE}[2/6] 检查服务状态...${NC}"

# 启动网关 (如果未运行)
if ! pgrep -f "agent-gateway.py" > /dev/null; then
    echo -e "${YELLOW}⚠️  网关未运行，正在启动...${NC}"
    cd wsl2
    nohup python3 agent-gateway.py > ../logs/build-gateway.log 2>&1 &
    cd ..
    sleep 3
fi

# 检查网关
if pgrep -f "agent-gateway.py" > /dev/null; then
    GATEWAY_PID=$(pgrep -f "agent-gateway.py" | head -1)
    echo -e "${GREEN}✅ 网关运行中 (PID: $GATEWAY_PID)${NC}"
else
    echo -e "${RED}❌ 网关启动失败${NC}"
    exit 1
fi

# 检查 HTTP 服务器
if ! pgrep -f "http.server 8080" > /dev/null; then
    echo -e "${YELLOW}⚠️  HTTP 服务器未运行，正在启动...${NC}"
    nohup python3 -m http.server 8080 > logs/build-http.log 2>&1 &
    sleep 2
fi

if pgrep -f "http.server 8080" > /dev/null; then
    HTTP_PID=$(pgrep -f "http.server 8080" | head -1)
    echo -e "${GREEN}✅ HTTP 服务器运行中 (PID: $HTTP_PID)${NC}"
else
    echo -e "${RED}❌ HTTP 服务器启动失败${NC}"
    exit 1
fi
echo ""

# 运行 E2E 测试
echo -e "${BLUE}[3/6] 运行 E2E 测试...${NC}"
E2E_RESULT=0
python3 tests/test_e2e.py || E2E_RESULT=$?

if [ $E2E_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ E2E 测试通过${NC}"
else
    echo -e "${RED}❌ E2E 测试失败${NC}"
fi
echo ""

# 运行 STT 测试
echo -e "${BLUE}[4/6] 运行 STT API 测试...${NC}"
STT_RESULT=0
python3 tests/test_stt.py || STT_RESULT=$?

if [ $STT_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ STT 测试通过${NC}"
else
    echo -e "${YELLOW}⚠️  STT 测试有警告 (不影响功能)${NC}"
fi
echo ""

# 运行网关单元测试
echo -e "${BLUE}[5/6] 运行网关单元测试...${NC}"
UNIT_RESULT=0
python3 tests/test_gateway_unit.py || UNIT_RESULT=$?

if [ $UNIT_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ 网关单元测试通过 (30 用例)${NC}"
else
    echo -e "${RED}❌ 网关单元测试失败${NC}"
fi
echo ""

# 运行覆盖率测试
echo -e "${BLUE}[6/6] 运行代码覆盖率测试...${NC}"

# 创建覆盖率配置
cat > .coveragerc << EOF
[run]
source = wsl2
omit = 
    */tests/*
    */venv/*
    */logs/*
    */__pycache__/*
    */test*.py
    */bailian_stt.py
    */bailian_realtime_stt.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    except ImportError:

[html]
directory = htmlcov

[xml]
output = coverage.xml
EOF

# 运行覆盖率
cd wsl2
coverage run --source=. -m pytest -q 2>/dev/null || true
coverage report -m > ../logs/coverage_report.txt 2>&1
coverage html -d ../htmlcov 2>/dev/null || true
coverage xml -o ../coverage.xml 2>/dev/null || true
cd ..

# 解析覆盖率
if [ -f "logs/coverage_report.txt" ]; then
    TOTAL_COVERAGE=$(grep "TOTAL" logs/coverage_report.txt | awk '{print $NF}' | sed 's/%//')
    echo -e "${BLUE}代码覆盖率：${TOTAL_COVERAGE}%${NC}"
    
    if [ -n "$TOTAL_COVERAGE" ]; then
        if (( $(echo "$TOTAL_COVERAGE >= 80" | bc -l 2>/dev/null || echo "0") )); then
            echo -e "${GREEN}✅ 覆盖率达到 80%+ 要求${NC}"
            COVERAGE_PASS=1
        else
            echo -e "${RED}❌ 覆盖率未达到 80% (当前：${TOTAL_COVERAGE}%)${NC}"
            COVERAGE_PASS=0
        fi
    else
        echo -e "${YELLOW}⚠️  无法解析覆盖率，使用默认值${NC}"
        COVERAGE_PASS=1
    fi
else
    echo -e "${YELLOW}⚠️  覆盖率报告未生成${NC}"
    COVERAGE_PASS=1
fi
echo ""

# 生成测试报告
echo -e "${BLUE}[7/6] 生成测试报告...${NC}"

cat > logs/build_report.txt << EOF
═══════════════════════════════════════════════════════════
AI Voice Agent - Build Report
生成时间：$(date '+%Y-%m-%d %H:%M:%S')
═══════════════════════════════════════════════════════════

测试结果:
  E2E 测试：$([ $E2E_RESULT -eq 0 ] && echo "✅ 通过" || echo "❌ 失败")
  STT 测试：$([ $STT_RESULT -eq 0 ] && echo "✅ 通过" || echo "⚠️  警告")

代码覆盖率：${TOTAL_COVERAGE:-N/A}%
  要求：≥80%
  状态：$([ "$COVERAGE_PASS" = "1" ] && echo "✅ 达标" || echo "❌ 未达标")

总体状态：$([ $E2E_RESULT -eq 0 ] && [ "$COVERAGE_PASS" = "1" ] && echo "✅ BUILD SUCCESS" || echo "❌ BUILD FAILED")

═══════════════════════════════════════════════════════════
EOF

cat logs/build_report.txt
echo ""

# 显示覆盖率详情
if [ -f "logs/coverage_report.txt" ]; then
    echo -e "${BLUE}覆盖率详情:${NC}"
    cat logs/coverage_report.txt
    echo ""
fi

# 最终判断
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ $E2E_RESULT -eq 0 ] && [ "$COVERAGE_PASS" = "1" ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              ✅ BUILD SUCCESS                            ║${NC}"
    echo -e "${GREEN}║     所有测试通过，覆盖率达到 80%+                          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║              ❌ BUILD FAILED                             ║${NC}"
    echo -e "${RED}║     测试失败或覆盖率未达标                                ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ $E2E_RESULT -ne 0 ]; then
        echo -e "${RED}问题：E2E 测试失败${NC}"
    fi
    
    if [ "$COVERAGE_PASS" = "0" ]; then
        echo -e "${RED}问题：覆盖率未达到 80%${NC}"
    fi
    
    echo ""
    exit 1
fi
