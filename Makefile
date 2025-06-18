# AwesomeTrader Makefile
# 最极简版 - 只关注核心依赖管理

.PHONY: help install clean sync

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# 项目配置
PYTHON_VERSION := 3.10

help: ## 显示帮助信息
	@echo "$(BLUE)AwesomeTrader - 量化交易系统$(RESET)"
	@echo ""
	@echo "$(GREEN)可用命令:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-10s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## 一键安装 - 自动安装uv、设置环境并安装所有依赖
	@echo "$(BLUE)开始一键安装...$(RESET)"
	@echo "$(BLUE)1. 检查uv安装状态...$(RESET)"
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "$(YELLOW)uv未安装，正在自动安装...$(RESET)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "$(GREEN)✓ uv安装完成$(RESET)"; \
	else \
		echo "$(GREEN)✓ uv已安装$(RESET)"; \
	fi
	@echo "$(BLUE)2. 创建Python虚拟环境...$(RESET)"
	@uv venv --python $(PYTHON_VERSION)
	@echo "$(GREEN)✓ 虚拟环境创建完成$(RESET)"
	@echo "$(BLUE)3. 激活虚拟环境...$(RESET)"
	@. .venv/bin/activate
	@echo "$(GREEN)✓ 虚拟环境已激活$(RESET)"
	@echo "$(BLUE)4. 同步项目依赖...$(RESET)"
	@uv sync
	@echo "$(GREEN)✓ 依赖同步完成$(RESET)"
	@echo ""
	@echo "$(GREEN)========================================$(RESET)"
	@echo "$(GREEN)  AwesomeTrader 安装完成!$(RESET)"
	@echo "$(GREEN)========================================$(RESET)"
	@echo ""
	@echo "$(GREEN)虚拟环境已激活，现在可以运行:$(RESET)"
	@echo "  $(YELLOW)python data_collector.py$(RESET)         # 运行数据收集器"
	@echo ""
	@echo "$(BLUE)或者直接使用uv运行:$(RESET)"
	@echo "  $(YELLOW)uv run python data_collector.py$(RESET)  # 使用uv直接运行"

sync: ## 同步项目依赖
	@echo "$(BLUE)同步项目依赖...$(RESET)"
	@uv sync
	@echo "$(GREEN)✓ 依赖同步完成$(RESET)"

clean: ## 清理构建文件和虚拟环境
	@echo "$(BLUE)清理项目...$(RESET)"
	@rm -rf .venv
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@rm -f uv.lock
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@echo "$(GREEN)✓ 清理完成$(RESET)" 