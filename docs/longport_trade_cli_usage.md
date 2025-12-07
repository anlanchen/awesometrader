# LongPort 交易账户查询 CLI 使用说明

## 概述

`longport_trade_cli.py` 是一个命令行工具，用于查询 LongPort 交易账户的各种信息，包括账户资金、股票持仓和资金流水。

## 功能特性

- ✅ 查询账户资金信息（支持币种筛选）
- ✅ 查询股票持仓信息（支持股票代码筛选）
- ✅ 查询资金流水记录（支持多种筛选条件）
- ✅ 输出格式化的文本报告
- ✅ 同时保存 JSON 格式数据
- ✅ 详细的日志记录

## 使用方法

### 1. 查询账户资金信息

```bash
# 查询所有币种的账户资金
python tasks/longport_trade_cli.py balance

# 查询美元账户资金
python tasks/longport_trade_cli.py balance --currency USD

# 查询港币账户资金
python tasks/longport_trade_cli.py balance --currency HKD

# 查询离岸人民币账户资金
python tasks/longport_trade_cli.py balance --currency CNH
```

**输出内容包括：**
- 总现金
- 最大融资额
- 剩余融资额
- 风险等级
- 保证金调用
- 净资产
- 初始保证金
- 维持保证金

### 2. 查询股票持仓信息

```bash
# 查询所有持仓
python tasks/longport_trade_cli.py positions

# 查询指定股票的持仓
python tasks/longport_trade_cli.py positions --symbols AAPL.US

# 查询多只股票的持仓
python tasks/longport_trade_cli.py positions --symbols AAPL.US 700.HK TSLA.US
```

**输出内容包括：**
- 股票代码和名称
- 持仓数量
- 可用数量
- 成本价
- 市场信息

### 3. 查询资金流水

```bash
# 查询指定时间段的资金流水
python tasks/longport_trade_cli.py cash-flow --start-date 2024-01-01 --end-date 2024-12-31

# 查询现金类别的流水
python tasks/longport_trade_cli.py cash-flow --start-date 2024-01-01 --end-date 2024-12-31 --business-type 1

# 查询股票类别的流水
python tasks/longport_trade_cli.py cash-flow --start-date 2024-01-01 --end-date 2024-12-31 --business-type 2

# 查询特定股票的流水
python tasks/longport_trade_cli.py cash-flow --start-date 2024-01-01 --end-date 2024-12-31 --symbol AAPL.US

# 分页查询（第2页，每页20条）
python tasks/longport_trade_cli.py cash-flow --start-date 2024-01-01 --end-date 2024-12-31 --page 2 --size 20
```

**参数说明：**
- `--start-date`: 开始日期（必填，格式：YYYY-MM-DD）
- `--end-date`: 结束日期（必填，格式：YYYY-MM-DD）
- `--business-type`: 资金类别（可选）
  - 1: 现金
  - 2: 股票
  - 3: 基金
- `--symbol`: 股票代码（可选）
- `--page`: 页码（可选，默认1）
- `--size`: 每页数量（可选，默认50，范围1-10000）

**输出内容包括：**
- 交易名称
- 流入/流出方向
- 业务类型
- 金额
- 余额
- 股票代码（如适用）
- 交易时间

## 输出文件

所有查询结果会自动保存到 `output/` 目录下：

- **文本格式**: `{command}_{timestamp}.txt` - 易读的格式化文本
- **JSON格式**: `{command}_{timestamp}.json` - 结构化数据，便于程序处理

例如：
- `output/balance_20241207_143025.txt`
- `output/balance_20241207_143025.json`
- `output/positions_20241207_143035.txt`
- `output/positions_20241207_143035.json`
- `output/cash_flow_20241207_143045.txt`
- `output/cash_flow_20241207_143045.json`

## 日志文件

运行日志保存在 `logs/` 目录下：

- 文件名格式: `longport_trade_cli_YYYY-MM-DD.log`
- 日志轮转: 每天一个新文件
- 保留时间: 30天

## 环境配置

使用前需确保已配置 LongPort API 环境变量：

```bash
export LONGPORT_APP_KEY="your_app_key"
export LONGPORT_APP_SECRET="your_app_secret"
export LONGPORT_ACCESS_TOKEN="your_access_token"
```

## 示例输出

### 账户资金查询示例

```
================================================================================
账户资金信息
================================================================================
查询时间: 2024-12-07 14:30:25
币种筛选: USD

账户 1: USD
--------------------------------------------------------------------------------
  总现金:         $120,543.25
  最大融资额:     $240,000.00
  剩余融资额:     $119,456.75
  风险等级:       1
  保证金调用:     $0.00
  净资产:         $125,678.50
  初始保证金:     $5,135.25
  维持保证金:     $2,567.63

================================================================================
```

### 持仓查询示例

```
================================================================================
股票持仓信息
================================================================================
查询时间: 2024-12-07 14:30:35
股票筛选: 全部

账户类型: 现金账户
--------------------------------------------------------------------------------
  股票代码: AAPL.US
  股票名称: 苹果
  持仓数量: 100 股
  可用数量: 100 股
  成本价:   USD 175.50
  市场:     US

  股票代码: 700.HK
  股票名称: 腾讯控股
  持仓数量: 200 股
  可用数量: 200 股
  成本价:   HKD 320.00
  市场:     HK

================================================================================
持仓股票总数: 2
================================================================================
```

## 常见问题

### Q: 如何查看特定币种的账户信息？

A: 使用 `--currency` 参数指定币种，例如：
```bash
python tasks/longport_trade_cli.py balance --currency USD
```

### Q: 如何只查看某几只股票的持仓？

A: 使用 `--symbols` 参数指定股票代码列表，例如：
```bash
python tasks/longport_trade_cli.py positions --symbols AAPL.US 700.HK
```

### Q: 资金流水查询可以跨多长时间？

A: 取决于 LongPort API 的限制，建议查询不超过1年的数据。如需查询更长时间，可以分段查询。

### Q: 输出文件在哪里？

A: 所有输出文件保存在项目根目录下的 `output/` 文件夹中。

## 技术细节

- **Python版本**: Python 3.7+
- **依赖库**: 
  - loguru: 日志记录
  - longport: LongPort OpenAPI SDK
- **日志级别**: INFO
- **编码格式**: UTF-8

## 与其他工具的区别

| 工具 | 用途 | 消息推送 | 行情数据 | 交易日判断 |
|------|------|---------|---------|-----------|
| `run_messager.py` | 定时推送账户报告 | ✅ | ✅ | ✅ |
| `longport_trade_cli.py` | 命令行查询工具 | ❌ | ❌ | ❌ |

`longport_trade_cli.py` 专注于提供简单、直接的查询功能，不包含消息推送、行情数据获取和交易日判断等功能。
