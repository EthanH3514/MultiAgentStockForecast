import os
import pandas as pd
from typing import List, Dict, Any, Optional
from .data_api import get_latest_quarter_date
from datetime import datetime

def read_csv_files(directory: str) -> str:
    """
    读取指定目录下所有CSV文件并拼接内容
    
    Args:
        directory: 要读取的目录路径
        
    Returns:
        str: 拼接后的字符串，格式为"文件名: 文件内容"
    """
    result = []
    
    # 确保目录存在
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        return ""
    
    # 遍历目录下所有文件
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                try:
                    # 读取CSV文件
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    
                    # 将DataFrame转换为字符串
                    df_str = df.to_string()
                    
                    # 拼接文件名和内容
                    result.append(f"{file}:\n{df_str}\n")
                except Exception as e:
                    print(f"❌ 读取文件 {file} 时出错: {str(e)}")
    
    # 将所有内容拼接成一个字符串
    return "\n".join(result)

def read_specific_csv(file_path: str) -> str:
    """
    读取指定的CSV文件
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        str: 文件内容字符串
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        return df.to_string()
    except Exception as e:
        print(f"❌ 读取文件 {file_path} 时出错: {str(e)}")
        return ""


def read_stock_news_csv_by_date(file_path: str, target_date: str = None) -> str:
    """
    读取股票新闻数据，返回指定日期前的新闻
    
    Args:
        file_path: CSV文件路径
        target_date: 目标日期，如果为None则返回所有新闻
        
    Returns:
        str: 指定日期前的新闻数据，格式为"新闻标题: 新闻内容 (发布时间)"
    """
    try:
        # 读取CSV文件
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # 将发布时间列转换为datetime类型
        df['发布时间'] = pd.to_datetime(df['发布时间'], format='%Y-%m-%d %H:%M:%S')
        
        # 如果指定了日期，筛选日期前的新闻
        if target_date:
            try:
                # 当天开盘以前的新闻
                target_date = pd.to_datetime(target_date, format='%Y%m%d').replace(hour=9, minute=30, second=0)
                print("target_date: ", target_date)
                df = df[df['发布时间'] <= target_date]
            except Exception as e:
                print(f"❌ 日期格式错误: {str(e)}")
                return ""
        
        if df.empty:
            print(f"❌ 没有找到相关新闻")
            return ""
        return df.to_string()
    except Exception as e:
        print(f"❌ 读取新闻数据时出错: {str(e)}")
        return ""
    

def get_csv_files(directory: str) -> List[str]:
    """
    获取指定目录下所有CSV文件的路径
    
    Args:
        directory: 要搜索的目录路径
        
    Returns:
        List[str]: CSV文件路径列表
    """
    csv_files = []
    
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        return csv_files
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    
    return csv_files

def get_csv_first_or_last_row(file_path: str, position: str = 'last') -> str:
    """
    获取指定CSV文件的第一行或最后一行数据
    
    Args:
        file_path: CSV文件路径
        position: 获取位置，'first' 表示第一行，'last' 表示最后一行
        
    Returns:
        str: 指定行的数据字符串
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        if position.lower() == 'first':
            row = df.iloc[0]
        elif position.lower() == 'last':
            row = df.iloc[-1]
        else:
            raise ValueError("position 参数必须是 'first' 或 'last'")
            
        # 将行数据转换为字符串，格式为 "列名: 值"
        result = []
        for column in df.columns:
            result.append(f"{column}: {row[column]}")
            
        return "\n".join(result)
        
    except Exception as e:
        print(f"❌ 读取文件 {file_path} 时出错: {str(e)}")
        return ""


def get_stock_fundamentals_main_business(file_path: str, target_date: str = None) -> str:
    """
    获取指定股票的主营构成
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        if target_date:
            target_date = datetime.strptime(target_date, '%Y%m%d')
            latest_date = get_latest_quarter_date(target_date, target_date.year)
            df = df[df['报告日期'] == latest_date]
        return df.to_string()
    except Exception as e:
        print(f"❌ 读取文件 {file_path} 时出错: {str(e)}")
        return ""


def get_stock_fundamentals_key_metrics(file_path: str, target_date: str = None) -> str:
    """
    获取指定股票的基本面关键指标
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df['报告期'] = pd.to_datetime(df['报告期'], format='%Y-%m-%d')
        if target_date:
            target_date = datetime.strptime(target_date, '%Y%m%d')
            df = df[df['报告期'] <= target_date]
        # 返回最后一行
        return df.iloc[-1].to_string()
    except Exception as e:
        print(f"❌ 读取文件 {file_path} 时出错: {str(e)}")
        return ""


