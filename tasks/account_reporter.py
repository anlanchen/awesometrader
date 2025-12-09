#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import json
import csv
from datetime import date
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from awesometrader.notify import DingTalkMessager
from awesometrader.utils import Utils


class AccountReporter:
    """账户信息报告器"""
    
    # CSV 字段定义
    CSV_FIELDS = [
        'date', 'total_assets', 'total_market_value', 'total_cash_balance',
        'total_adjustment', 'leverage_ratio', 'total_pnl', 'total_pnl_pct'
    ]
    
    def __init__(self):
        """初始化账户报告器"""
        # 缓存目录
        cache_dir = Utils.get_cache_dir()
        
        # 账户数据目录
        self.account_dir = cache_dir / 'account'
        
        # CSV 文件路径
        self.csv_path = cache_dir / 'account.csv'
        
        # 钉钉配置
        self.webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=31017c949ed2c36aa3cdad026f5ff29ea44b38633b26ce90e0197d092191b963"
        self.secret = "SECab458845ce006384fd7b7e12959440c9f803106b7140e3ce109373dff3e11d81"
        self.messager = DingTalkMessager(dingtalk_webhook=self.webhook_url, dingtalk_secret=self.secret)
        
        logger.info("账户报告器初始化完成")
    
    def get_today_date_str(self) -> str:
        """获取今天的日期字符串 (YYYYMMDD)"""
        return date.today().strftime('%Y%m%d')
    
    def get_json_path(self, date_str: str) -> Path:
        """获取指定日期的 JSON 文件路径"""
        return self.account_dir / f'account_metrics_{date_str}.json'
    
    def get_txt_path(self, date_str: str) -> Path:
        """获取指定日期的 TXT 文件路径"""
        return self.account_dir / f'account_metrics_{date_str}.txt'
    
    def load_json_data(self, date_str: str) -> dict:
        """加载指定日期的 JSON 数据"""
        json_path = self.get_json_path(date_str)
        
        if not json_path.exists():
            logger.error(f"JSON 文件不存在: {json_path}")
            return {}
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功加载 JSON 数据: {json_path}")
            return data
        except Exception as e:
            logger.error(f"加载 JSON 数据失败: {e}")
            return {}
    
    def load_txt_content(self, date_str: str) -> str:
        """加载指定日期的 TXT 内容"""
        txt_path = self.get_txt_path(date_str)
        
        if not txt_path.exists():
            logger.error(f"TXT 文件不存在: {txt_path}")
            return ""
        
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"成功加载 TXT 内容: {txt_path}")
            return content
        except Exception as e:
            logger.error(f"加载 TXT 内容失败: {e}")
            return ""
    
    def extract_csv_row(self, data: dict, date_str: str) -> dict:
        """从 JSON 数据中提取 CSV 行数据"""
        # 格式化日期为 YYYY-MM-DD
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        
        # 格式化数值：保留2位小数，百分比字段转换为%显示
        return {
            'date': formatted_date,
            'total_assets': f"{data.get('total_assets', 0):.2f}",
            'total_market_value': f"{data.get('total_market_value', 0):.2f}",
            'total_cash_balance': f"{data.get('total_cash_balance', 0):.2f}",
            'total_adjustment': f"{data.get('total_adjustment', 0):.2f}",
            'leverage_ratio': f"{data.get('leverage_ratio', 0) * 100:.2f}%",
            'total_pnl': f"{data.get('total_pnl', 0):.2f}",
            'total_pnl_pct': f"{data.get('total_pnl_pct', 0) * 100:.2f}%",
        }
    
    def update_csv(self, row_data: dict) -> bool:
        """更新 CSV 文件，如果日期已存在则更新，否则追加"""
        try:
            # 确保目录存在
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取现有数据
            existing_rows = []
            if self.csv_path.exists():
                with open(self.csv_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    existing_rows = list(reader)
            
            # 查找是否已存在该日期的记录
            date_found = False
            for i, row in enumerate(existing_rows):
                if row['date'] == row_data['date']:
                    existing_rows[i] = row_data
                    date_found = True
                    logger.info(f"更新已存在的日期记录: {row_data['date']}")
                    break
            
            if not date_found:
                existing_rows.append(row_data)
                logger.info(f"添加新的日期记录: {row_data['date']}")
            
            # 按日期排序
            existing_rows.sort(key=lambda x: x['date'])
            
            # 写入 CSV 文件
            with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_FIELDS)
                writer.writeheader()
                writer.writerows(existing_rows)
            
            logger.success(f"CSV 文件更新成功: {self.csv_path}")
            return True
            
        except Exception as e:
            logger.error(f"更新 CSV 文件失败: {e}")
            return False
    
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
    
    def report(self, date_str: str = None) -> bool:
        """
        执行报告任务
        1. 读取指定日期的 JSON 数据，更新到 CSV 文件
        2. 发送指定日期的 TXT 内容到钉钉
        """
        if date_str is None:
            date_str = self.get_today_date_str()
        
        logger.info(f"开始执行报告任务，日期: {date_str}")
        
        # 1. 加载 JSON 数据并更新 CSV
        json_data = self.load_json_data(date_str)
        if not json_data:
            logger.error("无法加载 JSON 数据，任务终止")
            return False
        
        row_data = self.extract_csv_row(json_data, date_str)
        csv_success = self.update_csv(row_data)
        
        # 2. 加载 TXT 内容并发送到钉钉
        txt_content = self.load_txt_content(date_str)
        if not txt_content:
            logger.error("无法加载 TXT 内容，跳过钉钉发送")
            return csv_success
        
        dingtalk_success = self.send_dingtalk_report(txt_content, date_str)
        
        return csv_success and dingtalk_success


def main():
    # 配置日志
    logger.remove()
    logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
    logger.add("logs/account_reporter_{time:YYYY-MM-DD}.log", rotation="1 day", retention="30 days")

    parser = argparse.ArgumentParser(description="AwesomeTrader 账户报告 CLI")
    
    # Command: report
    parser.add_argument("--date", type=str, default=None,
                        help="指定日期 (格式: YYYYMMDD)，默认为今天")

    args = parser.parse_args()

    reporter = AccountReporter()

    try:
        success = reporter.report(date_str=args.date)
        if success:
            logger.success("报告任务执行完成")
        else:
            logger.error("报告任务执行失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
