from loguru import logger
from datetime import datetime, date
from typing import Optional, List, Any, Dict
from decimal import Decimal
import requests
import json
import time
import hmac
import hashlib
import base64
import urllib.parse


class Messager:
    def __init__(self, dingtalk_webhook: Optional[str] = None, dingtalk_secret: Optional[str] = None):
        """
        初始化Messager类
        
        Args:
            dingtalk_webhook: 钉钉机器人webhook地址
            dingtalk_secret: 钉钉机器人加签密钥（可选）
        """
        self.dingtalk_webhook = dingtalk_webhook
        self.dingtalk_secret = dingtalk_secret
        
        if self.dingtalk_webhook:
            logger.info("钉钉机器人已配置")
        else:
            logger.info("钉钉机器人未配置")
    
    def _generate_sign(self, timestamp: int) -> str:
        """
        生成钉钉机器人加签
        
        Args:
            timestamp: 时间戳（毫秒）
            
        Returns:
            str: 加签字符串
        """
        if not self.dingtalk_secret:
            return ""
            
        string_to_sign = f'{timestamp}\n{self.dingtalk_secret}'
        hmac_code = hmac.new(
            self.dingtalk_secret.encode('utf-8'), 
            string_to_sign.encode('utf-8'), 
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign
    
    def send_dingtalk_text(self, content: str, at_user_ids: Optional[List[str]] = None, is_at_all: bool = False) -> bool:
        """
        发送钉钉文本消息
        
        Args:
            content: 消息内容
            at_user_ids: @的用户userId列表  
            is_at_all: 是否@所有人
            
        Returns:
            bool: 发送是否成功
        """
        if not self.dingtalk_webhook:
            logger.error("钉钉机器人webhook未配置")
            return False
            
        try:
            # 构造消息体
            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                },
                "at": {
                    "atUserIds": at_user_ids or [],
                    "isAtAll": is_at_all
                }
            }
            
            # 准备请求参数
            timestamp = int(time.time() * 1000)
            webhook_url = self.dingtalk_webhook
            
            # 如果有加签密钥，添加签名参数
            if self.dingtalk_secret:
                sign = self._generate_sign(timestamp)
                webhook_url += f"&timestamp={timestamp}&sign={sign}"
            
            # 发送请求
            headers = {'Content-Type': 'application/json'}
            response = requests.post(webhook_url, data=json.dumps(data), headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.success(f"钉钉文本消息发送成功: {content[:50]}...")
                    return True
                else:
                    logger.error(f"钉钉消息发送失败: {result.get('errmsg', '未知错误')}")
                    return False
            else:
                logger.error(f"钉钉消息发送失败，HTTP状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"发送钉钉文本消息异常: {e}")
            return False
    
    def send_dingtalk_markdown(self, title: str, text: str, at_user_ids: Optional[List[str]] = None, is_at_all: bool = False) -> bool:
        """
        发送钉钉Markdown消息
        
        Args:
            title: 消息标题
            text: Markdown格式的消息内容
            at_user_ids: @的用户userId列表
            is_at_all: 是否@所有人
            
        Returns:
            bool: 发送是否成功
        """
        if not self.dingtalk_webhook:
            logger.error("钉钉机器人webhook未配置")
            return False
            
        try:
            # 构造消息体
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": text
                },
                "at": {
                    "atUserIds": at_user_ids or [],
                    "isAtAll": is_at_all
                }
            }
            
            # 准备请求参数
            timestamp = int(time.time() * 1000)
            webhook_url = self.dingtalk_webhook
            
            # 如果有加签密钥，添加签名参数
            if self.dingtalk_secret:
                sign = self._generate_sign(timestamp)
                webhook_url += f"&timestamp={timestamp}&sign={sign}"
            
            # 发送请求
            headers = {'Content-Type': 'application/json'}
            response = requests.post(webhook_url, data=json.dumps(data), headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.success(f"钉钉Markdown消息发送成功: {title}")
                    return True
                else:
                    logger.error(f"钉钉消息发送失败: {result.get('errmsg', '未知错误')}")
                    return False
            else:
                logger.error(f"钉钉消息发送失败，HTTP状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"发送钉钉Markdown消息异常: {e}")
            return False
    
    def send_trading_notification(self, symbol: str, action: str, price: float, quantity: int, 
                                 reason: str = "", at_user_ids: Optional[List[str]] = None) -> bool:
        """
        发送交易通知消息
        
        Args:
            symbol: 股票代码
            action: 交易动作（买入/卖出）
            price: 价格
            quantity: 数量
            reason: 交易原因
            at_user_ids: @的用户userId列表
            
        Returns:
            bool: 发送是否成功
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构造Markdown格式的交易通知
        markdown_text = f"""
## 交易通知
**股票代码**: {symbol}  
**交易动作**: {action}  
**价格**: {price}  
**数量**: {quantity}  
**时间**: {current_time}  
        """
        
        if reason:
            markdown_text += f"**交易原因**: {reason}"
        
        return self.send_dingtalk_markdown(
            title="交易通知",
            text=markdown_text,
            at_user_ids=at_user_ids
        )
    
    def send_market_close_summary(self, summary_data: Dict[str, Any], at_user_ids: Optional[List[str]] = None) -> bool:
        """
        发送市场收市总结消息
        
        Args:
            summary_data: 市场总结数据字典
            at_user_ids: @的用户userId列表
            
        Returns:
            bool: 发送是否成功
        """
        current_date = date.today().strftime("%Y-%m-%d")
        
        # 构造Markdown格式的市场收市总结
        markdown_text = f"""
## 市场收市总结
        """
        
        # 添加具体的行情数据
        for key, value in summary_data.items():
            markdown_text += f"\n**{key}**: {value}\n"
        # 添加统计日期
        markdown_text += f"\n**统计日期**: {current_date}"
        
        return self.send_dingtalk_markdown(
            title="市场收市总结",
            text=markdown_text,
            at_user_ids=at_user_ids
        )