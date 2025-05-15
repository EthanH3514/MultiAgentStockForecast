import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns
from model import build_model
import os
from sklearn.preprocessing import StandardScaler
from torch.serialization import safe_globals

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

print(torch.__version__)
print(torch.cuda.is_available())

def calculate_technical_indicators(df):
    """计算技术指标"""
    # 基础特征
    df['MA5'] = df['收盘'].rolling(window=5).mean()
    df['MA10'] = df['收盘'].rolling(window=10).mean()
    df['MA20'] = df['收盘'].rolling(window=20).mean()
    
    # RSI
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['收盘'].ewm(span=12, adjust=False).mean()
    exp2 = df['收盘'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 布林带
    df['BB_middle'] = df['收盘'].rolling(window=20).mean()
    df['BB_upper'] = df['BB_middle'] + 2 * df['收盘'].rolling(window=20).std()
    df['BB_lower'] = df['BB_middle'] - 2 * df['收盘'].rolling(window=20).std()
    
    # 成交量指标
    df['Volume_MA5'] = df['成交量'].rolling(window=5).mean()
    df['Volume_MA10'] = df['成交量'].rolling(window=10).mean()
    
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

def plot_predictions(y_true, y_pred, dates, train_y_true=None, train_y_pred=None, train_dates=None):
    """绘制预测结果和真实值的对比图"""
    plt.figure(figsize=(20, 10))
    
    # 绘制训练数据
    if train_y_true is not None and train_y_pred is not None and train_dates is not None:
        plt.plot(train_dates, train_y_true, label='训练集真实值', color='blue', alpha=0.5)
        plt.plot(train_dates, train_y_pred, label='训练集预测值', color='red', alpha=0.5, linestyle='--')
    
    # 绘制测试数据
    plt.plot(dates, y_true, label='测试集真实值', color='blue', linewidth=2)
    plt.plot(dates, y_pred, label='测试集预测值', color='red', linestyle='--', linewidth=2)
    
    plt.title('股价预测结果对比（训练集和测试集）')
    plt.xlabel('日期')
    plt.ylabel('股价')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), 'prediction_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()

def plot_error_distribution(y_true, y_pred):
    """绘制误差分布图"""
    errors = y_pred - y_true
    error_percentages = (errors / y_true) * 100
    
    plt.figure(figsize=(15, 10))
    
    # 误差直方图
    plt.subplot(2, 1, 1)
    sns.histplot(error_percentages, bins=50)
    plt.title('预测误差百分比分布')
    plt.xlabel('误差百分比 (%)')
    plt.ylabel('频数')
    plt.grid(True)
    
    # 误差箱线图
    plt.subplot(2, 1, 2)
    sns.boxplot(y=error_percentages)
    plt.title('预测误差百分比箱线图')
    plt.ylabel('误差百分比 (%)')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), 'error_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()

def plot_direction_accuracy(y_true, y_pred, dates):
    """绘制涨跌预测准确度分析图"""
    # 计算实际涨跌
    true_direction = np.diff(y_true) > 0
    # 计算预测涨跌
    pred_direction = np.diff(y_pred) > 0
    # 计算准确度
    accuracy = np.mean(true_direction == pred_direction) * 100
    
    plt.figure(figsize=(15, 10))
    
    # 绘制涨跌预测准确度热力图
    plt.subplot(2, 1, 1)
    confusion_matrix = np.zeros((2, 2))
    for t, p in zip(true_direction, pred_direction):
        confusion_matrix[int(t), int(p)] += 1
    
    sns.heatmap(confusion_matrix, annot=True, fmt='g', cmap='Blues',
                xticklabels=['跌', '涨'], yticklabels=['跌', '涨'])
    plt.title('涨跌预测混淆矩阵')
    plt.xlabel('预测方向')
    plt.ylabel('实际方向')
    
    # 绘制准确率随时间变化
    plt.subplot(2, 1, 2)
    window_size = 20  # 20天滑动窗口
    rolling_accuracy = []
    for i in range(window_size, len(true_direction)):
        window_true = true_direction[i-window_size:i]
        window_pred = pred_direction[i-window_size:i]
        rolling_accuracy.append(np.mean(window_true == window_pred) * 100)
    
    plt.plot(dates[window_size+1:], rolling_accuracy)
    plt.title('涨跌预测准确率随时间变化（20天滑动窗口）')
    plt.xlabel('日期')
    plt.ylabel('准确率 (%)')
    plt.grid(True)
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), 'direction_accuracy.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    return accuracy

