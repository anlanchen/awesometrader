# AwesomeTrader - 量化交易系统框架

一个基于 Python 的全栈量化交易系统，集成数据获取、策略开发、回测验证、风险控制和实盘交易功能。

## 项目结构

```
awesometrader/
├── awesometrader/             # 核心框架模块
│   ├── datainterface.py       # 数据接口模块，提供数据读取、保存、验证功能
│   ├── collector.py           # 数据收集模块，基于长桥OpenAPI获取实时和历史数据
│   └── utils.py               # 通用工具类，提供路径管理和项目配置功能
├── data_collector.py          # 数据收集器主程序，提供自动化数据收集和定时更新
├── docs/                      # 文档目录
├── strategies/                # 策略实现目录
├── tests/                     # 测试用例目录
├── pyproject.toml             # 项目配置和依赖管理文件
└── README.md                  # 项目说明文档
```
## 技术架构
- **数据源：** 长桥OpenAPI
- **回测引擎：** backtesting.py
- **交易接口：** 长桥OpenAPI
- **风控系统：** 风险控制机制


## 核心功能

### 数据收集器 (data_collector.py)

自动化的股票数据收集系统，支持美股、港股、A股、新加坡股市数据获取和定时更新。

#### 使用方法

**交互模式运行：**
```bash
python data_collector.py
```
**环境配置：** `.env`