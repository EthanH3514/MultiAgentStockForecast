from keras.api import Input
from keras.api.layers import LSTM, Dense, Dropout, BatchNormalization
from keras.api.models import Model
from keras.api.regularizers import l2


def build_model(sequence_length=20, features=27):
    """
    构建LSTM股价预测模型
    sequence_length: 输入序列长度（20个交易日，约一个月）
    features: 特征数量（10个基础特征 + 17个技术指标）
    """
    # 输入层
    inputs = Input(shape=(sequence_length, features))
    
    # 第一个LSTM层 - 短期特征提取
    x1 = LSTM(512, return_sequences=True, dropout=0.2, 
             kernel_regularizer=l2(0.0001))(inputs)
    x1 = BatchNormalization()(x1)
    
    # 第二个LSTM层 - 长期特征提取
    x2 = LSTM(256, return_sequences=False, dropout=0.2,
             kernel_regularizer=l2(0.0001))(x1)
    x2 = BatchNormalization()(x2)
    
    # 全连接层
    x = Dense(128, activation='relu', kernel_regularizer=l2(0.0001))(x2)
    x = BatchNormalization()(x)
    x = Dropout(0.2)(x)
    
    x = Dense(64, activation='relu', kernel_regularizer=l2(0.0001))(x)
    x = BatchNormalization()(x)
    x = Dropout(0.2)(x)
    
    # 输出层（预测下一天的收盘价）
    outputs = Dense(1, activation='linear')(x)
    
    # 构建模型
    model = Model(inputs=inputs, outputs=outputs)
    return model
