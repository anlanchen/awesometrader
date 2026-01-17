#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汇率查询工具

提供汇率获取、币种转换等功能，支持 USD, HKD, CNH 三种币种。
基准货币固定为 CNH（人民币）。
使用 akshare 从中国外汇交易中心获取人民币外汇即期报价数据。
数据来源: http://www.chinamoney.com.cn/chinese/mkdatapfx/
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, Optional
from loguru import logger

import akshare as ak
import pandas as pd

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ExchangeRateService:
    """汇率服务类，基准货币固定为 CNH（人民币）"""

    # 币种与市场的映射关系
    MARKET_CURRENCY_MAP = {
        'US': 'USD',
        'HK': 'HKD',
        'CN': 'CNH',
    }

    # 默认汇率（当 API 调用失败时使用）
    DEFAULT_RATES = {
        'USD': 7.00,  # 1 USD = 7.00 CNH
        'HKD': 0.90,  # 1 HKD = 0.90 CNH
        'CNH': 1.0,
    }

    def __init__(self):
        """初始化汇率服务"""
        # 汇率缓存: {'USD': 7.10, 'HKD': 0.91, 'CNH': 1.0}
        self._rates: Optional[Dict[str, float]] = None
        # 缓存时间戳
        self._cache_time: Optional[datetime] = None
        # 缓存有效期（1天）
        self._cache_ttl = timedelta(days=1)

        logger.info("汇率服务初始化完成")

    def _fetch_fx_spot_rates(self) -> Optional[Dict[str, float]]:
        """
        从中国外汇交易中心获取人民币外汇即期报价

        数据来源: http://www.chinamoney.com.cn/chinese/mkdatapfx/

        Returns:
            Dict[str, float]: 汇率字典，key 为币种代码，value 为 1 单位该币种 = 多少人民币
            例如：{'USD': 7.00, 'HKD': 0.90, 'CNH': 1.0}
            如果 USD 汇率获取失败，返回 None 以触发备用数据源
        """
        try:
            logger.info("正在从中国外汇交易中心获取人民币外汇即期报价...")

            df = ak.fx_spot_quote()

            if df.empty:
                logger.warning("获取的外汇即期报价数据为空")
                return None

            # 解析货币对，提取 USD/CNY 和 HKD/CNY 的汇率
            usd_rate = None
            hkd_rate = None

            for _, row in df.iterrows():
                currency_pair = str(row['货币对']).strip()
                # 使用买报价和卖报价的中间价
                buy_price = row['买报价']
                sell_price = row['卖报价']

                # 检查是否为有效数值（排除 NaN）
                if pd.isna(buy_price) or pd.isna(sell_price):
                    continue

                mid_price = (float(buy_price) + float(sell_price)) / 2

                if currency_pair == 'USD/CNY':
                    usd_rate = mid_price
                elif currency_pair == 'HKD/CNY':
                    hkd_rate = mid_price

                if usd_rate is not None and hkd_rate is not None:
                    break

            # USD 和 HKD 都是核心货币，任一缺失则返回 None 以触发备用数据源
            if usd_rate is None or hkd_rate is None:
                missing = []
                if usd_rate is None:
                    missing.append("USD/CNY")
                if hkd_rate is None:
                    missing.append("HKD/CNY")
                logger.warning(f"未能从外汇即期报价获取 {', '.join(missing)} 汇率，尝试备用数据源")
                return None

            rates = {
                'USD': usd_rate,
                'HKD': hkd_rate,
                'CNH': 1.0,
            }

            logger.success(f"成功获取汇率: 1 USD = {usd_rate:.4f} CNH, 1 HKD = {hkd_rate:.4f} CNH")
            return rates

        except Exception as e:
            logger.warning(f"获取外汇即期报价失败: {e}")
            return None

    def _fetch_boc_safe_rates(self) -> Optional[Dict[str, float]]:
        """
        从外汇管理局获取人民币汇率中间价（备用数据源）

        数据来源: https://www.safe.gov.cn/safe/rmbhlzjj/index.html

        Returns:
            Dict[str, float]: 汇率字典，key 为币种代码，value 为 1 单位该币种 = 多少人民币
            例如：{'USD': 7.00, 'HKD': 0.90, 'CNH': 1.0}
        """
        try:
            logger.info("正在从外汇管理局获取人民币汇率中间价...")

            df = ak.currency_boc_safe()

            if df.empty:
                logger.warning("获取的人民币汇率中间价数据为空")
                return None

            # 获取最新一条数据（按日期排序后取最后一条）
            df = df.sort_values('日期', ascending=True)
            latest_row = df.iloc[-1]

            logger.info(f"获取到最新汇率日期: {latest_row['日期']}")

            # 解析 USD 和 HKD 汇率
            # 注意：美元和港元采用直接标价法，即 100 外币 = 多少人民币
            usd_rate = None
            hkd_rate = None

            if '美元' in df.columns and pd.notna(latest_row['美元']):
                # 100 USD = latest_row['美元'] CNH，所以 1 USD = latest_row['美元'] / 100
                usd_rate = float(latest_row['美元']) / 100
            if '港元' in df.columns and pd.notna(latest_row['港元']):
                # 100 HKD = latest_row['港元'] CNH，所以 1 HKD = latest_row['港元'] / 100
                hkd_rate = float(latest_row['港元']) / 100

            # 使用默认值填充缺失的汇率
            if usd_rate is None:
                logger.warning(f"未找到美元汇率中间价，使用默认值 {self.DEFAULT_RATES['USD']}")
                usd_rate = self.DEFAULT_RATES['USD']
            if hkd_rate is None:
                logger.warning(f"未找到港元汇率中间价，使用默认值 {self.DEFAULT_RATES['HKD']}")
                hkd_rate = self.DEFAULT_RATES['HKD']

            rates = {
                'USD': usd_rate,
                'HKD': hkd_rate,
                'CNH': 1.0,
            }

            logger.success(f"成功从外汇管理局获取汇率: 1 USD = {usd_rate:.4f} CNH, 1 HKD = {hkd_rate:.4f} CNH")
            return rates

        except Exception as e:
            logger.warning(f"获取人民币汇率中间价失败: {e}")
            return None

    def get_exchange_rates(self) -> Dict[str, float]:
        """
        获取汇率数据（以 CNH 为基准）

        Returns:
            Dict[str, float]: 汇率字典，表示 1 单位该币种 = 多少 CNH
        """
        # 检查缓存是否有效
        if self._rates and self._cache_time:
            if datetime.now() - self._cache_time < self._cache_ttl:
                return self._rates
            else:
                logger.info("缓存已过期，重新获取汇率数据")

        logger.info("正在获取汇率数据...")

        # 首先尝试从中国外汇交易中心获取即期报价
        rates = self._fetch_fx_spot_rates()

        if rates:
            self._rates = rates
            self._cache_time = datetime.now()
            logger.success(f"成功获取汇率数据: {rates}")
            return rates

        # 如果失败，尝试从外汇管理局获取汇率中间价作为备用
        logger.info("尝试使用备用数据源（外汇管理局）...")
        rates = self._fetch_boc_safe_rates()

        if rates:
            self._rates = rates
            self._cache_time = datetime.now()
            logger.success(f"成功从备用数据源获取汇率数据: {rates}")
            return rates

        # 如果都失败，使用默认汇率
        logger.warning("所有数据源获取汇率失败，使用默认汇率")
        return self.DEFAULT_RATES.copy()

    def convert_to_cnh(self, amount: float, from_currency: str) -> float:
        """
        将指定币种金额转换为人民币

        Args:
            amount: 金额
            from_currency: 源币种 (USD, HKD, CNH)

        Returns:
            float: 转换后的人民币金额
        """
        if from_currency == 'CNH':
            return amount

        rates = self.get_exchange_rates()
        rate = rates.get(from_currency, 1.0)
        return amount * rate

    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        币种转换

        Args:
            amount: 金额
            from_currency: 源币种 (USD, HKD, CNH)
            to_currency: 目标币种 (USD, HKD, CNH)

        Returns:
            float: 转换后的金额
        """
        if from_currency == to_currency:
            return amount

        rates = self.get_exchange_rates()

        # 先转换为 CNH，再转换为目标币种
        cnh_amount = amount * rates.get(from_currency, 1.0)
        target_rate = rates.get(to_currency, 1.0)

        return cnh_amount / target_rate

    def clear_cache(self) -> None:
        """清除汇率缓存"""
        self._rates = None
        self._cache_time = None
        logger.info("汇率缓存已清除")

    def query_exchange_rates(self) -> None:
        """查询并显示汇率信息"""
        try:
            logger.info("开始查询汇率...")

            # 清除缓存以获取最新汇率
            self.clear_cache()
            rates = self.get_exchange_rates()

            if not rates:
                logger.warning("未能获取汇率信息")
                return

            # 根据是否使用了默认值判断数据来源
            is_default = (rates == self.DEFAULT_RATES)
            if is_default:
                source = "默认值"
            else:
                source = "外汇管理局/中国外汇交易中心"

            # 格式化输出
            print("=" * 50)
            print("人民币汇率查询")
            print("=" * 50)
            print(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"数据来源: {source}")
            print("-" * 50)
            print(f"  1 USD = {rates['USD']:.4f} CNH")
            print(f"  1 HKD = {rates['HKD']:.4f} CNH")
            print("=" * 50)

        except Exception as e:
            logger.error(f"查询汇率失败: {e}")


def main():
    """主函数"""
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO"
    )

    # 创建解析器
    parser = argparse.ArgumentParser(
        description="汇率查询工具 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询汇率（以人民币为基准）
  python exchange_rate.py rates
"""
    )

    # 创建子命令解析器
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 子命令: rates
    subparsers.add_parser("rates", help="查询当前汇率")

    # 解析参数
    args = parser.parse_args()

    # 如果没有提供命令，显示帮助信息
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 执行命令
    try:
        service = ExchangeRateService()

        if args.command == "rates":
            service.query_exchange_rates()

    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
