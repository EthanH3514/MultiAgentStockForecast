import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from model import build_model, save_model
import os

def calculate_technical_indicators(df):
    """计算技术指标"""
    # 计算移动平均线
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

def prepare_data(data_path, sequence_length=20):
    """
    准备训练数据
    sequence_length: 输入序列长度（20个交易日，约一个月）
    """
    # 读取数据
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
    
    # 创建标签：1表示上涨，0表示下跌
    df['Label'] = (df['收盘'].shift(-1) > df['收盘']).astype(int)
    
    # 删除最后一行（因为没有下一天的数据作为标签）
    df = df[:-1]
    
    # 准备特征数据
    X = df[features].values
    y = df['Label'].values
    
    # 数据标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 保存scaler用于后续预测
    scaler_path = os.path.join(os.path.dirname(__file__), 'scaler.npy')
    np.save(scaler_path, scaler)
    
    # 创建序列数据
    X_seq, y_seq = [], []
    for i in range(len(X_scaled) - sequence_length):
        X_seq.append(X_scaled[i:(i + sequence_length)])
        y_seq.append(y[i + sequence_length])
    
    X_seq = np.array(X_seq)
    y_seq = np.array(y_seq)
    
    # 将3D序列数据重塑为2D（SVM需要2D输入）
    n_samples = X_seq.shape[0]
    X_reshaped = X_seq.reshape(n_samples, -1)
    
    # 划分训练集和验证集
    X_train, X_val, y_train, y_val = train_test_split(
        X_reshaped, y_seq, test_size=0.2, random_state=42
    )
    
    print(f"数据集大小：")
    print(f"训练集: {len(X_train)} 条数据")
    print(f"验证集: {len(X_val)} 条数据")
    
    return X_train, y_train, X_val, y_val

def train_model():
    # 获取数据路径
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_data_path = os.path.join(root_dir, 'data/600415/股票日线数据.csv')
    
    # 准备数据
    X_train, y_train, X_val, y_val = prepare_data(abs_data_path)
    
    # 构建模型
    model = build_model()
    
    # 训练模型
    print("开始训练模型...")
    model.fit(X_train, y_train)
    
    # 评估模型
    train_accuracy = model.score(X_train, y_train)
    val_accuracy = model.score(X_val, y_val)
    
    print(f"训练集准确率: {train_accuracy:.4f}")
    print(f"验证集准确率: {val_accuracy:.4f}")
    
    # 保存模型
    model_path = os.path.join(os.path.dirname(__file__), 'best_model.pkl')
    save_model(model, model_path)
    
    return model

if __name__ == "__main__":
    model = train_model()