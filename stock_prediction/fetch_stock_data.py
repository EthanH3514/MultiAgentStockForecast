import akshare as ak
import pandas as pd
from datetime import datetime
import os
from stock_prediction.util.data_api import fetch_stock_daily_data, fetch_stock_news_data, fetch_macro_data, create_path, fetch_stock_fundamentals_data


def fetch_stock_data(stock_code: int, start_date: str, end_date: str, ws_server: None) -> None:
    """
    拉取股票相关数据
    :param stock_code: 股票代码
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param ws_server: WebSocket服务器实例
    :return: None
    """
    # 创建数据目录
    if ws_server:
        ws_server.emit_analysis_progress('data_preparation', "正在创建数据目录...")
    root_dir = os.path.dirname(os.path.abspath(__file__))

    create_path(os.path.join(root_dir, 'data', str(stock_code)))
    
    # 获取股票日线数据
    if ws_server:
        ws_server.emit_analysis_progress('data_preparation', "正在拉取股票日线数据...")
    fetch_stock_daily_data(stock_code=stock_code, start_date=start_date, end_date=end_date)
    
    # 获取新闻数据
    if ws_server:
        ws_server.emit_analysis_progress('data_preparation', "正在拉取股票新闻数据...")
    fetch_stock_news_data(stock_code=stock_code)

    # 获取公司基本面数据
    if ws_server:
        ws_server.emit_analysis_progress('data_preparation', "正在拉取公司基本面数据...")
    fetch_stock_fundamentals_data(stock_code=stock_code)

    # 获取宏观数据
    if ws_server:
        ws_server.emit_analysis_progress('data_preparation', "正在拉取宏观数据...")
    fetch_macro_data()

    if ws_server:
        ws_server.emit_analysis_progress('data_preparation', "数据拉取完成！")


if __name__ == "__main__":
    stock_code = "600415"  # 小商品城
    start_date = "20100101"
    end_date = datetime.now().strftime("%Y%m%d")
    fetch_stock_data(stock_code=stock_code, start_date=start_date, end_date=end_date)