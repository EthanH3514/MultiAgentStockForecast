import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from model import build_model
import os
from torch.serialization import safe_globals

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

def prepare_data(data_path, sequence_length=20):
    """准备训练数据"""
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
    with safe_globals([StandardScaler]):
        torch.save(scaler, os.path.join(os.path.dirname(__file__), 'scaler.pt'))
    
    X, y = [], []
    
    # 创建序列，使用滑动窗口
    for i in range(len(scaled_data) - sequence_length):
        X.append(scaled_data[i:(i + sequence_length)])
        y.append(scaled_data[i + sequence_length, 1])  # 预测收盘价（索引1）
    
    X = torch.FloatTensor(np.array(X))
    y = torch.FloatTensor(np.array(y))
    
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
    # 获取数据路径
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_data_path = os.path.join(root_dir, 'data/600415/股票日线数据.csv')
    
    # 准备数据
    X_train, y_train, X_val, y_val = prepare_data(abs_data_path)
    
    # 构建模型
    model = build_model(sequence_length=X_train.shape[1], 
                       features=X_train.shape[2])
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    X_train = X_train.to(device)
    y_train = y_train.to(device)
    X_val = X_val.to(device)
    y_val = y_val.to(device)
    
    # 定义损失函数和优化器
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.2, patience=50, min_lr=0.0000001)
    
    # 训练参数
    epochs = 3000
    batch_size = 64
    best_val_loss = float('inf')
    patience = 200
    patience_counter = 0
    
    # 训练历史
    history = {'train_loss': [], 'val_loss': []}
    
    # 训练循环
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        
        # 批次训练
        for i in range(0, len(X_train), batch_size):
            batch_X = X_train[i:i+batch_size]
            batch_y = y_train[i:i+batch_size]
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs.squeeze(), batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= (len(X_train) / batch_size)
        
        # 验证
        model.eval()
        with torch.no_grad():
            val_outputs = model(X_val)
            val_loss = criterion(val_outputs.squeeze(), y_val)
            val_loss = val_loss.item()
        
        # 更新学习率
        scheduler.step(val_loss)
        
        # 保存历史
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        
        # 打印进度
        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch+1}/{epochs}], Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}')
        
        # 保存最佳模型
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), os.path.join(os.path.dirname(__file__), 'best_model.pt'))
            patience_counter = 0
        else:
            patience_counter += 1
        
        # 早停
        if patience_counter >= patience:
            print(f'Early stopping at epoch {epoch+1}')
            break
    
    # 保存训练历史
    torch.save(history, os.path.join(os.path.dirname(__file__), 'training_history.pt'))
    
    return model, history

if __name__ == '__main__':
    train_model()