def get_latest_data_from_directory(directory: str) -> str:
    """
    读取指定目录下所有CSV文件的最新数据并拼接
    
    Args:
        directory: 要读取的目录路径
        
    Returns:
        str: 所有文件最新数据的拼接字符串
    """
    result = []
    
    # 确保目录存在
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        return ""
    
    # 遍历目录下所有文件
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                try:
                    # 读取CSV文件
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    
                    # 获取文件名（不含扩展名）作为标题
                    file_title = os.path.splitext(file)[0]
                    
                    # 检查是否有日期列
                    date_columns = [col for col in df.columns if '日期' in col or '时间' in col or '月份' in col or '季度' in col or '年份' in col]
                    
                    if date_columns:
                        # 如果有日期列，使用日期列判断最新数据
                        date_col = date_columns[0]
                        latest_row = df.iloc[-1]  # 默认使用最后一行
                        
                        # 如果日期列是字符串，尝试转换为日期
                        if df[date_col].dtype == 'object':
                            try:
                                # 创建临时日期列
                                df['temp_date'] = pd.NaT
                                
                                # 处理不同的日期格式
                                for idx, date_str in enumerate(df[date_col]):
                                    if pd.isna(date_str):
                                        continue
                                        
                                    try:
                                        # 处理年份格式（如"2024年第1-4季度"）
                                        if '年第' in date_str and '季度' in date_str:
                                            year = int(date_str.split('年第')[0])
                                            quarter = int(date_str.split('年第')[1].split('季度')[0])
                                            df.at[idx, 'temp_date'] = pd.Timestamp(year=year, month=quarter*3, day=1)
                                            
                                        # 处理年月格式（如"2024年12月份"）
                                        elif '年' in date_str and '月份' in date_str:
                                            year = int(date_str.split('年')[0])
                                            month = int(date_str.split('年')[1].split('月份')[0])
                                            df.at[idx, 'temp_date'] = pd.Timestamp(year=year, month=month, day=1)
                                            
                                        # 处理标准日期格式（如"2024-12-07"）
                                        else:
                                            df.at[idx, 'temp_date'] = pd.to_datetime(date_str)
                                    except:
                                        continue
                                
                                # 获取最新日期对应的行
                                if not df['temp_date'].isna().all():
                                    latest_date = df['temp_date'].max()
                                    latest_row = df[df['temp_date'] == latest_date].iloc[0]
                                else:
                                    # 如果日期转换全部失败，使用最后一行
                                    latest_row = df.iloc[-1]
                            except Exception as e:
                                print(f"❌ 读取文件 {file} 时出错: {str(e)}")
                                latest_row = df.iloc[-1]
                    else:
                        # 如果没有日期列，使用最后一行
                        latest_row = df.iloc[-1]
                    
                    # 将行数据转换为字符串，格式为 "列名: 值"
                    row_data = []
                    for column in df.columns:
                        if column != 'temp_date':  # 排除临时日期列
                            value = latest_row[column]
                            if pd.notna(value):  # 只添加非空值
                                # 格式化数值，如果是浮点数则保留2位小数
                                if isinstance(value, float):
                                    value = f"{value:.2f}"
                                row_data.append(f"{column}: {value}")
                    
                    # 拼接文件名和数据
                    result.append(f"{file_title}:\n" + "\n".join(row_data) + "\n")
                    
                except Exception as e:
                    print(f"❌ 读取文件 {file} 时出错: {str(e)}")
    
    # 将所有内容拼接成一个字符串
    return "\n".join(result)


def get_macro_data_by_date(file_path: str, target_date: str = None) -> str:
    """
    获取指定日期前的宏观数据
    """
    result = []

    if target_date:
        target_date = datetime.strptime(target_date, '%Y-%m-%d')
    else:
        target_date = datetime.now()

    for root, dirs, files in os.walk(file_path):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                df = pd.read_csv(file_path, encoding='utf-8-sig')


    

def get_stock_fundamentals_data(stock_code: str, target_date: str = None, data_path: str = None) -> str:
    """
    获取指定股票的基本面数据
    """
    result = []

    fundamentals_data_path = ('data' if data_path is None else data_path) + '/' + str(stock_code) + '/' + '股票基本面数据'
    for root, dirs, files in os.walk(fundamentals_data_path):
        for file in files:
            if file.endswith('.csv'):
                if file == '基本面数据关键指标.csv' or file == '主营构成.csv':
                    continue
                try:
                    file_path = os.path.join(root, file)
                    
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    df_str = df.to_string()

                    result.append(f'{file}:\n{df_str}\n')
                except Exception as e:
                    print(f"❌ 读取文件 {file} 时出错: {str(e)}")
    answer = '\n'.join(result)

    # 获取主营构成
    try:
        indicator_path = fundamentals_data_path + '/' + '主营构成.csv'
        answer += '\n' + '主营构成:\n' + get_stock_fundamentals_main_business(indicator_path, target_date)
    except Exception as e:
        print(f"❌ 读取文件 {indicator_path} 时出错: {str(e)}")

    # 获取基本面数据关键指标
    try:
        indicator_path = fundamentals_data_path + '/' + '基本面数据关键指标.csv'
        answer += '\n' + '基本面数据关键指标:\n' + get_stock_fundamentals_key_metrics(indicator_path, target_date)
    except Exception as e:
        print(f"❌ 读取文件 {indicator_path} 时出错: {str(e)}")

    print(f'✅ 基本面数据获取完成 {stock_code}')
    return answer


