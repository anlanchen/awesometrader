# Web 应用启动指南

本文档说明如何启动 AwesomeTrader 的 Web 分析服务，包括 Backend API 服务和 Frontend 前端界面。

## 📋 前置条件

### Python 环境
确保已安装 Python 3.10+ 并完成项目依赖安装：

```bash
# 一键安装（推荐）
make install

# 或手动安装
uv venv --python 3.10
source .venv/bin/activate
uv sync
```

### Node.js 环境
Frontend 需要 Node.js 环境（建议 v18+）：

```bash
# 检查 Node.js 版本
node -v

# 检查 npm 版本
npm -v
```

---

## 🚀 启动 Backend

Backend 是基于 FastAPI 构建的 API 服务，提供账户收益分析、风控指标、基准对比等功能。

### 方式一：使用 uvicorn（推荐）

```bash
# 在项目根目录执行
uvicorn webapp.backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 方式二：直接运行模块

```bash
# 在项目根目录执行
python -m webapp.backend.main
```

### 服务信息

启动成功后，可以访问：

| 服务 | 地址 |
|------|------|
| API 根路径 | http://localhost:8000 |
| Swagger 文档 | http://localhost:8000/docs |
| ReDoc 文档 | http://localhost:8000/redoc |
| 健康检查 | http://localhost:8000/health |

### 配置说明

- **端口**: 默认 8000
- **数据源**: 自动从 `caches/account.csv` 加载账户数据
- **文件监控**: 启动时会自动监控 `account.csv` 文件变更，实时更新数据

---

## 🎨 启动 Frontend

Frontend 是基于 Vite + React + TypeScript 构建的现代化前端界面。

### 步骤 1：安装依赖

```bash
# 进入 frontend 目录
cd webapp/frontend

# 安装 npm 依赖
npm install
```

### 步骤 2：启动开发服务器

```bash
# 在 webapp/frontend 目录下执行
npm run dev
```

### 服务信息

启动成功后，终端会显示访问地址，通常是：

| 服务 | 地址 |
|------|------|
| 本地访问 | http://localhost:5173 |
| 网络访问 | http://<your-ip>:5173 |

### 其他命令

```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

---

## 🔄 一键启动/重启（推荐）

项目提供了一键启动脚本，自动检测并重启前后端服务：

### 启动服务

```bash
# 在项目根目录执行
./start_webapp.sh
```

脚本会自动：
1. 检测端口 8000 (Backend) 和 5173 (Frontend) 是否被占用
2. 如果有旧服务在运行，自动 kill 掉
3. 启动 Backend 和 Frontend 服务
4. 显示服务状态和访问地址

### 停止服务

```bash
# 在项目根目录执行
./stop_webapp.sh
```

### 日志文件

服务日志保存在 `logs/` 目录：
- `logs/backend.log` - Backend 日志
- `logs/frontend.log` - Frontend 日志

---

## 🔄 手动启动 Backend 和 Frontend

如果需要手动启动，可以使用两个终端窗口分别启动：

### 终端 1：启动 Backend

```bash
cd /path/to/awesometrader
source .venv/bin/activate
uvicorn webapp.backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 终端 2：启动 Frontend

```bash
cd /path/to/awesometrader/webapp/frontend
npm run dev
```

---

## ❓ 常见问题

### Q: Backend 启动报错 "Module not found"
A: 确保在项目根目录执行命令，并且已激活虚拟环境：
```bash
source .venv/bin/activate
```

### Q: Frontend 启动报错 "Cannot find module"
A: 确保已安装依赖：
```bash
cd webapp/frontend
npm install
```

### Q: Frontend 无法连接 Backend API
A: 
1. 确保 Backend 已启动且运行在 8000 端口
2. 检查 Frontend 的 API 配置（`webapp/frontend/services/api.ts`）

### Q: 账户数据显示为空
A: 确保 `caches/account.csv` 文件存在且格式正确。可以先运行账户数据收集任务：
```bash
python tasks/account_reporter.py
```

---

## 📁 相关文件

| 文件/目录 | 说明 |
|-----------|------|
| `start_webapp.sh` | 一键启动脚本（自动重启服务） |
| `stop_webapp.sh` | 停止服务脚本 |
| `logs/` | 服务日志目录 |
| `webapp/backend/main.py` | Backend 入口文件 |
| `webapp/backend/config.py` | Backend 配置 |
| `webapp/frontend/` | Frontend 源代码 |
| `webapp/frontend/package.json` | Frontend 依赖配置 |
| `caches/account.csv` | 账户数据文件 |
