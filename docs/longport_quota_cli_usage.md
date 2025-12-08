# LongPort 行情数据收集 CLI 使用说明

## 概述

`longport_quota_cli.py` 是一个命令行工具，用于管理股票池和收集 LongPort 行情数据，包括同步自选股、获取历史K线数据和更新最新数据等功能。

## 功能特性

- ✅ 同步 LongPort 自选股到本地股票池
- ✅ 获取股票历史K线数据
- ✅ 更新股票最新K线数据
- ✅ 查看各市场交易时段
- ✅ 支持多市场（美股、港股、A股、新加坡）
- ✅ 支持多种K线周期（日线、周线、月线、年线）
- ✅ 自动前复权处理
- ✅ 详细的日志记录

## 使用方法

### 1. 查看交易时段 (show_sessions)

查看各市场的交易时段信息。

```bash
python tasks/longport_quota_cli.py show_sessions
```

**输出内容包括：**
- 各市场的开盘/收盘时间
- 盘前盘后交易时段（如适用）

### 2. 同步自选股 (sync_watchlist)

将 LongPort 账户中的自选股同步到本地 `stock_pool.csv` 文件。

```bash
python tasks/longport_quota_cli.py sync_watchlist
```

**功能说明：**
- 从 LongPort 获取自选股列表
- 获取股票基础信息（包括中文名称）
- 保存到 `stock_pool.csv` 文件
- 文件格式包含：`stock_code`（股票代码）、`stock_name`（股票名称）

### 3. 获取历史数据 (get_history)

从指定起始日期获取股票池中股票的历史K线数据。

```bash
# 获取所有市场的日线历史数据
python tasks/longport_quota_cli.py get_history

# 获取美股的日线历史数据
python tasks/longport_quota_cli.py get_history --market US

# 获取港股的周线历史数据
python tasks/longport_quota_cli.py get_history --market HK --period Week

# 获取A股的月线历史数据
python tasks/longport_quota_cli.py get_history --market CN --period Month
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--market` | 字符串 | ALL | 市场代码 (US/HK/CN/SG/ALL) |
| `--period` | 字符串 | Day | K线周期 (Day/Week/Month/Year) |

**市场代码说明：**

| 代码 | 说明 | 股票代码示例 |
|------|------|-------------|
| US | 美国股市 | AAPL.US, TSLA.US |
| HK | 香港股市 | 700.HK, 9988.HK |
| CN | 中国A股 | 600519.SH, 000001.SZ |
| SG | 新加坡股市 | D05.SG |
| ALL | 所有市场 | - |

**数据说明：**
- 起始日期默认为 2020-01-01
- 结束日期为当前日期
- 数据自动进行前复权处理
- 数据保存为 CSV 格式

### 4. 更新最新数据 (update_latest)

更新股票池中股票的最新K线数据（增量更新）。

```bash
# 更新所有市场的日线数据
python tasks/longport_quota_cli.py update_latest

# 更新美股的日线数据
python tasks/longport_quota_cli.py update_latest --market US

# 更新港股的周线数据
python tasks/longport_quota_cli.py update_latest --market HK --period Week
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--market` | 字符串 | ALL | 市场代码 (US/HK/CN/SG/ALL) |
| `--period` | 字符串 | Day | K线周期 (Day/Week/Month/Year) |

**与 get_history 的区别：**
- `get_history`: 强制覆盖历史数据，适合首次获取或重新获取完整数据
- `update_latest`: 增量更新，只追加新数据，适合日常更新

## 输出文件

### 股票池文件

位置：`stock_pool.csv`

格式示例：
```csv
stock_code,stock_name
AAPL.US,苹果
700.HK,腾讯控股
600519.SH,贵州茅台
```

### 历史数据文件

位置：`data/{stock_code}/{period}/` 目录下

例如：
- `data/AAPL.US/Day/AAPL.US.csv`
- `data/700.HK/Week/700.HK.csv`

数据格式包含：
- 日期 (date)
- 开盘价 (open)
- 最高价 (high)
- 最低价 (low)
- 收盘价 (close)
- 成交量 (volume)
- 成交额 (turnover)

## 日志文件

运行日志保存在 `logs/` 目录下：

- 文件名格式: `longport_quota_cli_YYYY-MM-DD.log`
- 日志轮转: 每天一个新文件
- 保留时间: 30天

## 环境配置

使用前需确保已配置 LongPort API 环境变量：

```bash
export LONGPORT_APP_KEY="your_app_key"
export LONGPORT_APP_SECRET="your_app_secret"
export LONGPORT_ACCESS_TOKEN="your_access_token"
```

## 使用示例

### 典型工作流程

```bash
# 1. 首先同步自选股到本地股票池
python tasks/longport_quota_cli.py sync_watchlist

# 2. 获取所有股票的历史数据（首次使用）
python tasks/longport_quota_cli.py get_history

# 3. 之后每天更新最新数据
python tasks/longport_quota_cli.py update_latest
```

### 按市场分别处理

```bash
# 美股交易日结束后更新美股数据
python tasks/longport_quota_cli.py update_latest --market US

# 港股交易日结束后更新港股数据
python tasks/longport_quota_cli.py update_latest --market HK
```

### 获取不同周期数据

```bash
# 获取日线数据
python tasks/longport_quota_cli.py get_history --period Day

# 获取周线数据
python tasks/longport_quota_cli.py get_history --period Week

# 获取月线数据
python tasks/longport_quota_cli.py get_history --period Month
```

## 常见问题

### Q: 如何添加新股票到股票池？

A: 有两种方式：
1. 在 LongPort App 中将股票添加到自选股，然后执行 `sync_watchlist`
2. 手动编辑 `stock_pool.csv` 文件，添加股票代码和名称

### Q: 为什么某些股票获取数据失败？

A: 可能的原因：
- 股票代码格式错误（需要包含市场后缀，如 `.US`、`.HK`）
- 股票已退市或更换代码
- API 请求频率限制（工具已内置 0.5 秒延迟）
- LongPort 行情权限不足

### Q: 历史数据从什么时候开始？

A: 默认从 2020-01-01 开始获取历史数据。如需修改，可以编辑 `LongPortQuotaCLI` 类中的 `start_date_str` 属性。

### Q: 数据是否已复权处理？

A: 是的，所有数据默认使用前复权（Forward Adjust）处理。

### Q: 如何查看当前股票池有哪些股票？

A: 直接查看项目根目录下的 `stock_pool.csv` 文件。

### Q: update_latest 和 get_history 有什么区别？

A: 
- `get_history`: 获取完整历史数据，会覆盖已有文件
- `update_latest`: 增量更新，只添加新数据到现有文件末尾

## 技术细节

- **Python版本**: Python 3.7+
- **依赖库**: 
  - loguru: 日志记录
  - longport: LongPort OpenAPI SDK
  - pandas: 数据处理
- **日志级别**: INFO
- **编码格式**: UTF-8
- **API 频率限制**: 每个请求间隔 0.5 秒

## 与其他工具的区别

| 工具 | 用途 | 历史数据 | 实时报价 | 账户信息 |
|------|------|---------|---------|----------|
| `longport_quota_cli.py` | 行情数据收集 | ✅ | ❌ | ❌ |
| `longport_trade_cli.py` | 账户指标查询 | ❌ | ✅ | ✅ |
| `run_messager.py` | 定时推送报告 | ❌ | ✅ | ✅ |

`longport_quota_cli.py` 专注于股票池管理和历史K线数据收集，为量化分析和策略回测提供数据支持。
