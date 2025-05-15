import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]

class StockTransformer(nn.Module):
    def __init__(self, input_dim=27, d_model=256, nhead=8, num_layers=4, dropout=0.2):
        """
        构建Transformer股价预测模型
        input_dim: 输入特征维度（10个基础特征 + 17个技术指标）
        d_model: Transformer模型的维度
        nhead: 多头注意力的头数
        num_layers: Transformer编码器层数
        dropout: Dropout比率
        """
        super(StockTransformer, self).__init__()
        
        # 特征映射层
        self.input_projection = nn.Linear(input_dim, d_model)
        
        # 位置编码
        self.pos_encoder = PositionalEncoding(d_model)
        
        # Transformer编码器层
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # 输出层
        self.decoder = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1)
        )

    def forward(self, x):
        # 特征映射
        x = self.input_projection(x)
        
        # 位置编码
        x = self.pos_encoder(x)
        
        # Transformer编码器
        x = self.transformer_encoder(x)
        
        # 取序列最后一个时间步的输出进行预测
        x = x[:, -1, :]
        
        # 解码器输出预测值
        out = self.decoder(x)
        
        return out

def build_model(sequence_length=20, features=27):
    """
    构建Transformer模型实例
    sequence_length: 输入序列长度（20个交易日，约一个月）
    features: 特征数量（10个基础特征 + 17个技术指标）
    """
    model = StockTransformer(input_dim=features)
    return model