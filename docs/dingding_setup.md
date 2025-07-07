# 钉钉群机器人设置指南

## 🤖 功能介绍

AwesomeTrader现已支持钉钉群机器人消息推送功能，可以实时推送交易提醒、市场行情、系统状态等信息到钉钉群聊。

## 📱 支持的消息类型

1. **文本消息** - 简单的文字通知
2. **Markdown消息** - 支持富文本格式的消息
3. **链接消息** - 带跳转链接的卡片消息
4. **交易提醒** - 专为交易系统设计的提醒消息
5. **市场总结** - 行情数据汇总消息
6. **@功能** - 支持@特定群成员或@所有人

## 🔧 配置步骤

### 第一步：创建钉钉群机器人

1. 在钉钉群聊中，点击右上角"..."菜单
2. 选择"群设置" -> "智能群助手"
3. 点击"添加机器人" -> "自定义"
4. 填写机器人名称（如：AwesomeTrader）
5. 选择安全设置：
   - **自定义关键词**：添加"交易"、"股票"、"行情"等关键词
   - **加签**（推荐）：系统会生成一个密钥
   - **IP地址**：如果服务器IP固定可选择此项

### 第二步：获取配置信息

创建完成后，你会得到：
- **Webhook地址**：形如 `https://oapi.dingtalk.com/robot/send?access_token=xxx`
- **加签密钥**：如果启用了加签功能（可选）

### 第三步：配置环境变量

在你的 `.env` 文件中添加：

```bash
# 钉钉机器人配置
DINGDING_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACCESS_TOKEN
DINGDING_SECRET=YOUR_SECRET_KEY  # 如果启用了加签功能
```

## 💻 使用示例

### 基础用法

```python
from awesometrader.messager import Messager

# 初始化（从环境变量读取配置）
import os
webhook = os.getenv('DINGDING_WEBHOOK')
secret = os.getenv('DINGDING_SECRET')
messager = Messager(dingding_webhook=webhook, dingding_secret=secret)

# 发送简单文本消息
messager.send_dingding_text("交易系统启动成功！")

# 发送@消息
messager.send_dingding_text(
    "重要提醒：AAPL突破关键阻力位！", 
    at_mobiles=["13800138000"]
)
```

### 交易提醒

```python
# 发送交易提醒
messager.send_trading_alert(
    symbol="AAPL.US",
    action="买入",
    price=150.25,
    quantity=100,
    reason="突破重要阻力位，技术指标向好"
)
```

### 市场行情总结

```python
# 发送市场总结
market_data = {
    "涨停股票数": 42,
    "跌停股票数": 8,
    "成交量": "8,520亿",
    "北向资金净流入": "+65.2亿"
}
messager.send_market_summary(market_data)
```

### Markdown格式消息

```python
markdown_content = """
## 📈 今日市场表现

### 美股市场
- **纳斯达克**: +1.2%
- **标普500**: +0.8%

> 数据来源: AwesomeTrader
"""

messager.send_dingding_markdown(
    title="每日市场快报",
    text=markdown_content
)
```

## 🔐 安全说明

1. **Webhook地址保密**：不要在代码中直接写入webhook地址，使用环境变量
2. **关键词过滤**：建议设置自定义关键词，避免垃圾消息
3. **加签验证**：推荐启用加签功能，提高安全性
4. **频率限制**：钉钉机器人有频率限制，建议合理控制发送频率

## 🚀 集成到交易系统

你可以在以下场景中使用钉钉消息推送：

1. **交易信号触发**：当策略产生买卖信号时自动通知
2. **风险预警**：当持仓出现异常波动时及时提醒
3. **每日总结**：交易日结束后推送当日交易总结
4. **系统状态**：数据收集、策略运行等系统状态通知
5. **错误报警**：系统出现异常时的紧急通知

## 📊 消息模板

系统内置了多种消息模板：

- `send_trading_alert()` - 交易提醒模板
- `send_market_summary()` - 市场总结模板
- 你也可以使用 `send_dingding_text()` 和 `send_dingding_markdown()` 自定义消息格式

## 🔧 故障排查

如果消息发送失败，请检查：

1. Webhook地址是否正确
2. 网络连接是否正常
3. 消息内容是否包含设置的关键词
4. 是否触发了频率限制
5. 加签密钥是否正确配置

## 🎯 最佳实践

1. **分类推送**：不同类型的消息使用不同的机器人
2. **优先级设置**：重要消息使用@功能
3. **消息格式**：使用Markdown提升消息可读性
4. **适度推送**：避免过度推送造成信息疲劳 