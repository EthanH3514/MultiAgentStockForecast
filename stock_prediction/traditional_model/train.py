import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from model import build_model
from keras.api.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from keras.api.losses import MeanSquaredError
import os

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
    
    data = df[features].values
    
    # 数据标准化
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data)
    
    # 保存scaler用于后续预测
    np.save('scaler.npy', scaler)
    
    X, y = [], []
    
    # 创建序列，使用滑动窗口
    for i in range(len(scaled_data) - sequence_length):
        X.append(scaled_data[i:(i + sequence_length)])
        y.append(scaled_data[i + sequence_length, 1])  # 预测收盘价（索引1）
    
    X = np.array(X)
    y = np.array(y)
    
    # 划分数据集：60%训练集，15%验证集，25%预留集
    train_size = int(len(X) * 0.6)
    val_size = int(len(X) * 0.15)
    
    # 训练集：前60%
    X_train = X[:train_size]
    y_train = y[:train_size]
    
    # 验证集：训练集之后的15%
    X_val = X[train_size:train_size + val_size]
    y_val = y[train_size:train_size + val_size]
    
    print(f"数据集大小：")
    print(f"训练集: {len(X_train)} 条数据")
    print(f"验证集: {len(X_val)} 条数据")
    print(f"预留集: {len(X) - train_size - val_size} 条数据")
    
    return X_train, y_train, X_val, y_val

def train_model():
    # 准备数据
    X_train, y_train, X_val, y_val = prepare_data('data/600415/股票日线数据.csv')
    
    # 构建模型
    model = build_model(sequence_length=X_train.shape[1], 
                       features=X_train.shape[2])
    
    # 编译模型
    model.compile(optimizer='adam', 
                 loss='mse',  # 使用字符串形式的MSE损失函数
                 metrics=['mae'])
    
    # 设置回调函数
    early_stopping = EarlyStopping(monitor='val_loss', 
                                 patience=200,  # 增加耐心值
                                 restore_best_weights=True,
                                 verbose=1)
    
    model_checkpoint = ModelCheckpoint('best_model.h5', 
                                     monitor='val_loss', 
                                     save_best_only=True, 
                                     mode='min',
                                     verbose=1)
    
    reduce_lr = ReduceLROnPlateau(monitor='val_loss',
                                 factor=0.2,  # 更温和的学习率衰减
                                 patience=50,  # 增加耐心值
                                 min_lr=0.0000001,
                                 verbose=1)
    
    # 训练模型
    history = model.fit(
        X_train, y_train,
        epochs=3000,  # 增加训练轮数
        batch_size=64,
        validation_data=(X_val, y_val),
        callbacks=[early_stopping, model_checkpoint, reduce_lr],
        verbose=1
    )
    
    # 保存训练历史
    np.save('training_history.npy', history.history)
    
    return model, history

if __name__ == "__main__":
    model, history = train_model()