def calculate_technical_indicators(df):
    """计算技术指标"""
    # 计算5日、10日、20日移动平均线
    df['MA5'] = df['收盘'].rolling(window=5).mean()
    df['MA10'] = df['收盘'].rolling(window=10).mean()
    df['MA20'] = df['收盘'].rolling(window=20).mean()
    
    # 计算RSI
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算MACD
    exp1 = df['收盘'].ewm(span=12, adjust=False).mean()
    exp2 = df['收盘'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 计算布林带
    df['BB_middle'] = df['收盘'].rolling(window=20).mean()
    df['BB_upper'] = df['BB_middle'] + 2 * df['收盘'].rolling(window=20).std()
    df['BB_lower'] = df['BB_middle'] - 2 * df['收盘'].rolling(window=20).std()
    
    # 计算价格变化率
    df['Price_Change'] = df['收盘'].pct_change()
    
    # 计算成交量变化率
    df['Volume_Change'] = df['成交量'].pct_change()
    
    # 计算波动率
    df['Volatility'] = df['收盘'].rolling(window=20).std()
    
    # 计算价格动量
    df['Momentum'] = df['收盘'].pct_change(periods=10)
    
    # 计算VWAP（成交量加权平均价格）
    df['VWAP'] = (df['收盘'] * df['成交量']).cumsum() / df['成交量'].cumsum()
    
    # 计算市场情绪指标
    df['Price_MA_Ratio'] = df['收盘'] / df['MA20']  # 价格与20日均线比率
    df['Volume_MA_Ratio'] = df['成交量'] / df['成交量'].rolling(window=20).mean()  # 成交量比率
    
    return df


def get_stock_price_data(stock_code: str, target_date: str = None, data_path: str = None) -> str:
    """
    获取指定股票的价格数据和技术指标
    
    Args:
        stock_code: 股票代码，如 '600415'
        target_date: 目标日期, 格式%Y%m%d, 如果为None则使用最新数据
        data_path: 数据路径，如果为None则使用默认路径

    Returns:
        str: 指定日期前的20行价格数据和技术指标的格式化字符串
    """
    try:
        price_data_path = os.path.join('data' if data_path is None else data_path, stock_code, '股票日线数据.csv')
        
        # 检查文件是否存在
        if not os.path.exists(price_data_path):
            print(f"❌ 文件不存在: {price_data_path}")
            return ""
            
        # 读取CSV文件
        df = pd.read_csv(price_data_path, encoding='utf-8-sig')
        
        # 将日期列转换为datetime类型
        df['日期'] = pd.to_datetime(df['日期'])
        
        # 如果指定了日期，筛选日期前的数据
        if target_date:
            try:
                target_date = pd.to_datetime(target_date, format='%Y%m%d')
                df = df[df['日期'] < target_date]
            except Exception as e:
                print(f"❌ 日期格式错误: {str(e)}")

        # 计算技术指标
        df = calculate_technical_indicators(df)
         
        # 获取数据行数
        total_rows = len(df)
        rows_to_get = min(20, total_rows)  # 如果数据少于20行，则获取所有数据
        
        # 获取最后N行数据
        last_rows = df.tail(rows_to_get)
        
        # 格式化输出
        result = []
        target_date = (str(target_date.strftime('%Y-%m-%d')) + '前') if target_date else "最新"
        result.append(f"=== {stock_code} {target_date} 的{rows_to_get}个交易日数据 ===")
        
        # 遍历每一行数据
        for _, row in last_rows.iterrows():
            row_data = []
            for column in df.columns:
                value = row[column]
                if pd.notna(value):  # 只添加非空值
                    if isinstance(value, float):
                        value = f"{value:.2f}"
                    elif isinstance(value, pd.Timestamp):
                        value = value.strftime('%Y-%m-%d')
                    row_data.append(f"{column}: {value}")
            result.append("\n".join(row_data))
            result.append("")  # 添加空行分隔不同交易日
        
        return "\n".join(result)
        
    except Exception as e:
        print(f"❌ 读取股票 {stock_code} 价格数据时出错: {str(e)}")
        return ""

