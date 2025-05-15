import torch
import pandas as pd
import numpy as np

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

def predict_next_day(model_path='best_model.pt', 
                    data_path='data/600415/股票日线数据.csv',
                    scaler_path='scaler.pt'):
    """使用最近20天的数据预测下一天的股价"""
    # 加载数据
    df = pd.read_csv(data_path)
    
    # 计算技术指标
    df = calculate_technical_indicators(df)
    
    # 选择需要的特征
    base_features = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
    technical_features = ['MA5', 'MA10', 'MA20', 'RSI', 'MACD', 'Signal', 'BB_middle', 'BB_upper', 'BB_lower',
                         'Price_Change', 'Volume_Change', 'Volatility', 'Momentum', 'VWAP', 'Price_MA_Ratio', 'Volume_MA_Ratio']
    
    features = base_features + technical_features
    data = df[features].values
    
    # 加载scaler
    scaler = torch.load(scaler_path)
    
    # 数据归一化
    scaled_data = scaler.transform(data)
    
    # 取最后20天的数据
    last_month = scaled_data[-20:]
    
    # 转换为PyTorch张量
    X = torch.FloatTensor(last_month).unsqueeze(0)  # 添加批次维度
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    X = X.to(device)
    
    # 加载模型
    from model import build_model
    model = build_model(sequence_length=20, features=len(features))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    
    # 预测
    with torch.no_grad():
        pred_scaled = model(X)
    
    # 反归一化
    dummy_array = np.zeros((1, data.shape[1]))
    dummy_array[0, 1] = pred_scaled.cpu().numpy()[0]  # 收盘价在第二列（索引1）
    pred = scaler.inverse_transform(dummy_array)
    
    # 获取原始数据的日期
    dates = pd.to_datetime(df['日期'].iloc[-252:])
    last_date = dates.iloc[-1]
    
    # 计算预测日期（下一个工作日）
    next_date = pd.date_range(start=last_date, periods=2, freq='B')[1]
    
    # 计算涨跌幅
    last_close = df['收盘'].iloc[-1]
    predicted_close = pred[0, 1]
    change_rate = ((predicted_close - last_close) / last_close) * 100
    
    # 确定预测方向
    direction = 1 if change_rate > 0 else -1
    
    return {
        'prediction_date': next_date.strftime('%Y-%m-%d'),
        'predicted_price': round(float(predicted_close), 2),
        'direction': direction,
        'change_rate': round(float(change_rate), 2)
    }