def test_model(model_path='best_model.pt', 
               data_path='data/600415/股票日线数据.csv',
               scaler_path='scaler.pt'):
    """测试模型性能"""
    # 加载数据
    df = pd.read_csv(data_path)
    
    # 计算技术指标
    df = calculate_technical_indicators(df)
    
    # 选择需要的特征
    base_features = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', 
                    '振幅', '涨跌幅', '涨跌额', '换手率']
    
    technical_features = ['MA5', 'MA10', 'MA20', 'RSI', 'MACD', 'Signal', 
                         'BB_middle', 'BB_upper', 'BB_lower', 'Price_Change', 
                         'Volume_Change', 'Volatility', 'Momentum', 'VWAP', 
                         'Price_MA_Ratio', 'Volume_MA_Ratio']
    
    features = base_features + technical_features
    
    # 删除包含NaN的行
    df = df.dropna()
    
    data = df[features].values
    
    # 加载scaler
    with safe_globals([StandardScaler]):
        scaler = torch.load(scaler_path, weights_only=False)
    
    # 数据标准化
    scaled_data = scaler.transform(data)
    
    # 准备数据
    sequence_length = 20  # 20个交易日，约一个月
    
    # 划分数据集：60%训练集，15%测试集，25%预留集
    train_size = int(len(scaled_data) * 0.6)
    test_size = int(len(scaled_data) * 0.15)
    
    train_data = scaled_data[:train_size]
    test_data = scaled_data[train_size:train_size + test_size]
    reserve_data = scaled_data[train_size + test_size:]  # 预留集
    
    # 准备训练数据
    X_train = []
    y_train = []
    train_dates = []
    
    for i in range(len(train_data) - sequence_length):
        X_train.append(train_data[i:(i + sequence_length)])
        y_train.append(train_data[i + sequence_length, 1])  # 预测收盘价（索引1）
        train_dates.append(df['日期'].iloc[i + sequence_length])
    
    X_train = torch.FloatTensor(np.array(X_train))
    y_train = torch.FloatTensor(np.array(y_train))
    train_dates = np.array(train_dates)
    
    # 准备测试数据
    X_test = []
    y_test = []
    test_dates = []
    
    for i in range(len(test_data) - sequence_length):
        X_test.append(test_data[i:(i + sequence_length)])
        y_test.append(test_data[i + sequence_length, 1])  # 预测收盘价（索引1）
        test_dates.append(df['日期'].iloc[train_size + i + sequence_length])
    
    X_test = torch.FloatTensor(np.array(X_test))
    y_test = torch.FloatTensor(np.array(y_test))
    test_dates = np.array(test_dates)
    
    print(f"数据集大小：")
    print(f"训练集: {len(train_data)} 条数据")
    print(f"测试集: {len(test_data)} 条数据")
    print(f"预留集: {len(reserve_data)} 条数据")
    print(f"\nX_train shape: {X_train.shape}")
    print(f"y_train shape: {y_train.shape}")
    print(f"X_test shape: {X_test.shape}")
    print(f"y_test shape: {y_test.shape}")
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 加载模型
    model = build_model(sequence_length=X_train.shape[1], 
                       features=X_train.shape[2])
    model.load_state_dict(torch.load(model_path))
    model = model.to(device)
    model.eval()
    
    # 将数据移动到设备
    X_train = X_train.to(device)
    y_train = y_train.to(device)
    X_test = X_test.to(device)
    y_test = y_test.to(device)
    
    # 预测训练集
    with torch.no_grad():
        train_pred = model(X_train).squeeze().cpu().numpy()
    y_train = y_train.cpu().numpy()
    
    # 预测测试集
    with torch.no_grad():
        test_pred = model(X_test).squeeze().cpu().numpy()
    y_test = y_test.cpu().numpy()
    
    # 反归一化训练集
    dummy_array_train_pred = np.zeros((len(train_pred), data.shape[1]))
    dummy_array_train = np.zeros((len(y_train), data.shape[1]))
    
    dummy_array_train_pred[:, 1] = train_pred  # 使用reshape(-1)将预测结果展平
    dummy_array_train[:, 1] = y_train
    
    train_pred = scaler.inverse_transform(dummy_array_train_pred)[:, 1]
    y_train = scaler.inverse_transform(dummy_array_train)[:, 1]
    
    # 反归一化测试集
    dummy_array_test_pred = np.zeros((len(test_pred), data.shape[1]))
    dummy_array_test = np.zeros((len(y_test), data.shape[1]))
    
    dummy_array_test_pred[:, 1] = test_pred  # 使用reshape(-1)将预测结果展平
    dummy_array_test[:, 1] = y_test
    
    test_pred = scaler.inverse_transform(dummy_array_test_pred)[:, 1]
    y_test = scaler.inverse_transform(dummy_array_test)[:, 1]
    
    # 计算评估指标
    mse = mean_squared_error(y_test, test_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, test_pred)
    
    # 计算涨跌预测准确度
    direction_accuracy = plot_direction_accuracy(y_test, test_pred, test_dates)
    
    print("\n模型测试结果：")
    print(f"均方误差 (MSE): {mse:.2f}")
    print(f"均方根误差 (RMSE): {rmse:.2f}")
    print(f"平均绝对误差 (MAE): {mae:.2f}")
    print(f"涨跌预测准确率: {direction_accuracy:.2f}%")
    
    # 计算预测准确率（允许5%的误差范围）
    accuracy = np.mean(np.abs(test_pred - y_test) / y_test < 0.05) * 100
    print(f"预测准确率 (误差<5%): {accuracy:.2f}%")
    
    # 绘制预测结果对比图
    plot_predictions(y_test, test_pred, test_dates, y_train, train_pred, train_dates)
    
    # 绘制误差分布图
    plot_error_distribution(y_test, test_pred)
    
    return mse, rmse, mae, accuracy, direction_accuracy

if __name__ == "__main__":
    # 获取数据路径
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print('root_dir: ', root_dir)
    abs_data_path = os.path.join(root_dir, 'data/600415/股票日线数据.csv')
    model_path = os.path.join(root_dir, 'traditional_model', 'Transformer', 'best_model.pt')
    scaler_path = os.path.join(root_dir, 'traditional_model', 'Transformer', 'scaler.pt')
    
    test_model(model_path=model_path, data_path=abs_data_path, scaler_path=scaler_path)