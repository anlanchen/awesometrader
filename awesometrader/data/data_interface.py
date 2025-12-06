import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
from loguru import logger
from datetime import datetime
from longport.openapi import Period
from ..utils import Utils

class DataInterface:
    def __init__(self):
        """初始化DataInterface类"""
        # 使用工具类获取缓存目录
        self.cache_dir = Utils.get_cache_dir()
        logger.info(f"DataInterface初始化完成，缓存目录: {self.cache_dir}")
        logger.info(f"项目根目录: {Utils.get_project_root()}")
        
    # ==================== 基础工具函数 ====================
    
    def get_stock_data_path(self, stock_code: str, period: Period, file_format: str = 'csv') -> Path:
        """
        获取股票数据文件路径
        :param stock_code: 股票代码 如 '00700.HK'
        :param period: K线周期，使用Period枚举，例如：Period.Day, Period.Min_5等
        :param file_format: 文件格式 ('csv' 或 'parquet')
        :return: 文件路径
        """
        stock_dir = self.cache_dir / stock_code
        stock_dir.mkdir(exist_ok=True)
        
        # 统一使用周期名称作为文件名
        # Period不是标准枚举，通过repr获取名称然后提取周期部分
        period_repr = repr(period)  # 例如: "Period.Day" 或 "Period.Min_1"
        if '.' in period_repr:
            period_name = period_repr.split('.', 1)[1].lower()  # "Period.Day" -> "day"
        else:
            period_name = period_repr.lower()  # 备用方案
        
        # 根据文件格式设置扩展名
        if file_format.lower() == 'parquet':
            filename = f"{period_name}.parquet"
        else:  # 默认为 csv
            filename = f"{period_name}.csv"
            
        return stock_dir / filename

    def get_df_from_file(self, input_path: Path) -> pd.DataFrame:
        """
        从文件中读取DataFrame
        :param input_path: 输入文件路径
        :return: DataFrame
        """
        try:
            if input_path.suffix == '.csv':
                df = pd.read_csv(input_path, index_col=0, parse_dates=True)
            elif input_path.suffix == '.parquet':
                df = pd.read_parquet(input_path)
                df.index = pd.to_datetime(df.index)
            else:
                raise ValueError(f"不支持的文件格式: {input_path.suffix}")
            
            logger.success(f"成功读取文件: {input_path}, 数据行数: {len(df)}")
            return df
        except Exception as e:
            logger.error(f"读取文件失败 {input_path}: {e}")
            return pd.DataFrame()

    def save_df_to_file(self, df: pd.DataFrame, file_path: str, file_format: str = 'csv') -> bool:
        """
        保存DataFrame到文件
        :param df: 要保存的DataFrame  
        :param file_path: 保存文件路径
        :param file_format: 文件格式 ('csv' 或 'parquet')
        :return: 是否保存成功
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if file_format == 'csv':
                if not file_path.suffix:
                    file_path = file_path.with_suffix('.csv')
                df.to_csv(file_path)
            elif file_format == 'parquet':
                if not file_path.suffix:
                    file_path = file_path.with_suffix('.parquet')
                df.to_parquet(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_format}")
                
            logger.success(f"文件保存成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return False
    
    # ==================== 股票池相关 ====================
    
    def load_stock_pool(self, stock_list_file: str) -> List[str]:
        """
        从文件中加载股票池
        :param stock_list_file: 股票列表文件路径
        :return: 股票代码列表
        """
        try:
            stock_pool_path = self.cache_dir / stock_list_file
            if stock_pool_path.exists():
                df = pd.read_csv(stock_pool_path)
                # 按优先级顺序查找股票代码列
                if 'stock_code' in df.columns:
                    stock_codes = df['stock_code'].tolist()
                elif 'code' in df.columns:
                    stock_codes = df['code'].tolist()
                else:
                    # 默认使用第一列
                    stock_codes = df.iloc[:, 0].tolist()
                
                # 过滤掉空值
                stock_codes = [code for code in stock_codes if pd.notna(code) and str(code).strip()]
                
                logger.info(f"成功加载{len(stock_codes)}只股票")
                return stock_codes
            else:
                logger.warning(f"股票池文件不存在: {stock_pool_path}")
                return []
        except Exception as e:
            logger.error(f"加载股票池失败: {e}")
            return []

    def load_stock_pool_with_names(self, stock_list_file: str) -> List[Dict[str, str]]:
        """
        从文件中加载股票池（包含名称信息）
        :param stock_list_file: 股票列表文件路径
        :return: 包含股票代码和名称的字典列表，格式：[{'code': 'AAPL.US', 'name': '苹果公司'}, ...]
        """
        try:
            stock_pool_path = self.cache_dir / stock_list_file
            if stock_pool_path.exists():
                df = pd.read_csv(stock_pool_path)
                stocks_info = []
                
                # 检查是否有股票名称列
                if 'stock_code' in df.columns and 'stock_name' in df.columns:
                    for _, row in df.iterrows():
                        if pd.notna(row['stock_code']) and str(row['stock_code']).strip():
                            stock_info = {
                                'code': str(row['stock_code']).strip(),
                                'name': str(row['stock_name']).strip() if pd.notna(row['stock_name']) else ''
                            }
                            stocks_info.append(stock_info)
                else:
                    # 如果没有名称列，只返回代码
                    stock_codes = self.load_stock_pool(stock_list_file)
                    for code in stock_codes:
                        stocks_info.append({'code': code, 'name': ''})
                
                logger.info(f"成功加载{len(stocks_info)}只股票的详细信息")
                return stocks_info
            else:
                logger.warning(f"股票池文件不存在: {stock_pool_path}")
                return []
        except Exception as e:
            logger.error(f"加载股票池详细信息失败: {e}")
            return []
    
    # ==================== 股票数据操作 ====================
    
    def get_stock_data(self, stock_code: str, period: Period = Period.Day, 
                      start_date: datetime = None, end_date: datetime = None,
                      file_format: str = 'csv') -> pd.DataFrame:
        """
        获取股票数据
        :param stock_code: 股票代码
        :param period: K线周期，使用Period枚举，例如：Period.Day, Period.Min_5等
        :param start_date: 开始日期，可选，用于过滤数据
        :param end_date: 结束日期，可选，用于过滤数据
        :param file_format: 文件格式 ('csv' 或 'parquet')
        :return: 股票数据DataFrame
        """
        try:
            # 优先尝试指定格式的文件
            file_path = self.get_stock_data_path(stock_code=stock_code, period=period, file_format=file_format)
            if not file_path.exists():
                # 如果指定格式文件不存在，尝试另一种格式
                alt_format = 'parquet' if file_format == 'csv' else 'csv'
                alt_file_path = self.get_stock_data_path(stock_code=stock_code, period=period, file_format=alt_format)
                if alt_file_path.exists():
                    file_path = alt_file_path
                    logger.info(f"指定格式文件不存在，使用 {alt_format} 格式文件: {file_path}")
            
            if file_path.exists():
                df = self.get_df_from_file(input_path=file_path)
                
                # 如果指定了日期范围，进行过滤
                if not df.empty and (start_date is not None or end_date is not None):
                    if start_date is not None:
                        df = df[df.index >= start_date]
                    if end_date is not None:
                        df = df[df.index <= end_date]
                    
                    logger.info(f"已根据日期范围过滤数据: {len(df)} 条记录")
                
                return df
            else:
                logger.warning(f"数据文件不存在: {file_path}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"获取股票数据失败: {e}")
            return pd.DataFrame()
    
    def save_stock_data(self, stock_code: str, df: pd.DataFrame, 
                       period: Period = Period.Day, file_format: str = 'csv', 
                       force_update: bool = False) -> bool:
        """
        保存股票数据
        :param stock_code: 股票代码
        :param df: 股票数据DataFrame
        :param period: K线周期，使用Period枚举，例如：Period.Day, Period.Min_5等
        :param file_format: 文件格式
        :param force_update: 是否强制更新，True时直接覆盖原文件，False时与已有数据合并
        :return: 是否保存成功
        """
        try:
            if df.empty:
                logger.warning("要保存的数据为空")
                return False
            
            file_path = self.get_stock_data_path(stock_code=stock_code, period=period, file_format=file_format)
            
            # 如果强制更新，直接保存
            if force_update:
                logger.info(f"强制更新模式，直接保存数据到: {file_path}")
                return self.save_df_to_file(df=df, file_path=str(file_path), file_format=file_format)
            
            # 非强制更新模式，需要合并数据
            final_df = df.copy()
            
            # 检查文件是否已存在（同时检查两种格式）
            existing_df = pd.DataFrame()
            if file_path.exists():
                logger.info(f"检测到已有数据文件，准备合并数据: {file_path}")
                existing_df = self.get_df_from_file(input_path=file_path)
            else:
                # 如果指定格式文件不存在，检查另一种格式的文件
                alt_format = 'parquet' if file_format == 'csv' else 'csv'
                alt_file_path = self.get_stock_data_path(stock_code=stock_code, period=period, file_format=alt_format)
                if alt_file_path.exists():
                    logger.info(f"指定格式文件不存在，检测到 {alt_format} 格式文件，准备合并数据: {alt_file_path}")
                    existing_df = self.get_df_from_file(input_path=alt_file_path)
                    # 删除旧格式文件，使用新格式保存
                    try:
                        alt_file_path.unlink()
                        logger.info(f"已删除旧格式文件: {alt_file_path}")
                    except Exception as e:
                        logger.warning(f"删除旧格式文件失败: {e}")
            
            if not existing_df.empty:
                logger.info(f"已有数据: {len(existing_df)} 条，新数据: {len(df)} 条")
                
                # 合并数据
                combined_df = pd.concat([existing_df, df], axis=0)
                
                # 去重（基于索引，保留最后一条记录）
                combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
                
                # 按时间排序
                combined_df = combined_df.sort_index()
                
                final_df = combined_df
                logger.info(f"数据合并完成，最终数据: {len(final_df)} 条")
                
                if len(final_df) > 0:
                    logger.info(f"数据时间范围: {final_df.index[0]} 到 {final_df.index[-1]}")
            else:
                logger.info(f"文件不存在，直接保存新数据到: {file_path}")
            
            # 保存最终合并后的数据
            success = self.save_df_to_file(df=final_df, file_path=str(file_path), file_format=file_format)
            
            if success:
                logger.success(f"股票数据保存成功: {stock_code}, 记录数: {len(final_df)}")
            
            return success
            
        except Exception as e:
            logger.error(f"保存股票数据失败: {e}")
            return False
    
    # ==================== 数据处理相关 ====================
    
    def validate_data(self, df: pd.DataFrame, check_nan: bool = True, 
                     date_range: Tuple[str, str] = None) -> Dict[str, bool]:
        """
        验证数据是否有效
        :param df: 要验证的DataFrame
        :param check_nan: 是否检查NaN值
        :param date_range: 日期范围检查 (start_date, end_date)
        :return: 验证结果字典
        """
        validation_result = {
            'is_empty': False,
            'has_nan': False,
            'date_range_complete': True,
            'is_valid': True
        }
        
        try:
            # 检查是否为空
            if df.empty:
                validation_result['is_empty'] = True
                validation_result['is_valid'] = False
                logger.warning("数据为空")
                return validation_result
            
            # 检查NaN值
            if check_nan and df.isnull().any().any():
                validation_result['has_nan'] = True
                validation_result['is_valid'] = False
                logger.warning("数据中存在NaN值")
            
            # 检查日期范围完整性
            if date_range:
                start_date, end_date = date_range
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                
                if not df.index.is_monotonic_increasing:
                    df = df.sort_index()
                
                # 检查日期范围
                if df.index[0] > start_date or df.index[-1] < end_date:
                    validation_result['date_range_complete'] = False
                    validation_result['is_valid'] = False
                    logger.warning(f"数据日期范围不完整: 需要{start_date}到{end_date}, 实际{df.index[0]}到{df.index[-1]}")
            
            if validation_result['is_valid']:
                logger.success("数据验证通过")
            
        except Exception as e:
            logger.error(f"数据验证失败: {e}")
            validation_result['is_valid'] = False
            
        return validation_result

    # ==================== 文件格式转换 ====================

    def convert_csv_to_parquet(self, input_file: Path) -> bool:
        """
        Convert CSV file to Parquet file
        :param input_file: File to Convert
        :return: bool
        """
        if input_file.suffix == '.csv':
            output_file = input_file.as_posix().replace('.csv', '.parquet')
            output_file = Path(output_file)
            # Temporary
            output_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f'Converting {input_file} to {output_file}')
            df = pd.read_csv(input_file, index_col=None)
            df.to_parquet(output_file, index=False)
            logger.success(f'转换完成: {output_file}')
            return True
        return False

    def convert_parquet_to_csv(self, input_file: Path) -> bool:
        """
        Convert Parquet file to CSV file
        :param input_file: File to Convert
        :return: bool
        """
        if input_file.suffix == '.parquet':
            output_file = input_file.as_posix().replace('.parquet', '.csv')
            logger.info(f'Converting {input_file} to {output_file}')
            df = pd.read_parquet(input_file)
            df.to_csv(output_file, index=False)
            logger.success(f'转换完成: {output_file}')
            return True
        return False

