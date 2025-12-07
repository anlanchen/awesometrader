"""
测试DingTalkMessager类的消息发送功能 - 简单真实接口测试
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from datetime import datetime, date
from loguru import logger
from awesometrader.notify import DingTalkMessager
import time


class TestMessageModule(unittest.TestCase):
    def setUp(self):
        """每个测试方法之前运行"""
        # 初始化消息接口
        self.webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=3fede205bc3f924ee019abd045523bbccd75009b0bd32e976e1e86a51108edca"
        self.secret = "SEC38b3260cdbd3ec2ddd153cb1c80ed8f73aedcfc801c907e5d86a1779d9a119eb"
        self.messager = DingTalkMessager(dingtalk_webhook=self.webhook_url, dingtalk_secret=self.secret)
        
    def tearDown(self):
        """每个测试方法之后运行"""
        pass
    
    def test_send_trading_notification(self):
        """测试发送交易通知消息"""
        logger.info("=== 测试交易通知功能 ===")
        
        # 测试买入通知
        logger.info("发送买入通知...")
        result = self.messager.send_trading_notification(
            symbol="BABA.US",
            action="买入",
            price=85.67,
            quantity=100,
            reason="技术指标显示买入信号"
        )
        self.assertTrue(result, "买入通知发送失败")
        logger.success("✓ 买入通知发送成功")
        
        # 等待避免频率限制
        time.sleep(1)
        
        # 测试卖出通知
        logger.info("发送卖出通知...")
        result = self.messager.send_trading_notification(
            symbol="BABA.US",
            action="卖出",
            price=85.30,
            quantity=50,
            reason="达到止盈目标"
        )
        self.assertTrue(result, "卖出通知发送失败")
        logger.success("✓ 卖出通知发送成功")
        
        logger.success("=== 交易通知测试完成 ===")
    
    def test_send_market_close_summary(self):
        """测试发送市场收市总结消息"""
        logger.info("=== 测试市场收市总结功能 ===")
        
        # 准备市场总结数据
        summary_data = {
            "交易总数": "5",
            "今日收益": "+2.35%",
            "累计收益": "+15.67%",
            "当前仓位": "BABA.US"
        }
        
        logger.info("发送市场收市总结...")
        result = self.messager.send_market_close_summary(summary_data)
        self.assertTrue(result, "市场收市总结发送失败")
        logger.success("✓ 市场收市总结发送成功")
        
        logger.success("=== 市场收市总结测试完成 ===")


if __name__ == '__main__':
    # 配置日志
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    logger.info("=== 开始消息功能测试 ===")
    logger.info("测试将发送真实钉钉消息")
    
    # 运行测试
    unittest.main(verbosity=2)
