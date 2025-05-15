import numpy as np
import pandas as pd
from stock_prediction.traditional_model.SVM.model import load_model

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

def predict_next_day(model_path='best_model.pkl', 
                    data_path='data/600415/股票日线数据.csv',
                    scaler_path='scaler.npy'):
    """使用最近20天的数据预测下一天的涨跌"""
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
    scaled_data = scaler.transform(data)
    
    # 取最后20天的数据
    last_month = scaled_data[-20:]
    
    # 重塑数据为一维数组（SVM需要2D输入）
    X = last_month.reshape(1, -1)
    
    # 加载模型并预测
    model = load_model(model_path)
    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    
    # 获取原始数据的日期
    dates = pd.to_datetime(df['日期'])
    last_date = dates.iloc[-1]
    
    # 生成下一个交易日的日期
    next_date = last_date + pd.Timedelta(days=1)
    while next_date.weekday() >= 5:  # 跳过周末
        next_date += pd.Timedelta(days=1)
    
    # 获取最近一天的收盘价
    last_close = df['收盘'].iloc[-1]
    
    # 预测涨跌方向和概率
    direction = 1 if prediction == 1 else -1
    confidence = probabilities[1] if prediction == 1 else probabilities[0]
    
    # 创建预测结果DataFrame
    results = pd.DataFrame({
        '日期': [next_date],
        '涨跌方向': [direction],
        '预测概率': [confidence],
        '当前价格': [last_close]
    })
    
    print("\n下一天股价涨跌预测：")
    print(results)
    print(f"预测{'上涨' if direction == 1 else '下跌'}的概率: {confidence:.2%}")
    
    return results

if __name__ == "__main__":
    predict_next_day()