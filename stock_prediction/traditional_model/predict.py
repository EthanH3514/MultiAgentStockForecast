import numpy as np
import pandas as pd
from keras.api.models import load_model
from sklearn.preprocessing import MinMaxScaler

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

def predict_next_day(model_path='best_model.h5', 
                    data_path='data/600415/股票日线数据.csv',
                    scaler_path='scaler.npy'):
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
    scaler = np.load(scaler_path, allow_pickle=True).item()
    
    # 数据归一化
    scaled_data = scaler.fit_transform(data)
    
    # 取最后20天的数据
    last_month = scaled_data[-20:]
    
    # 重塑数据为模型输入格式
    X = last_month.reshape(1, 20, len(features))
    
    # 加载模型并预测
    model = load_model(model_path, custom_objects={'mse': 'mean_squared_error'})
    pred_scaled = model.predict(X)
    
    # 反归一化
    # 创建一个与原始数据相同形状的零数组
    dummy_array = np.zeros((1, data.shape[1]))
    # 将预测的收盘价放在正确的位置
    dummy_array[0, 1] = pred_scaled[0]
    # 反归一化
    pred = scaler.inverse_transform(dummy_array)
    
    # 获取原始数据的日期
    dates = pd.to_datetime(df['日期'].iloc[-252:])
    last_date = dates.iloc[-1]
    
    # 生成下一个交易日的日期
    next_date = last_date + pd.Timedelta(days=1)
    while next_date.weekday() >= 5:  # 跳过周末
        next_date += pd.Timedelta(days=1)
    
    # 获取最近一天的收盘价
    last_close = df['收盘'].iloc[-1]
    predicted_price = pred[0, 1]
    
    # 计算涨跌幅
    price_change = predicted_price - last_close
    price_change_rate = (price_change / last_close) * 100
    
    # 判断涨跌方向
    direction = 1 if price_change > 0 else -1
    
    # 创建预测结果DataFrame
    results = pd.DataFrame({
        '日期': [next_date],
        '预测收盘价': [predicted_price],
        '涨跌方向': [direction],
        '涨跌幅': [price_change_rate]
    })
    
    print("\n下一天股价预测：")
    print(results)
    
    return results

if __name__ == "__main__":
    predict_next_day()
