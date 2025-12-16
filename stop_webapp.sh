#!/bin/bash
# ============================================================================
# AwesomeTrader Web 应用停止脚本
# ============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  AwesomeTrader Web 应用停止脚本${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 杀掉指定端口的进程
kill_port() {
    local port=$1
    local service_name=$2
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}⏹️  正在停止 $service_name (端口 $port)...${NC}"
        for pid in $pids; do
            kill -9 $pid 2>/dev/null || true
            echo -e "   已终止进程 PID: $pid"
        done
        echo -e "${GREEN}✅ $service_name 已停止${NC}"
    else
        echo -e "${GREEN}✅ $service_name 未运行${NC}"
    fi
}

# 停止服务
kill_port $BACKEND_PORT "Backend"
kill_port $FRONTEND_PORT "Frontend"

# 清理 PID 文件
rm -f "$SCRIPT_DIR/logs/backend.pid" 2>/dev/null
rm -f "$SCRIPT_DIR/logs/frontend.pid" 2>/dev/null

echo ""
echo -e "${GREEN}🎉 所有服务已停止${NC}"
echo ""
