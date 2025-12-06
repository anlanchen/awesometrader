# AwesomeTrader - 量化交易系统框架

一个基于Python的全栈量化交易系统，集成数据获取、策略开发、回测验证、风险控制和实盘交易功能，基于长桥OpenAPI打造的专业量化交易平台。

## ✨ 主要特性

### 🔗 多市场数据支持
- **全球市场覆盖**：支持美股(US)、港股(HK)、A股(CN)、新加坡股市(SG)
- **实时数据获取**：基于长桥OpenAPI获取实时行情、历史K线数据
- **多周期支持**：日线、周线、分钟线等多种K线周期
- **数据格式灵活**：支持CSV、Parquet双格式存储，便于数据分析

### 📊 策略开发框架
- **内置技术指标**：集成TA-Lib技术分析库，支持MA、MACD、RSI、MFI等指标
- **策略模板**：提供多种策略模板，包括均线交叉、多因子等策略
- **参数优化**：支持策略参数网格搜索和优化
- **回测验证**：基于backtesting.py框架的专业回测系统

### 💼 实盘交易功能
- **交易接口**：完整的交易功能，支持买入、卖出、撤单、改单
- **多种订单类型**：限价单、市价单、条件单等多种订单类型
- **账户管理**：实时查询账户资金、持仓信息
- **风险控制**：内置风险管理机制

### 🤖 自动化数据收集
- **定时更新**：支持多市场交易时段自动数据更新
- **股票池管理**：自选股同步，股票池自动维护
- **数据验证**：数据完整性检查和异常处理
- **环境配置**：灵活的环境变量配置

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Make (可选，用于便捷安装)

### 安装步骤

推荐使用 `make` 命令进行一键安装（自动配置 uv 包管理器和虚拟环境）：

```bash
make install
```

或者手动安装依赖：

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建并激活虚拟环境
uv venv --python 3.10
source .venv/bin/activate

# 同步依赖
uv sync
```

## 📖 使用指南

### 1. 数据收集
运行数据收集器，自动从长桥更新股票池数据：

```bash
python run_collector.py
```

### 2. 策略回测
编写或选择策略后，运行回测脚本（示例）：

```bash
# 运行策略回测示例（需自行编写或调整具体脚本）
python strategies/sma_cross.py
```

### 3. 实盘/模拟交易
配置好长桥 API 密钥后，启动交易程序：

```bash
python run_trader.py
```

### 4. 消息通知
测试钉钉消息通知功能：

```bash
python run_messager.py
```

## 📁 项目结构

```text
awesometrader/
├── awesometrader/             # 核心框架包
│   ├── __init__.py            # 导出主要类 (DataInterface, LongPortAPI, etc.)
│   ├── collector/             # 数据收集模块
│   │   └── longport_api.py    # 长桥OpenAPI数据接口实现
│   ├── data/                  # 数据管理模块
│   │   └── data_interface.py  # 数据读写、验证接口
│   ├── notify/                # 消息通知模块
│   │   └── dingtalk_messager.py # 钉钉机器人通知实现
│   ├── trader/                # 交易执行模块
│   │   └── longport_trader_api.py # 长桥交易接口实现
│   ├── utils/                 # 通用工具模块
│   │   └── utils.py           # 路径管理、配置加载等工具
│   └── tests/                 # 单元测试
├── strategies/                # 策略实现目录
│   ├── sma.py                 # 简单移动平均策略
│   ├── sma_cross.py           # 双均线交叉策略
│   ├── macd.py                # MACD策略
│   ├── mfi.py                 # 资金流量指标策略
│   └── multi_factor.py        # 多因子综合策略
├── caches/                    # 数据缓存目录 (CSV/Parquet)
├── results/                   # 回测结果目录 (HTML报告/CSV统计)
├── logs/                      # 运行日志目录
├── docs/                      # 文档目录
├── run_collector.py           # 数据收集启动脚本
├── run_trader.py              # 交易程序启动脚本
├── run_messager.py            # 消息测试启动脚本
├── pyproject.toml             # 项目配置和依赖管理
├── Makefile                   # 项目管理命令
└── README.md                  # 项目说明文档
```

## 🛠 技术架构

### 核心技术栈
- **Python 3.10+**：核心开发语言
- **长桥OpenAPI (longport)**：官方 SDK，提供行情和交易接口
- **backtesting.py**：轻量级、功能强大的回测引擎
- **TA-Lib**：金融市场数据的技术分析库
- **pandas**：高性能数据处理和分析
- **uv**：极速 Python 包管理器和项目管理工具

### 依赖库
主要依赖项定义在 `pyproject.toml` 中，通过 `uv` 进行管理。

```toml
dependencies = [
    "pandas",           # 数据处理
    "numpy",            # 数值计算
    "ta-lib",           # 技术分析
    "requests",         # HTTP请求
    "humanize",         # 人性化显示
    "loguru",           # 日志管理
    "schedule",         # 定时任务
    "python-dotenv",    # 环境变量
    "pyarrow",          # Parquet支持
    "longport",         # 长桥OpenAPI
    "backtesting"       # 回测框架
]
```
