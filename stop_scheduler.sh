#!/bin/bash
# ============================================================================
# AwesomeTrader Scheduler 停止脚本
# ============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PID 文件
PID_FILE="$SCRIPT_DIR/logs/scheduler.pid"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  AwesomeTrader Scheduler 停止脚本${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 停止 Scheduler
stop_scheduler() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ]; then
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}⏹️  正在停止 Scheduler (PID: $pid)...${NC}"
                kill "$pid" 2>/dev/null || true
                sleep 2
                # 如果还没停止，强制杀掉
                if kill -0 "$pid" 2>/dev/null; then
                    echo -e "${YELLOW}   进程未响应，强制终止...${NC}"
                    kill -9 "$pid" 2>/dev/null || true
                fi
                echo -e "${GREEN}✅ Scheduler 已停止${NC}"
            else
                echo -e "${GREEN}✅ Scheduler 未运行 (PID $pid 不存在)${NC}"
            fi
        fi
        rm -f "$PID_FILE"
    else
        echo -e "${GREEN}✅ Scheduler 未运行 (PID 文件不存在)${NC}"
    fi
}

# 停止服务
stop_scheduler

echo ""
echo -e "${GREEN}🎉 Scheduler 已停止${NC}"
echo ""

