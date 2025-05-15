<template>
  <div class="traditional-result">
    <el-row>
      <el-col :span="24">
        <div class="prediction-summary">
          <h3>预测摘要</h3>
          <div class="prediction-date">
            <span class="date-label">预测日期：</span>
            <span class="date">{{ predictionResult.prediction_date }}</span>
          </div>
          <!-- LSTM和Transformer显示预测价格 -->
          <template v-if="modelType === 'LSTM' || modelType === 'Transformer'">
            <div class="prediction-price">
              <span class="price-label">预测价格：</span>
              <span class="price">{{ predictionResult.predicted_price }}</span>
            </div>
          </template>
          <!-- 都显示预测方向 -->
          <div class="prediction-direction">
            <span class="direction-label">预测方向：</span>
            <span class="direction" :class="{'up': predictionResult.direction == 1, 'down': predictionResult.direction == -1}">
              {{ predictionResult.direction === 1 ? '看涨 ↑' : '看跌 ↓' }}
            </span>
          </div>
          <template v-if="modelType === 'SVM'">
            <div class="prediction-confidence">
              <span class="confidence-label">预测概率：</span>
              <span class="confidence">{{ predictionResult.confidence * 100 }}%</span>
            </div>
            <div class="current-price">
              <span class="current-price-label">当前价格：</span>
              <span class="current-price-value">{{ predictionResult.current_price }}</span>
            </div>
          </template>
          <!-- LSTM和Transformer显示预测涨跌幅 -->
          <template v-if="modelType === 'LSTM' || modelType === 'Transformer'">
            <div class="prediction-change">
              <span class="change-label">预测涨跌幅：</span>
              <span class="change" :class="{'up': predictionResult.direction == 1, 'down': predictionResult.direction == -1}">
                {{ predictionResult.change_rate }}%
              </span>
            </div>
          </template>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  name: 'TraditionalPrediction',
  props: {
    predictionResult: {
      type: Object,
      required: true,
    },
    modelType: {
      type: String,
      required: true,
      validator: function(value) {
        return ['LSTM', 'SVM', 'Transformer'].indexOf(value) !== -1;
      },
    },
  },
};
</script>

<style scoped>
.prediction-summary {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.prediction-summary h3 {
  margin-bottom: 15px;
  color: #303133;
}

.direction-label, .price-label, .date-label, .change-label,
.confidence-label, .current-price-label {
  font-weight: bold;
  margin-right: 10px;
}

.direction.up, .change.up {
  color: #f56c6c !important;
  font-weight: bold;
}

.direction.down, .change.down {
  color: #67c23a !important;
  font-weight: bold;
}

.price, .confidence {
  font-size: 18px;
  font-weight: bold;
  color: #409EFF;
}

.current-price-value {
  font-size: 18px;
  font-weight: bold;
  color: #67c23a;
}

.prediction-date, .prediction-direction, .prediction-price, .prediction-change,
.prediction-confidence, .current-price {
  margin-bottom: 10px;
  font-size: 16px;
}
</style>