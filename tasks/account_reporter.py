#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
账户报告器 - 钉钉通知模块

"""

import os
import sys
from datetime import date
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from awesometrader.notify import DingTalkMessager
from awesometrader.utils import Utils


class AccountReporter:
    """账户信息报告器 - 钉钉通知"""
    
    def __init__(self):
        """初始化账户报告器"""
        # 缓存目录
        cache_dir = Utils.get_cache_dir()
        
        # 账户数据目录
        self.account_dir = cache_dir / 'account'
        
        # 钉钉配置
        self.webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=31017c949ed2c36aa3cdad026f5ff29ea44b38633b26ce90e0197d092191b963"
        self.secret = "SECab458845ce006384fd7b7e12959440c9f803106b7140e3ce109373dff3e11d81"
        self.messager = DingTalkMessager(dingtalk_webhook=self.webhook_url, dingtalk_secret=self.secret)
        
        logger.info("账户报告器初始化完成")
    
    def get_today_date_str(self) -> str:
        """获取今天的日期字符串 (YYYYMMDD)"""
        return date.today().strftime('%Y%m%d')
    
    def send_dingtalk_report(self, txt_content: str, date_str: str) -> bool:
        """发送 TXT 内容到钉钉"""
        if not txt_content:
            logger.error("TXT 内容为空，无法发送")
            return False
        
        try:
            # 格式化日期用于标题
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            title = f"账户报告 {formatted_date}"
            
            # 将 TXT 内容转换为 Markdown 格式（使用代码块保持格式）
            markdown_text = f"## 📊 {title}\n\n```\n{txt_content}\n```"
            
            success = self.messager.send_dingtalk_markdown(
                title=title,
                text=markdown_text
            )
            
            if success:
                logger.success("钉钉报告发送成功")
            else:
                logger.error("钉钉报告发送失败")
            
            return success
            
        except Exception as e:
            logger.error(f"发送钉钉报告失败: {e}")
            return False

if __name__ == "__main__":
    logger.warning("此模块暂停使用，CSV 更新功能已迁移到 longport_trade_cli.py")
