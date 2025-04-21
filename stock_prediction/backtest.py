from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from predict_by_agent import get_format_predict_result_by_agent
import time
import os
import matplotlib.dates as mdates

plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体显示中文
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def backtest_prediction(
    stock_code: str,
    target_date: str,
    days_before: int,
    show_plot: bool = True,
    save_plot: bool = False
) -> pd.DataFrame:
    """运行回测并可视化结果
    
    参数:
        stock_code: 股票代码
        target_date: 要预测的目标日期 (格式: YYYYMMDD)
        days_before: 回溯天数
        show_plot: 是否显示图表
        save_plot: 是否保存图表
    """
    # 计算日期范围
    end_date = datetime.strptime(target_date, "%Y%m%d")
    start_date = end_date - timedelta(days=days_before)

    # 读取市场数据
    market_data_path = "data" + "/" + stock_code + "/" + "股票日线数据.csv"
    df = pd.read_csv(market_data_path, encoding='utf-8', low_memory=False)
    
    # 添加昨天的收盘价
    df['yesterday_close'] = df['收盘'].shift(1)
    
    # 转换日期格式并筛选日期范围
    df['日期'] = pd.to_datetime(df['日期'], format='%Y-%m-%d')
    df = df[(df['日期'] >= start_date) & (df['日期'] <= end_date)].copy()
    
    print('裁剪后的市场数据: ', df)
    print('裁剪后的市场数据长度: ', len(df))


    # 准备存储预测结果
    predictions = []
    correct_count = 0
    total_count = 0

    # 遍历数据
    for idx, row in df.iterrows():
        date = row['日期']
        print(f"正在处理第 {idx} 行数据, 日期: {date}")
        close_price = row['收盘']
        
        _start_date = (date - timedelta(days=151)).strftime("%Y%m%d")
        _target_date = date.strftime("%Y%m%d")
        print(f"滑动窗口范围: [{_start_date}, {_target_date})")

        # 获取预测结果 滑动窗口 [_start_date, _target_date) -> date
        predict_direction, predict_price = get_format_predict_result_by_agent(
            stock_code, _start_date, _target_date
        )

        yesterday_close_price = row['yesterday_close'] if not pd.isna(row['yesterday_close']) else 0
        
        print("idx: ", idx, "yesterday_close_price: ", yesterday_close_price)

        # if idx > 0:
        #     prev_row = df.iloc[idx - 1]
        #     yesterday_close_price = float(prev_row['收盘'])
        # else:
        #     print("Error: 第 0 行数据没有前一天数据")
        
        # 评估预测准确性
        if predict_direction == 1:  # 预测上涨
            is_correct = (close_price - yesterday_close_price) * (predict_price - yesterday_close_price) > 0
        else:  # 预测下跌
            is_correct = (close_price - yesterday_close_price) * (predict_price - yesterday_close_price) < 0
        
        # 记录预测结果
        predictions.append({
            'date': date,
            'close': close_price,
            'predict_price': predict_price,
            'yesterday_close_price': yesterday_close_price,
            'predict_direction': predict_direction,
            'is_correct': is_correct
        })
        
        if is_correct:
            correct_count += 1
        total_count += 1

        print(f"预测结果: {predict_direction}, 预测价格: {predict_price}, 正确: {is_correct}")
        print(predictions)
        # time.sleep(1000)

    # 转换为DataFrame便于分析
    result_df = pd.DataFrame(predictions)    

    result_df['date'] = pd.to_datetime(result_df['date'])
    
    # 2. 计算实际涨跌方向
    result_df['actual_direction'] = (result_df['close'] - result_df['yesterday_close_price']).apply(
        lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    
    result_df['is_correct'] = (result_df['predict_direction'] == result_df['actual_direction'])
    
    # 3. 计算各类准确率
    total_accuracy = result_df['is_correct'].mean() * 100
    up_accuracy = result_df[result_df['predict_direction'] == 1]['is_correct'].mean() * 100
    down_accuracy = result_df[result_df['predict_direction'] == -1]['is_correct'].mean() * 100
    actual_up_accuracy = result_df[result_df['actual_direction'] == 1]['is_correct'].mean() * 100
    actual_down_accuracy = result_df[result_df['actual_direction'] == -1]['is_correct'].mean() * 100
    
    # 4. 打印统计结果
    print("========== 预测准确率统计 ==========")
    print(f"总体准确率: {total_accuracy:.1f}%" if not pd.isna(total_accuracy) else "总体准确率: 无数据")
    print(f"\n按预测方向分类:")
    print(f"  预测上涨准确率: {up_accuracy:.1f}% (共{len(result_df[result_df['predict_direction']==1])}次)" if not pd.isna(up_accuracy) else "预测上涨准确率: 无数据 (共0次)")
    print(f"  预测下跌准确率: {down_accuracy:.1f}% (共{len(result_df[result_df['predict_direction']==-1])}次)" if not pd.isna(down_accuracy) else "预测下跌准确率: 无数据 (共0次)")
    print(f"\n按实际走势分类:")
    print(f"  实际上涨时的预测准确率: {actual_up_accuracy:.1f}% (共{len(result_df[result_df['actual_direction']==1])}天)" if not pd.isna(actual_up_accuracy) else "实际上涨时的预测准确率: 无数据 (共0天)")
    print(f"  实际下跌时的预测准确率: {actual_down_accuracy:.1f}% (共{len(result_df[result_df['actual_direction']==-1])}天)" if not pd.isna(actual_down_accuracy) else "实际下跌时的预测准确率: 无数据 (共0天)")
    
    # 5. 绘制图表
    plt.figure(figsize=(14, 10))
    
    # 价格走势
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(result_df['date'], result_df['close'], 'ko-', label='实际收盘价')
    ax1.plot(result_df['date'], result_df['predict_price'], 'bx--', label='预测价格')
    ax1.set_title(f'价格走势与预测对比 (总体准确率: {total_accuracy:.1f}%)', fontsize=12, pad=20)
    ax1.set_ylabel('价格')
    ax1.legend()
    
    # 添加准确率标注
    accuracy_text = (f"预测上涨准确率: {up_accuracy:.1f}%\n"
                    f"预测下跌准确率: {down_accuracy:.1f}%\n"
                    f"实际上涨时准确率: {actual_up_accuracy:.1f}%\n"
                    f"实际下跌时准确率: {actual_down_accuracy:.1f}%")
    ax1.text(0.02, 0.98, accuracy_text, transform=ax1.transAxes,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 标记预测正确/错误
    correct_dates = result_df[result_df['is_correct']]['date']
    incorrect_dates = result_df[~result_df['is_correct']]['date']
    ax1.scatter(correct_dates, result_df.loc[result_df['is_correct'], 'close'], 
                color='green', s=100, label='预测正确', marker='^')
    ax1.scatter(incorrect_dates, result_df.loc[~result_df['is_correct'], 'close'], 
                color='red', s=100, label='预测错误', marker='v')
    
    # 涨跌方向
    ax2 = plt.subplot(2, 1, 2)
    ax2.plot(result_df['date'], result_df['actual_direction'], 'go-', label='实际方向')
    ax2.plot(result_df['date'], result_df['predict_direction'], 'rx--', label='预测方向')
    ax2.set_title('涨跌方向对比 (1=上涨, -1=下跌)', fontsize=12)
    ax2.set_ylabel('方向')
    ax2.legend()
    
    # 添加方向预测准确率标注
    ax2.text(0.02, 0.98, f"方向预测准确率: {total_accuracy:.1f}%", 
            transform=ax2.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 格式化x轴日期
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
        plt.setp(ax.get_xticklabels(), rotation=45)
    
    plt.tight_layout()

    _start_date = start_date.strftime("%Y%m%d")
    if save_plot:
        plt.savefig(f"results/{stock_code}_backtest_{_start_date}_{target_date}_{days_before}.png", dpi=300, bbox_inches='tight')
        print(f"图表已保存至: results/{stock_code}_backtest_{_start_date}_{target_date}_{days_before}.png")
    plt.show()
    
    return result_df


def analyze_prediction_accuracy(csv_path, save_plot: bool = True):
    """
    已废弃
    """
    # 1. 读取CSV文件
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # 2. 计算实际涨跌方向
    df['actual_direction'] = (df['close'] - df['yesterday_price']).apply(
        lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    
    df['is_correct'] = (df['predict_direction'] == df['actual_direction'])
    
    # 3. 计算各类准确率
    total_accuracy = df['is_correct'].mean() * 100
    up_accuracy = df[df['predict_direction'] == 1]['is_correct'].mean() * 100
    down_accuracy = df[df['predict_direction'] == -1]['is_correct'].mean() * 100
    actual_up_accuracy = df[df['actual_direction'] == 1]['is_correct'].mean() * 100
    actual_down_accuracy = df[df['actual_direction'] == -1]['is_correct'].mean() * 100
    
    # 4. 打印统计结果
    print("========== 预测准确率统计 ==========")
    print(f"总体准确率: {total_accuracy:.1f}%")
    print(f"\n按预测方向分类:")
    print(f"  预测上涨准确率: {up_accuracy:.1f}% (共{len(df[df['predict_direction']==1])}次)")
    print(f"  预测下跌准确率: {down_accuracy:.1f}% (共{len(df[df['predict_direction']==-1])}次)")
    print(f"\n按实际走势分类:")
    print(f"  实际上涨时的预测准确率: {actual_up_accuracy:.1f}% (共{len(df[df['actual_direction']==1])}天)")
    print(f"  实际下跌时的预测准确率: {actual_down_accuracy:.1f}% (共{len(df[df['actual_direction']==-1])}天)")
    
    # 5. 绘制图表
    plt.figure(figsize=(14, 10))
    
    # 价格走势
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(df['date'], df['close'], 'ko-', label='实际收盘价')
    ax1.plot(df['date'], df['predict_price'], 'bx--', label='预测价格')
    ax1.set_title(f'价格走势与预测对比 (总体准确率: {total_accuracy:.1f}%)', fontsize=12, pad=20)
    ax1.set_ylabel('价格')
    ax1.legend()
    
    # 添加准确率标注
    accuracy_text = (f"预测上涨准确率: {up_accuracy:.1f}%\n"
                    f"预测下跌准确率: {down_accuracy:.1f}%\n"
                    f"实际上涨时准确率: {actual_up_accuracy:.1f}%\n"
                    f"实际下跌时准确率: {actual_down_accuracy:.1f}%")
    ax1.text(0.02, 0.98, accuracy_text, transform=ax1.transAxes,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 标记预测正确/错误
    correct_dates = df[df['is_correct']]['date']
    incorrect_dates = df[~df['is_correct']]['date']
    ax1.scatter(correct_dates, df.loc[df['is_correct'], 'close'], 
                color='green', s=100, label='预测正确', marker='^')
    ax1.scatter(incorrect_dates, df.loc[~df['is_correct'], 'close'], 
                color='red', s=100, label='预测错误', marker='v')
    
    # 涨跌方向
    ax2 = plt.subplot(2, 1, 2)
    ax2.plot(df['date'], df['actual_direction'], 'go-', label='实际方向')
    ax2.plot(df['date'], df['predict_direction'], 'rx--', label='预测方向')
    ax2.set_title('涨跌方向对比 (1=上涨, -1=下跌)', fontsize=12)
    ax2.set_ylabel('方向')
    ax2.legend()
    
    # 添加方向预测准确率标注
    ax2.text(0.02, 0.98, f"方向预测准确率: {total_accuracy:.1f}%", 
            transform=ax2.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 格式化x轴日期
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
        plt.setp(ax.get_xticklabels(), rotation=45)
    
    plt.tight_layout()
    if save_plot:
        plt.savefig(f"results/600415_backtest_20250331_20250403_153553.png", dpi=300, bbox_inches='tight')
        print(f"图表已保存至: results/600415_backtest_20250331_20250403_153553.png")
    plt.show()
    
    return df


if __name__ == "__main__":
    stock_code = "600415"
    target_date = "20250409"
    days_before = 10
    
    # 运行回测并显示图表
    result = backtest_prediction(
        stock_code=stock_code,
        target_date=target_date,
        days_before=days_before,
        show_plot=True,
        save_plot=True
    )
    
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S").replace(":", "_")
    # 可选: 保存详细结果到CSV
    result.to_csv(f"results/{stock_code}_backtest_details_{target_date}_{current_time}.csv", index=False)

    # csv_path = "results/600415_backtest_details_20250331_20250403_153701.csv"
    # analyze_prediction_accuracy(csv_path)

