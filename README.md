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

## 📁 项目结构

```
awesometrader/
├── awesometrader/             # 核心框架模块
│   ├── __init__.py            # 模块初始化，导出主要类
│   ├── datainterface.py       # 数据接口模块，提供数据读取、保存、验证功能
│   ├── collector.py           # 数据收集模块，基于长桥OpenAPI获取实时和历史数据
│   ├── trader.py              # 交易模块，提供完整的交易功能接口
│   └── utils.py               # 通用工具类，提供路径管理和项目配置功能
├── data_collector.py          # 数据收集器主程序，提供自动化数据收集和定时更新
├── strategies/                # 策略实现目录
│   ├── sma.py                 # 简单移动平均策略
│   ├── sma_cross.py           # 双均线交叉策略
│   ├── macd.py                # MACD策略
│   ├── mfi.py                 # 资金流量指标策略
│   └── multi_factor.py        # 多因子综合策略
├── tests/                     # 测试用例目录
│   ├── test_data_simple.py    # 数据模块测试
│   └── test_trade_simple.py   # 交易模块测试
├── caches/                    # 数据缓存目录
├── results/                   # 回测结果目录
├── logs/                      # 日志目录
├── docs/                      # 文档目录
├── pyproject.toml             # 项目配置和依赖管理文件
└── README.md                  # 项目说明文档
```

## 🛠 技术架构

### 核心技术栈
- **Python 3.10+**：核心开发语言
- **长桥OpenAPI**：数据源和交易接口
- **backtesting.py**：专业回测引擎
- **TA-Lib**：技术分析指标库
- **pandas**：数据处理和分析
- **loguru**：日志管理

### 依赖库
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