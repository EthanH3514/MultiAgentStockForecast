import akshare as ak
import pandas as pd
from datetime import datetime
import os
import time
import random
import functools
from typing import Optional, List
import re
import shutil


root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(root_dir, 'data')

def timer(func):
    """
    计时装饰器，用于统计函数执行时间
    
    Args:
        func: 要计时的函数
    
    Returns:
        包装后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        print(f"{func.__name__} 执行耗时: {duration:.2f}秒")
        return result
    return wrapper

def sleep_random(seconds: float = 1.0, random_range: float = 0.5) -> None:
    """
    随机延时函数，用于避免请求过于频繁
    
    Args:
        seconds: 基础延时秒数
        random_range: 随机浮动范围（秒）
    """
    time.sleep(seconds + random.uniform(0, random_range))

def create_path(path_str: str) -> None:
    """
    递归创建路径，如果路径不存在则创建
    
    Args:
        path_str: 要创建的路径字符串
    """
    if not os.path.exists(path_str):
        os.makedirs(path_str)
        print(f"创建路径: {path_str}")

def check_file_exists(file_path: str, max_age_days: int = 30) -> bool:
    """
    检查文件是否存在且未过期
    
    Args:
        file_path: 文件路径
        max_age_days: 文件最大有效期（天），默认30天
    
    Returns:
        bool: 文件是否存在且未过期
    """
    if not os.path.exists(file_path):
        return False
    
    # 检查文件修改时间
    file_mtime = os.path.getmtime(file_path)
    current_time = time.time()
    age_days = (current_time - file_mtime) / (24 * 3600)
    
    if age_days > max_age_days:
        print(f"文件已过期（{age_days:.1f}天），需要更新: {file_path}")
        return False
    
    return True

@timer
def fetch_with_cache(func, file_path: str, max_age_days: int = 30, position: str = None) -> bool:
    """
    带缓存检查的数据获取函数
    
    Args:
        func: 获取数据的函数
        file_path: 文件保存路径
        max_age_days: 文件最大有效期（天），默认30天
        position: 获取位置，'first' 表示第一行，'last' 表示最后一行, None 表示全部
    """
    if check_file_exists(file_path, max_age_days):
        print(f"✅ 文件有效，跳过获取: {file_path}")
        return True
    
    if position is not None and position != 'first' and position != 'last':
        print(f"❌ 位置参数错误: {position}")
        return False
    
    print(f"🔍 获取新数据: {file_path}")
    try:
        sleep_random(1.5, 0.5)  # 添加随机延时
        df = func()
        print('df: ', df)
        if position == 'first':
            df = df.iloc[0]
        elif position == 'last':
            df = df.iloc[-1]
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"✅ 数据已保存到: {file_path}")
        return True
    except Exception as e:
        print(f"❌ 获取数据失败: {str(e)}")
        sleep_random(3.0, 1.0)  # 失败后等待更长时间
        try:
            df = func()
            if position == 'first':
                df = df.iloc[0]
            elif position == 'last':
                df = df.iloc[-1]
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"✅ 重试成功：数据已保存到: {file_path}")
            return True
        except Exception as e2:
            print(f"❌ 重试失败: {str(e2)}")
            return False


@timer
def fetch_stock_daily_data(stock_code: int, start_date: str, end_date: str) -> None:
    """
    获取股票日线数据
    """
    global path
    daily_data_path = os.path.join(path, str(stock_code), '股票日线数据.csv')

    # 获取股票日线数据
    print('🔍 正在获取股票日线数据...')
    try:
        stock_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                      start_date=start_date, end_date=end_date,
                                      adjust="qfq")
        # 删除不需要的列
        stock_df = stock_df.drop('股票代码', axis=1)
        # 保存日线数据
        stock_df.to_csv(daily_data_path, index=False, encoding='utf-8-sig')
        print(f'✅ 股票日线数据已保存到 {daily_data_path}')
    except Exception as e:
        print(f"❌ 获取股票日线数据失败: {str(e)}")

@timer
def fetch_stock_news_data(stock_code: int) -> None:
    """
    获取股票新闻数据
    """
    global path
    news_data_path = os.path.join(path, str(stock_code), '股票新闻数据.csv')

    # 获取新闻数据
    print('🔍 正在获取新闻数据...')
    try:
        news_df = ak.stock_news_em(symbol=stock_code)
        # 删除不需要的列
        news_df = news_df.drop('关键词', axis=1)
        # 按时间排序
        news_df['发布时间'] = pd.to_datetime(news_df['发布时间'], format='%Y-%m-%d %H:%M:%S')
        news_df = news_df.sort_values('发布时间', ascending=False)
        news_df.to_csv(news_data_path, index=False, encoding='utf-8-sig')
        print(f"✅ 新闻数据已保存到 {news_data_path}")
    except Exception as e:
        print(f"❌ 获取新闻数据失败: {str(e)}")

@timer
def fetch_stock_fundamentals_data(stock_code: int):
    """
    获取股票基本面数据
    """
    global path
    fundamentals_data_path = os.path.join(path, str(stock_code), '股票基本面数据')
    
    # 获取个股研报
    fetch_stock_report_data(stock_code, fundamentals_data_path)

    # 获取业绩报表
    fetch_stock_yjbb_data(stock_code, fundamentals_data_path)

    # 获取主营介绍
    fetch_stock_zyjs_data(stock_code, fundamentals_data_path)

    # 获取主营构成
    fetch_stock_zygc_data(stock_code, fundamentals_data_path)

    # 获取基本面数据关键指标
    fetch_stock_financial_abstract_data(stock_code, fundamentals_data_path)


@timer
def fetch_stock_report_data(stock_code: int, fundamentals_data_path: str) -> None:
    """
    获取个股研报
    """
    create_path(fundamentals_data_path)
    report_data_path = os.path.join(fundamentals_data_path, '个股研报.csv')
    
    # 获取个股研报
    print('🔍 正在获取个股研报...')
    fetch_with_cache(lambda: ak.stock_research_report_em(symbol=stock_code), report_data_path)


# 获取最近的季度日期
def get_latest_quarter_date(current_date: datetime, current_year: int) -> str:
    """
    获取最近的季度日期
    """
    quarter_dates = [
        f"{current_year}0331",  # 第一季度
        f"{current_year}0630",  # 第二季度
        f"{current_year}0930",  # 第三季度
        f"{current_year}1231"   # 第四季度
    ]
    latest_date = None
    for date in quarter_dates:
        date_obj = datetime.strptime(date, "%Y%m%d")
        if date_obj < current_date:
            latest_date = date
        else:
            break
    if latest_date is None:
        current_year -= 1
        return get_latest_quarter_date(current_date, current_year)
    return latest_date


# 获取最近的两个季度日期
def get_latest_two_quarter_dates(current_date: datetime, current_year: int) -> List[str]:
    """
    获取最近的两个季度日期（按时间顺序排列）
    例如：当前日期是2023-08-15，则返回 ['20230630', '20230331']
    """
    # 生成当前年和前一年的所有季度日期
    quarter_dates = []
    for year in [current_year - 1, current_year]:
        quarter_dates.extend([
            f"{year}0331",  # 第一季度
            f"{year}0630",  # 第二季度
            f"{year}0930",  # 第三季度
            f"{year}1231"   # 第四季度
        ])
    
    # 转换为datetime对象并过滤掉未来日期
    valid_dates = []
    for date_str in quarter_dates:
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        if date_obj < current_date:
            valid_dates.append(date_obj)
    
    # 按日期降序排序并取最近的两个
    valid_dates.sort(reverse=True)
    latest_two = valid_dates[:2]
    
    # 转换回字符串格式并按时间顺序排列（早的在前）
    return [d.strftime("%Y%m%d") for d in sorted(latest_two)]



@timer
def fetch_stock_yjbb_data(stock_code: int, fundamentals_data_path: str, target_date: str = None) -> None:
    """
    获取业绩报表
    
    Args:
        stock_code: 股票代码
        fundamentals_data_path: 基本面数据保存路径
    """
    create_path(fundamentals_data_path)
    yjbb_data_path = os.path.join(fundamentals_data_path, '业绩报表.csv')
    
    current_date = None
    current_year = None

    if target_date is None:
        # 获取当前日期
        current_date = datetime.now()
        current_year = current_date.year
    else:
        current_date = datetime.strptime(target_date, '%Y-%m-%d')
        current_year = current_date.year

    # 找到最近的已过期的两个季度日期
    latest_date = get_latest_two_quarter_dates(current_date, current_year)

    print(f"最近的已过期的两个季度日期: {latest_date}")

    # 获取业绩报表
    def fetch_and_filter_data(date_list: List[str]) -> pd.DataFrame:
        result_dfs = []
        for date in date_list:
            sleep_random()
            print(f'🔍 正在获取业绩报表，使用日期: {date}...')
            # 获取所有股票的业绩报表
            try:
                df = ak.stock_yjbb_em(date=date)
            except Exception as e:
                print(f"❌ 获取数据失败: {str(e)}")
                continue
            
            if df is None or df.empty:
                print(f"❌ 日期 {date} 没有业绩报表数据或接口返回异常")
                continue

            print('开始筛选')
            # 筛选指定股票的数据
            stock_data = df[df['股票代码'] == str(stock_code)]
            stock_data.insert(loc=0, column='时间', value=date)
            print('stock_data: ', stock_data)

            if stock_data.empty:
                print(f"❌ 日期 {date} 没有股票 {stock_code} 的业绩报表数据")
                continue
            
            result_dfs.append(stock_data)
        
        return pd.concat(result_dfs).drop_duplicates()
    
    fetch_with_cache(lambda: fetch_and_filter_data(latest_date), yjbb_data_path)


@timer
def fetch_stock_zyjs_data(stock_code: int, fundamentals_data_path: str) -> None:
    """
    获取主营介绍
    """
    create_path(fundamentals_data_path)
    zyjs_data_path = os.path.join(fundamentals_data_path, '主营介绍.csv')
    
    # 获取主营介绍
    print('🔍 正在获取主营介绍...')
    fetch_with_cache(lambda: ak.stock_zyjs_ths(symbol=stock_code), zyjs_data_path)


@timer
def fetch_stock_zygc_data(stock_code: int, fundamentals_data_path: str) -> None:
    """
    获取主营构成
    """
    create_path(fundamentals_data_path)
    zygc_data_path = os.path.join(fundamentals_data_path, '主营构成.csv')
    
    # 获取主营构成
    print('🔍 正在获取主营构成...')
    result = fetch_with_cache(lambda: ak.stock_zygc_em(symbol='SH' + str(stock_code)), zygc_data_path)
    
    # 如果沪市获取失败，则尝试深市
    if not result:
        fetch_with_cache(lambda: ak.stock_zygc_em(symbol='SZ' + str(stock_code)), zygc_data_path)


@timer
def fetch_stock_financial_abstract_data(stock_code: int, fundamentals_data_path: str) -> None:
    """
    获取基本面数据关键指标
    """
    create_path(fundamentals_data_path)
    financial_abstract_data_path = os.path.join(fundamentals_data_path, '基本面数据关键指标.csv')

    # 获取基本面数据关键指标
    print('🔍 正在获取基本面数据关键指标...')
    fetch_with_cache(lambda: ak.stock_financial_abstract_ths(symbol=stock_code), financial_abstract_data_path)


@timer
def fetch_macro_data():
    """
    获取宏观数据
    """
    print('🔍 正在获取宏观数据...')
    global path
    macro_data_path = os.path.join(path, '宏观数据')
    
    fetch_macro_cn(os.path.join(macro_data_path, '中国宏观数据'))
    fetch_macro_us(os.path.join(macro_data_path, '美国宏观数据'))


def fetch_macro_cn(macro_cn_data_path: str):
    """
    获取中国宏观数据
    """
    print('🔍 正在获取中国宏观数据...')
    create_path(macro_cn_data_path)

    # 获取中国宏观杠杆率数据
    fetch_macro_cnbs_data(os.path.join(macro_cn_data_path, '宏观杠杆率数据.csv'))

    # 获取国民经济运行状况数据
    fetch_macro_cn_gmjjy(os.path.join(macro_cn_data_path, '国民经济运行状况数据'))

    # 获取贸易状况数据
    fetch_macro_cn_myzk(os.path.join(macro_cn_data_path, '贸易状况数据'))

    # 获取产业指标
    fetch_macro_cn_cyzb(os.path.join(macro_cn_data_path, '产业指标'))

    # 获取金融指标
    fetch_macro_cn_jrzb(os.path.join(macro_cn_data_path, '金融指标'))


def fetch_macro_cnbs_data(macro_cnbs_data_path: str):
    """
    获取中国宏观杠杆率数据
    """
    print('🔍 正在获取中国宏观杠杆率数据...')
    fetch_with_cache(ak.macro_cnbs, macro_cnbs_data_path)


def fetch_macro_cn_gmjjy(macro_cn_gmjjy_data_path: str):
    """
    获取国民经济运行状况数据
    """
    create_path(macro_cn_gmjjy_data_path)
    print('🔍 正在获取国民经济运行状况数据...')
    # 获取企业商品价格指数数据
    fetch_macro_china_qyspjg(macro_cn_gmjjy_data_path + '/企业商品价格指数数据.csv')

    # 获取外商直接投资数据
    fetch_macro_china_fdi(macro_cn_gmjjy_data_path + '/外商直接投资数据.csv')

    # 获取LPR品种数据
    fetch_macro_china_lpr(macro_cn_gmjjy_data_path + '/LPR品种数据.csv')

    # 获取城镇调查失业率
    fetch_macro_china_urban_unemployment(macro_cn_gmjjy_data_path + '/城镇调查失业率.csv')

    # 获取社会融资规模增量统计
    fetch_macro_china_shrzgm(macro_cn_gmjjy_data_path + '/社会融资规模增量统计.csv')

    # 获取中国GDP年率
    fetch_macro_china_gdp_yearly(macro_cn_gmjjy_data_path + '/中国GDP年率.csv')

    # 获取物价水平
    fetch_macro_china_wjsp(macro_cn_gmjjy_data_path + '/物价水平')

def fetch_macro_china_qyspjg(macro_china_qyspjg_data_path: str):
    """
    获取企业商品价格指数数据
    """
    print('🔍 正在获取企业商品价格指数数据...')
    fetch_with_cache(ak.macro_china_qyspjg, macro_china_qyspjg_data_path)


def fetch_macro_china_fdi(macro_china_fdi_data_path: str):
    """
    获取外商直接投资数据
    """
    print('🔍 正在获取外商直接投资数据...')
    fetch_with_cache(ak.macro_china_fdi, macro_china_fdi_data_path)


def fetch_macro_china_lpr(macro_china_lpr_data_path: str):
    """
    获取LPR品种数据
    """
    print('🔍 正在获取LPR品种数据...')
    fetch_with_cache(ak.macro_china_lpr, macro_china_lpr_data_path)


def fetch_macro_china_urban_unemployment(macro_china_urban_unemployment_data_path: str):
    """
    获取城镇调查失业率
    """
    print('🔍 正在获取城镇调查失业率...')
    fetch_with_cache(ak.macro_china_urban_unemployment, macro_china_urban_unemployment_data_path)


def fetch_macro_china_shrzgm(macro_china_shrzgm_data_path: str):
    """
    获取社会融资规模增量统计
    """
    print('🔍 正在获取社会融资规模增量统计...')
    fetch_with_cache(ak.macro_china_shrzgm, macro_china_shrzgm_data_path)


def fetch_macro_china_gdp_yearly(macro_china_gdp_yearly_data_path: str):
    """
    获取中国GDP年率
    """
    print('🔍 正在获取中国GDP年率...')
    fetch_with_cache(ak.macro_china_gdp_yearly, macro_china_gdp_yearly_data_path)


def fetch_macro_china_wjsp(macro_china_wjsp_data_path: str):
    """
    获取物价水平
    """
    print('🔍 正在获取物价水平...')
    create_path(macro_china_wjsp_data_path)

    # 获取中国CPI年率报告
    fetch_macro_china_cpi_yearly(macro_china_wjsp_data_path + '/中国CPI年率报告.csv')

    # 获取中国CPI月率报告
    fetch_macro_china_cpi_monthly(macro_china_wjsp_data_path + '/中国CPI月率报告.csv')

    # 获取中国PPI年率报告
    fetch_macro_china_ppi_yearly(macro_china_wjsp_data_path + '/中国PPI年率报告.csv')


def fetch_macro_china_cpi_yearly(macro_china_cpi_yearly_data_path: str):
    """
    获取中国CPI年率报告
    """
    print('🔍 正在获取中国CPI年率报告...')
    fetch_with_cache(ak.macro_china_cpi_yearly, macro_china_cpi_yearly_data_path)


def fetch_macro_china_cpi_monthly(macro_china_cpi_monthly_data_path: str):
    """
    获取中国CPI月率报告
    """
    print('🔍 正在获取中国CPI月率报告...')
    fetch_with_cache(ak.macro_china_cpi_monthly, macro_china_cpi_monthly_data_path)


def fetch_macro_china_ppi_yearly(macro_china_ppi_yearly_data_path: str):
    """
    获取中国PPI年率报告
    """
    print('🔍 正在获取中国PPI年率报告...')
    fetch_with_cache(ak.macro_china_ppi_yearly, macro_china_ppi_yearly_data_path)


def fetch_macro_cn_myzk(macro_cn_myzk_data_path: str):
    """
    获取贸易状况数据
    """
    create_path(macro_cn_myzk_data_path)
    print('🔍 正在获取贸易状况数据...')

    # 获取以美元计算的出口年率
    fetch_macro_china_exports_yoy(macro_cn_myzk_data_path + '/以美元计算的出口年率.csv')

    # 获取以美元计算的进口年率
    fetch_macro_china_imports_yoy(macro_cn_myzk_data_path + '/以美元计算的进口年率.csv')

    # 获取以美元计算的贸易帐（亿美元）
    fetch_macro_china_trade_balance(macro_cn_myzk_data_path + '/以美元计算的贸易帐（亿美元）.csv')


def fetch_macro_china_exports_yoy(macro_china_exports_yoy_data_path: str):
    """
    获取以美元计算的出口年率
    """
    print('🔍 正在获取以美元计算的出口年率...')
    fetch_with_cache(ak.macro_china_exports_yoy, macro_china_exports_yoy_data_path)


def fetch_macro_china_imports_yoy(macro_china_imports_yoy_data_path: str):
    """
    获取以美元计算的进口年率
    """
    print('🔍 正在获取以美元计算的进口年率...')
    fetch_with_cache(ak.macro_china_imports_yoy, macro_china_imports_yoy_data_path)


def fetch_macro_china_trade_balance(macro_china_trade_balance_data_path: str):
    """
    获取以美元计算的贸易帐（亿美元）
    """
    print('🔍 正在获取以美元计算的贸易帐（亿美元）...')
    fetch_with_cache(ak.macro_china_trade_balance, macro_china_trade_balance_data_path)


def fetch_macro_cn_cyzb(macro_cn_cyzb_data_path: str):
    """
    获取产业指标
    """
    create_path(macro_cn_cyzb_data_path)

    # 获取工业增加值增长
    fetch_macro_china_gyzjz(macro_cn_cyzb_data_path + '/工业增加值增长.csv')

    # 获取官方制造业PMI
    fetch_macro_china_pmi_yearly(macro_cn_cyzb_data_path + '/制造业PMI.csv')

    # 获取官方非制造业PMI
    fetch_macro_china_non_man_pmi(macro_cn_cyzb_data_path + '/非制造业PMI.csv')


def fetch_macro_china_gyzjz(macro_china_gyzjz_data_path: str):
    """
    获取工业增加值增长
    """
    print('🔍 正在获取工业增加值增长...')
    fetch_with_cache(ak.macro_china_gyzjz, macro_china_gyzjz_data_path)


def fetch_macro_china_pmi_yearly(macro_china_pmi_yearly_data_path: str):
    """
    获取官方制造业PMI
    """
    print('🔍 正在获取官方制造业PMI...')
    fetch_with_cache(ak.macro_china_pmi_yearly, macro_china_pmi_yearly_data_path)


def fetch_macro_china_non_man_pmi(macro_china_non_man_pmi_data_path: str):
    """
    获取官方非制造业PMI
    """
    print('🔍 正在获取官方非制造业PMI...')
    fetch_with_cache(ak.macro_china_non_man_pmi, macro_china_non_man_pmi_data_path)


def fetch_macro_cn_jrzb(macro_cn_jrzb_data_path: str):
    """
    获取金融指标
    """
    create_path(macro_cn_jrzb_data_path)
    print('🔍 正在获取金融指标...')

    # 获取外汇储备（亿美元）
    fetch_macro_china_fx_reserves_yearly(macro_cn_jrzb_data_path + '/外汇储备（亿美元）.csv')

    # 获取M2货币供应年率
    fetch_macro_china_m2_yearly(macro_cn_jrzb_data_path + '/M2货币供应年率.csv')

    # 获取企业景气及企业家信心指数
    fetch_macro_china_enterprise_boom_index(macro_cn_jrzb_data_path + '/企业景气及企业家信心指数.csv')

    # 获取居民消费价格指数
    fetch_macro_china_cpi(macro_cn_jrzb_data_path + '/居民消费价格指数.csv')

    # 获取国内生产总值
    fetch_macro_china_gdp(macro_cn_jrzb_data_path + '/国内生产总值.csv')

    # 获取货币供应量
    fetch_macro_china_supply_of_money(macro_cn_jrzb_data_path + '/货币供应量.csv')

    # 获取人民币汇率中间价
    fetch_macro_china_rmb(macro_cn_jrzb_data_path + '/人民币汇率中间价.csv')


def fetch_macro_china_fx_reserves_yearly(macro_china_fx_reserves_yearly_data_path: str):
    """
    获取外汇储备（亿美元）
    """
    print('🔍 正在获取外汇储备（亿美元）...')
    fetch_with_cache(ak.macro_china_fx_reserves_yearly, macro_china_fx_reserves_yearly_data_path)


def fetch_macro_china_m2_yearly(macro_china_m2_yearly_data_path: str):
    """
    获取M2货币供应年率
    """
    print('🔍 正在获取M2货币供应年率...')
    fetch_with_cache(ak.macro_china_m2_yearly, macro_china_m2_yearly_data_path)


def fetch_macro_china_enterprise_boom_index(macro_china_enterprise_boom_index_data_path: str):
    """
    获取企业景气及企业家信心指数
    """
    print('🔍 正在获取企业景气及企业家信心指数...')
    fetch_with_cache(ak.macro_china_enterprise_boom_index, macro_china_enterprise_boom_index_data_path)


def fetch_macro_china_cpi(macro_china_cpi_data_path: str):
    """
    获取居民消费价格指数
    """
    print('🔍 正在获取居民消费价格指数...')
    fetch_with_cache(ak.macro_china_cpi, macro_china_cpi_data_path)


def fetch_macro_china_gdp(macro_china_gdp_data_path: str):
    """
    获取国内生产总值
    """
    print('🔍 正在获取国内生产总值...')
    fetch_with_cache(ak.macro_china_gdp, macro_china_gdp_data_path)


def fetch_macro_china_supply_of_money(macro_china_supply_of_money_data_path: str):
    """
    获取货币供应量
    """
    print('🔍 正在获取货币供应量...')
    fetch_with_cache(ak.macro_china_supply_of_money, macro_china_supply_of_money_data_path)


def fetch_macro_china_rmb(macro_china_rmb_data_path: str):
    """
    获取人民币汇率中间价
    """
    print('🔍 正在获取人民币汇率中间价...')
    fetch_with_cache(ak.macro_china_rmb, macro_china_rmb_data_path)


def fetch_macro_us(macro_us_data_path: str):
    """
    获取美国宏观数据
    """
    create_path(macro_us_data_path)



def parse_diverse_date(date_str: str, date_column: str) -> Optional[datetime]:
    """
    解析多种格式的日期字符串
    
    Args:
        date_str: 原始日期字符串
        date_column: 日期列的名称（用于判断格式）
    
    Returns:
        解析成功的datetime对象，解析失败返回None
    """
    if pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    
    try:
        # 处理格式: 2023-05-31
        if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', date_str):
            return datetime.strptime(date_str, '%Y-%m-%d')
        
        # 处理格式: 2008年02月份
        if '月份' in date_column and re.match(r'^\d{4}年\d{1,2}月份$', date_str):
            return datetime.strptime(date_str, '%Y年%m月份')
        
        # 处理格式: 1991-04-21 (TRADE_DATE列)
        if 'TRADE_DATE' in date_column and re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', date_str):
            return datetime.strptime(date_str, '%Y-%m-%d')
        
        # 处理格式: 202011 (date列)
        if 'date' in date_column.lower() and re.match(r'^\d{6}$', date_str):
            return datetime.strptime(date_str, '%Y%m')
        
        # 处理格式: 201501 (月份列)
        if '月份' in date_column and re.match(r'^\d{6}$', date_str):
            return datetime.strptime(date_str, '%Y%m')
        
        # 处理格式: 2024年第4季度
        if '季度' in date_column and re.match(r'^\d{4}年第[1-4]季度$', date_str):
            year = int(date_str[:4])
            quarter = int(date_str[6])
            month = quarter * 3
            day = 31 if month in [3, 12] else 30
            return datetime(year, month, day)
        
        # 处理格式: 2024年第1-4季度
        if '季度' in date_column and re.match(r'^\d{4}年第[1-4]-[1-4]季度$', date_str):
            year = int(date_str[:4])
            return datetime(year, 12, 31)
        
        # 处理格式: 2025.2 (统计时间列)
        if '统计时间' in date_column and re.match(r'^\d{4}\.\d{1,2}$', date_str):
            return datetime.strptime(date_str, '%Y.%m')
        
        # 处理格式: 2005-03 (年份列)
        if '年份' in date_column and re.match(r'^\d{4}-\d{1,2}$', date_str):
            return datetime.strptime(date_str, '%Y-%m')

        # 处理格式: 2025-04-01 11:33:01
        if re.match(r'^\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}$', date_str):
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        
    except ValueError:
        print(f"❌ 无法解析日期字符串: {date_str}")
        return None
    
    return None


def filter_csv_by_date_range(input_path: str, 
                            output_path: str,
                            start_date: str, 
                            end_date: str,
                            backup_dir: str = None):
    """
    处理单个CSV文件，按日期范围筛选数据并保存，同时备份原始文件
    
    Args:
        input_path: 输入CSV文件路径
        output_path: 输出CSV文件路径
        start_date: 开始日期 (格式: %Y%m%d) (包含)
        end_date: 结束日期 (格式: %Y%m%d) (包含)
        backup_dir: 备份目录路径，如果为None，则不备份
    """
    # 转换日期范围
    start_dt = datetime.strptime(start_date, '%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d').replace(hour=23, minute=59, second=59)
    
    # 读取CSV文件
    df = pd.read_csv(input_path, encoding='utf-8', low_memory=False)
    
    # 查找日期列
    date_columns = [col for col in df.columns 
                   if any(keyword in col for keyword in 
                         ['日期', '月份', 'TRADE_DATE', 'date', '季度', '统计时间', '年份', '报告期', '发布时间']) 
                         and col != '最新公告日期']
    
    if not date_columns:
        # 如果没有找到日期列，直接复制文件到输出路径
        shutil.copy2(input_path, output_path)
        print(f"提示: 文件 {os.path.basename(input_path)} 未找到日期列，已直接复制到输出路径")
        return
    
    # 备份原始文件
    if backup_dir:
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, os.path.basename(input_path))
        shutil.copy2(input_path, backup_path)
    
    # 筛选数据
    filtered_dfs = []
    for date_col in date_columns:
        # 解析日期列
        df['parsed_date'] = df[date_col].apply(
            lambda x: parse_diverse_date(x, date_col))
        # 筛选日期范围内的数据
        mask = (df['parsed_date'] >= start_dt) & (df['parsed_date'] <= end_dt)
        filtered_df = df.loc[mask].copy()
        
        if not filtered_df.empty:
            filtered_df.drop(columns=['parsed_date'], inplace=True)
            filtered_dfs.append(filtered_df)
    
    # 合并并保存结果
    if filtered_dfs:
        result_df = pd.concat(filtered_dfs).drop_duplicates()
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"处理完成: {os.path.basename(input_path)} -> 保存 {len(result_df)} 行数据")
    else:
        print(f"警告: 文件 {os.path.basename(input_path)} 在指定日期范围内无数据")


def process_all_csvs_in_directory(root_dir: str,
                                 output_dir: str,
                                 start_date: str,
                                 end_date: str,
                                 backup_dir: str = None):
    """
    截取日期范围内的数据
    递归处理目录下所有CSV文件
    
    Args:
        root_dir: 要处理的根目录
        output_dir: 输出目录
        start_date: 开始日期 (格式: %Y%m%d) 包含
        end_date: 结束日期 (格式: %Y%m%d) 包含
        backup_dir: 备份目录路径，如果为None，则不备份
    """
    print(f"🔍 开始处理目录: {root_dir}")
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 遍历所有CSV文件
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith('.csv'):
                input_path = os.path.join(root, file)
                # 保持原始目录结构
                rel_path = os.path.relpath(root, root_dir)
                if rel_path == '.':
                    rel_path = ''
                print(f"root: {root}, rel_path: {rel_path}")
                
                output_subdir = os.path.join(output_dir, rel_path)
                os.makedirs(output_subdir, exist_ok=True)
                
                output_path = os.path.join(output_subdir, file)
                
                # 处理文件
                try:
                    filter_csv_by_date_range(
                        input_path=input_path,
                        output_path=output_path,
                        start_date=start_date,
                        end_date=end_date,
                        backup_dir=os.path.join(backup_dir, rel_path) if backup_dir else None
                    )
                except Exception as e:
                    print(f"处理文件 {input_path} 时出错: {str(e)}")
    print(f"✅ 处理目录完成: {root_dir}")


if __name__ == "__main__":
    process_all_csvs_in_directory(
        root_dir="data/宏观数据",
        output_dir="output_data/宏观数据",
        start_date="20220101",
        end_date="20250331"
        # backup_dir="backup_data/宏观数据"
    )

    # filter_csv_by_date_range(
    #     input_path="data/宏观数据/中国宏观数据/金融指标/企业景气及企业家信心指数.csv",
    #     output_path="output_data/宏观数据/中国宏观数据/金融指标/企业景气及企业家信心指数.csv",
    #     start_date="20210101",
    #     end_date="20250331"
    #     # backup_dir="backup_data/宏观数据/中国宏观数据/产业指标"
    # )

