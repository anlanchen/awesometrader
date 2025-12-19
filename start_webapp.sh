#!/bin/bash
# ============================================================================
# AwesomeTrader Web 应用启动脚本
# 自动检测并重启 Backend (FastAPI) 和 Frontend (Vite) 服务
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

# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  AwesomeTrader Web 应用启动脚本${NC}"
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

# 杀掉指定端口的进程
kill_port() {
    local port=$1
    local service_name=$2
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}⚠️  检测到 $service_name 已在端口 $port 运行，正在停止...${NC}"
        for pid in $pids; do
            kill -9 $pid 2>/dev/null || true
            echo -e "   已终止进程 PID: $pid"
        done
        sleep 1
        echo -e "${GREEN}✅ $service_name 已停止${NC}"
    else
        echo -e "${GREEN}✅ 端口 $port 空闲${NC}"
    fi
}

# 启动 Backend
start_backend() {
    echo ""
    echo -e "${BLUE}🚀 启动 Backend (FastAPI)...${NC}"
    
    # 确定 Python 路径（优先使用虚拟环境）
    if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
        PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
        echo -e "   使用虚拟环境: .venv"
    else
        PYTHON_BIN="python"
        echo -e "   使用系统 Python"
    fi
    
    # 后台启动 uvicorn（直接使用虚拟环境的 python）
    nohup $PYTHON_BIN -m uvicorn webapp.backend.main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        > "$LOG_DIR/backend.log" 2>&1 &
    
    local backend_pid=$!
    echo $backend_pid > "$LOG_DIR/backend.pid"
    
    # 等待服务启动
    sleep 3
    
    # 检查是否启动成功
    if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend 启动成功${NC}"
        echo -e "   PID: $backend_pid"
        echo -e "   地址: http://localhost:$BACKEND_PORT"
        echo -e "   文档: http://localhost:$BACKEND_PORT/docs"
        echo -e "   日志: $LOG_DIR/backend.log"
    else
        echo -e "${RED}❌ Backend 启动失败，请查看日志: $LOG_DIR/backend.log${NC}"
        return 1
    fi
}

# 启动 Frontend
start_frontend() {
    echo ""
    echo -e "${BLUE}🎨 启动 Frontend (Vite)...${NC}"
    
    cd "$SCRIPT_DIR/webapp/frontend"
    
    # 检查依赖是否安装
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}   正在安装 npm 依赖...${NC}"
        npm install --silent
    fi
    
    # 后台启动 vite
    nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    
    local frontend_pid=$!
    echo $frontend_pid > "$LOG_DIR/frontend.pid"
    
    # 等待服务启动
    sleep 3
    
    # 检查是否启动成功
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend 启动成功${NC}"
        echo -e "   PID: $frontend_pid"
        echo -e "   地址: http://localhost:$FRONTEND_PORT"
        echo -e "   日志: $LOG_DIR/frontend.log"
    else
        echo -e "${RED}❌ Frontend 启动失败，请查看日志: $LOG_DIR/frontend.log${NC}"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
}

# 显示服务状态
show_status() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${GREEN}🎉 Web 应用已启动！${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo -e "  ${GREEN}Frontend:${NC}  http://localhost:$FRONTEND_PORT"
    echo -e "  ${GREEN}Backend:${NC}   http://localhost:$BACKEND_PORT"
    echo -e "  ${GREEN}API 文档:${NC}  http://localhost:$BACKEND_PORT/docs"
    echo ""
    echo -e "${YELLOW}提示: 使用 ./stop_webapp.sh 停止服务${NC}"
    echo ""
}

# ============================================================================
# 环境变量检查
# ============================================================================

check_env_vars() {
    echo -e "${BLUE}🔐 检查认证环境变量...${NC}"
    
    local missing_vars=()
    
    if [ -z "$SECRET_KEY" ]; then
        missing_vars+=("SECRET_KEY")
    fi
    
    if [ -z "$ADMIN_USERNAME" ]; then
        missing_vars+=("ADMIN_USERNAME")
    fi
    
    if [ -z "$ADMIN_PASSWORD_HASH" ]; then
        missing_vars+=("ADMIN_PASSWORD_HASH")
    fi
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo -e "${RED}❌ 缺少必需的环境变量:${NC}"
        for var in "${missing_vars[@]}"; do
            echo -e "   - $var"
        done
        echo ""
        echo -e "${YELLOW}请参考文档配置环境变量: docs/webapp_setup.md${NC}"
        echo ""
        exit 1
    fi
    
    echo -e "${GREEN}✅ 环境变量检查通过${NC}"
}

# ============================================================================
# 主流程
# ============================================================================

# 0. 检查环境变量
check_env_vars

# 1. 停止已有服务
echo -e "${BLUE}📋 检查现有服务...${NC}"
kill_port $BACKEND_PORT "Backend"
kill_port $FRONTEND_PORT "Frontend"

# 2. 启动服务
start_backend
start_frontend

# 3. 显示状态
show_status
