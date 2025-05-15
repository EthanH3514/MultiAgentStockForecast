<template>
  <div class="agent-result">
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="prediction-summary">
          <h3>预测摘要</h3>
          <div class="prediction-date">
            <span class="date-label">预测日期：</span>
            <span class="date">{{ predictionResult.target_date }}</span>
          </div>
          <div class="prediction-price">
            <span class="price-label">预测价格：</span>
            <span class="price">{{ predictionResult.predicted_price }}</span>
          </div>
          <div class="prediction-direction">
            <span class="direction-label">预测方向：</span>
            <span class="direction" :class="{'up': predictionResult.direction == 1, 'down': predictionResult.direction == -1}">
              {{ predictionResult.direction === 1 ? '看涨 ↑' : '看跌 ↓' }}
            </span>
          </div>
          <div class="prediction-change" v-if="predictionResult.change_rate !== undefined">
            <span class="change-label">预测涨跌幅：</span>
            <span class="change" :class="{'up': predictionResult.direction == 1, 'down': predictionResult.direction == -1}">
              {{ predictionResult.change_rate }}%
            </span>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  name: 'AgentPrediction',
  props: {
    predictionResult: {
      type: Object,
      required: true,
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

.direction-label, .price-label, .date-label, .change-label {
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

.price {
  font-size: 18px;
  font-weight: bold;
  color: #409EFF;
}

.prediction-date, .prediction-direction, .prediction-price, .prediction-change {
  margin-bottom: 10px;
  font-size: 16px;
}
</style>