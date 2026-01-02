#!/bin/bash
# ============================================================================
# AwesomeTrader Scheduler 启动脚本
# 后台运行任务调度器
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日志目录
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# PID 文件
PID_FILE="$LOG_DIR/scheduler.pid"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  AwesomeTrader Scheduler 启动脚本${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================================================
# 加载 .env 文件（如果存在）
# ============================================================================

if [ -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${BLUE}📁 加载 .env 文件...${NC}"
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
    echo -e "${GREEN}✅ .env 文件已加载${NC}"
    echo ""
fi

# ============================================================================
# 函数定义
# ============================================================================

# 检查 Scheduler 是否已在运行
check_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            return 0  # 正在运行
        fi
    fi
    return 1  # 未运行
}

# 停止已有的 Scheduler
stop_existing() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  检测到 Scheduler 已在运行 (PID: $pid)，正在停止...${NC}"
            kill "$pid" 2>/dev/null || true
            sleep 2
            # 如果还没停止，强制杀掉
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
            echo -e "${GREEN}✅ 已停止旧的 Scheduler${NC}"
        fi
        rm -f "$PID_FILE"
    fi
}

# 启动 Scheduler
start_scheduler() {
    echo ""
    echo -e "${BLUE}🚀 启动 Scheduler...${NC}"
    
    # 确定 Python 路径（优先使用虚拟环境）
    if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
        PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
        echo -e "   使用虚拟环境: .venv"
    else
        PYTHON_BIN="python"
        echo -e "   使用系统 Python"
    fi
    
    # 日志文件路径（由 loguru 自动写入）
    TODAY=$(date +%Y-%m-%d)
    LOG_FILE="$LOG_DIR/scheduler_$TODAY.log"
    
    # 后台启动 Scheduler
    # stdout 丢弃（loguru 已直接写日志文件），stderr 重定向到日志
    nohup $PYTHON_BIN -u run_scheduler.py > /dev/null 2>> "$LOG_FILE" &
    
    local scheduler_pid=$!
    echo $scheduler_pid > "$PID_FILE"
    
    # 等待一会儿检查是否启动成功
    sleep 2
    
    # 检查进程是否还在运行
    if kill -0 "$scheduler_pid" 2>/dev/null; then
        echo -e "${GREEN}✅ Scheduler 启动成功${NC}"
        echo -e "   PID: $scheduler_pid"
        echo -e "   日志: $LOG_FILE"
    else
        echo -e "${RED}❌ Scheduler 启动失败，请查看日志: $LOG_FILE${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 显示状态
show_status() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${GREEN}🎉 Scheduler 已在后台运行！${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo -e "${YELLOW}提示:${NC}"
    echo -e "  - 查看日志: tail -f logs/scheduler_$(date +%Y-%m-%d).log"
    echo -e "  - 停止服务: ./stop_scheduler.sh"
    echo ""
}

# ============================================================================
# 主流程
# ============================================================================

# 1. 停止已有的 Scheduler（如果正在运行）
stop_existing

# 2. 启动 Scheduler
start_scheduler

# 3. 显示状态
show_status

