# Web 应用部署指南

## 快速开始

### 1. 安装依赖

```bash
# Python 依赖（项目根目录）
make install

# 前端依赖
cd webapp/frontend && npm install
```

### 2. 配置认证（必需）

#### 生成 JWT 密钥

```bash
# 方法 1：使用 Python
python -c "import secrets; print(secrets.token_hex(32))"

# 方法 2：使用 openssl
openssl rand -hex 32
```

#### 生成密码哈希

```bash
# 使用 bcrypt 生成密码哈希（替换 your-password 为你的密码）
python -c "import bcrypt; print(bcrypt.hashpw('your-password'.encode(), bcrypt.gensalt()).decode())"

# 示例输出：$2b$12$xGTe3WqHF54ezlaOOYZTNOkH.gzBHSShJp5TsnS8rb3h3G5KwqeF.
```

#### 创建 .env 文件

> ⚠️ **重要**：bcrypt 哈希包含 `$` 符号，在 shell 中会被解释为变量。**必须用单引号包裹密码哈希**！

```bash
cat > .env << 'EOF'
# JWT 签名密钥（使用上面生成的随机密钥）
SECRET_KEY=your-random-secret-key-here

# 管理员用户名
ADMIN_USERNAME=admin

# 管理员密码哈希（必须用单引号包裹！）
ADMIN_PASSWORD_HASH='$2b$12$xxxxxx...'
EOF
```

#### 完整示例

```bash
# 一键生成配置（密码设为 admin123）
SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
HASH=$(python -c "import bcrypt; print(bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode())")

# 注意：密码哈希必须用单引号包裹，防止 $ 被解释
cat > .env << EOF
SECRET_KEY=$SECRET
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH='$HASH'
EOF

echo "✅ .env 文件已生成，用户名: admin，密码: admin123"
```

| 变量 | 说明 |
|------|------|
| `SECRET_KEY` | JWT 签名密钥（必须设置） |
| `ADMIN_USERNAME` | 登录用户名 |
| `ADMIN_PASSWORD_HASH` | bcrypt 密码哈希（必须设置） |
| `AUTH_ENABLED` | 设为 `false` 可禁用认证（仅开发环境） |

### 3. 启动服务

```bash
./start_webapp.sh
```

### 4. 访问应用

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:3000 |
| API 文档 | http://localhost:8000/docs |

---

## 手动启动

如需分别启动前后端：

```bash
# 终端 1：启动 Backend
uvicorn webapp.backend.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2：启动 Frontend
cd webapp/frontend && npm run dev
```

停止服务：
```bash
./stop_webapp.sh
```

---

## 生产环境部署

### 1. 创建环境配置

```bash
# 生成强密码和密钥（不要提交到 Git）
SECRET=$(openssl rand -hex 32)
HASH=$(python -c "import bcrypt; print(bcrypt.hashpw('YourStrongPassword'.encode(), bcrypt.gensalt()).decode())")

# 注意：密码哈希必须用单引号包裹
cat > .env << EOF
SECRET_KEY=$SECRET
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH='$HASH'
AUTH_ENABLED=true
EOF
```

### 2. 启动脚本

```bash
#!/bin/bash
set -a && source .env && set +a
uvicorn webapp.backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. 安全建议

- ✅ 修改默认密码和 JWT 密钥
- ✅ 使用 HTTPS（通过 Nginx 配置 SSL）
- ✅ 限制 CORS 域名（修改 `main.py` 中的 `allow_origins`）

---

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| Backend 报错 "Module not found" | 激活虚拟环境：`source .venv/bin/activate` |
| Frontend 报错 "Cannot find module" | 安装依赖：`cd webapp/frontend && npm install` |
| 无法连接 API | 确保 Backend 在 8000 端口运行 |
| 数据显示为空 | 运行 `python tasks/account_reporter.py` 生成数据 |
| 忘记密码 | 重新设置 `ADMIN_PASSWORD_HASH` 并重启 |
| 登录报错 "Invalid salt" | 密码哈希必须用单引号包裹：`ADMIN_PASSWORD_HASH='$2b$...'` |

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `start_webapp.sh` | 一键启动脚本 |
| `stop_webapp.sh` | 停止服务脚本 |
| `logs/` | 日志目录 |
| `webapp/backend/config.py` | 后端配置 |
| `caches/account.csv` | 账户数据 |
