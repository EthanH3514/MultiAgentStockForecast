<template>
  <div class="stock-prediction-container">
    <el-card class="input-card">
      <template #header>
        <div class="card-header">
          <h2>股票预测</h2>
        </div>
      </template>
      <el-form :model="form" label-width="120px">
        <el-form-item label="股票代码">
          <el-input v-model="form.stockCode" placeholder="请输入股票代码，如：600415"></el-input>
        </el-form-item>
        <el-form-item label="预测方法">
          <el-radio-group v-model="form.predictionMethod">
            <el-radio label="agent">智能代理预测</el-radio>
            <el-radio label="traditional">传统模型预测</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="submitForm" :loading="loading">开始预测</el-button>
          <el-button type="success" @click="downloadAnalysis" :disabled="!predictionResult || form.predictionMethod !== 'agent'">下载分析报告</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 历史股价数据图表 -->
    <el-card v-if="historicalData.length > 0" class="chart-card">
      <template #header>
        <div class="card-header">
          <h2>历史二十天股价走势</h2>
        </div>
      </template>
      <div class="chart-container" ref="stockChartRef"></div>
    </el-card>

    <div class="result-container">
      <el-card v-if="form.predictionMethod === 'agent'" class="analysis-card">
        <template #header>
          <div class="card-header">
            <h2>分析进度</h2>
          </div>
        </template>
        <AnalysisProgress ref="analysisProgress" />
      </el-card>
      
      <el-card v-if="predictionResult" class="result-card">
        <template #header>
          <div class="card-header">
            <h2>预测结果</h2>
          </div>
        </template>
        
        <!-- 智能代理预测结果 -->
        <div v-if="form.predictionMethod === 'agent'" class="agent-result">
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
        
        <!-- 传统模型预测结果 -->
        <div v-else class="traditional-result">
          <el-row>
            <el-col :span="24">
              <div class="prediction-summary">
                <h3>预测摘要</h3>
                <div class="prediction-date">
                  <span class="date-label">预测日期：</span>
                  <span class="date">{{ predictionResult.prediction_date }}</span>
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
      </el-card>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import AnalysisProgress from '@/components/AnalysisProgress.vue';
import JSZip from 'jszip';
import * as echarts from 'echarts';

export default {
  name: 'StockPrediction',
  components: {
    AnalysisProgress,
  },
  data() {
    return {
      form: {
        stockCode: '',
        predictionMethod: 'agent',
      },
      loading: false,
      predictionResult: null,
      decisionAnalysisStatus: { inProgress: false, message: '', reasoning: '' },
      targetDate: '',
      historicalData: [],
      stockChart: null,
    };
  },
  methods: {
    async submitForm() {
      if (!this.form.stockCode) {
        this.$message.error('请输入股票代码');
        return;
      }
      this.targetDate = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      
      if (this.form.predictionMethod === 'agent' && this.$refs.analysisProgress) {
        this.$refs.analysisProgress.resetStatus();
      }
      
      this.loading = true;
      try {
        // 获取历史股价数据
        await this.fetchHistoricalData();
        
        let endpoint = 'http://localhost:5000/api/predict/traditional';
        if (this.form.predictionMethod === 'agent') {
          endpoint = 'http://localhost:5000/api/predict/agent';
        }
        
        const response = await axios.post(endpoint, {
          stock_code: this.form.stockCode,
          api_key: localStorage.getItem('arkApiKey'),
        });
        
        if (response.data.success) {
          this.predictionResult = response.data.data;
          console.log('预测结果:', this.predictionResult);
          // 保留两位小数
          this.predictionResult.predicted_price = parseFloat(this.predictionResult.predicted_price).toFixed(2);
          console.log('预测价格:', this.predictionResult.predicted_price);
          const lastDayClosePrice = parseFloat(this.historicalData[this.historicalData.length - 1].close);
          this.predictionResult.change_rate = parseFloat((this.predictionResult.predicted_price - lastDayClosePrice) / lastDayClosePrice * 100).toFixed(2);
          if (!this.predictionResult.direction) {
            this.predictionResult.direction = this.predictionResult.change_rate > 0 ? 1 : -1;
          }
          this.$message.success('预测完成');
        } else {
          this.$message.error(response.data.error || '预测失败');
        }
      } catch (error) {
        console.error('预测请求错误:', error);
        this.$message.error('预测请求失败: ' + (error.response?.data?.error || error.message));
      } finally {
        this.loading = false;
      }
    },
    async fetchHistoricalData() {
      try {
        const response = await axios.get(`http://localhost:5000/api/stock/historical/${this.form.stockCode}`);
        if (response.data && response.data.success) {
          this.historicalData = response.data.data;
          this.$nextTick(() => {
            this.initStockChart();
          });
        } else {
          console.error('获取历史数据失败:', response.data.error);
          this.$message.warning('获取历史股价数据失败');
        }
      } catch (error) {
        console.error('获取历史数据请求错误:', error);
      }
    },
    initStockChart() {
      if (this.stockChart) {
        this.stockChart.dispose();
      }
      
      const chartDom = this.$refs.stockChartRef;
      if (!chartDom) return;
      
      this.stockChart = echarts.init(chartDom);
      
      const dates = this.historicalData.map(item => item.date);
      const data = this.historicalData.map(item => [
        parseFloat(item.open),
        parseFloat(item.close),
        parseFloat(item.low),
        parseFloat(item.high),
      ]);
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
          },
          formatter: function (params) {
            const data = params[0].data;
            return `日期: ${params[0].axisValue}<br/>
                   开盘价: ${data[0]}<br/>
                   收盘价: ${data[1]}<br/>
                   最低价: ${data[2]}<br/>
                   最高价: ${data[3]}<br/>`;
          },
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '10%',
          containLabel: true,
        },
        xAxis: {
          type: 'category',
          data: dates,
          scale: true,
          boundaryGap: true,
          axisLine: { lineStyle: { color: '#8392A5' } },
          axisLabel: {
            rotate: 30,
            formatter: value => value.substring(5), // 只显示月-日
          },
          min: 'dataMin',
          max: 'dataMax',
        },
        yAxis: {
          scale: true,
          splitArea: {
            show: true,
          },
        },
        series: [{
          name: '股价',
          type: 'candlestick',
          data: data,
          itemStyle: {
            color: '#f56c6c',
            color0: '#67c23a',
            borderColor: '#f56c6c',
            borderColor0: '#67c23a',
          },
          sampling: 'none',
        }],
      };
      
      this.stockChart.setOption(option);
    },
    
    handleResize() {
      if (!this.stockChart || this.stockChart.isDisposed()) return;

      const container = this.$refs.chartContainer;
      if (!container || container.offsetWidth === 0) return;
      
      setTimeout(() => {
        try{
          this.stockChart.resize();
        } catch (error) {
          console.log('Resize failed:', error);
        }
      }, 100);
    },
    
    async downloadAnalysis() {
      try {
        const zip = new JSZip();
        const agentTypes = ['market', 'news', 'fundamental', 'macro', 'decision'];
        
        // 从前端已有的分析结果中提取数据
        for (const agentType of agentTypes) {
          const analysisData = this.$refs.analysisProgress.getAgentAnalysis(agentType);
          if (analysisData) {
            const content = `分析时间: ${new Date().toLocaleString()}
            
            ${analysisData}`;
            zip.file(`${this.form.stockCode}_${agentType}_analysis_${this.targetDate}.txt`, content);
          }
        }

        // 生成并下载zip文件
        const content = await zip.generateAsync({type: 'blob'});
        const url = window.URL.createObjectURL(content);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${this.form.stockCode}_analysis_reports_${this.targetDate}.zip`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        this.$message.success('分析报告下载成功');
      } catch (error) {
        console.error('下载分析报告失败:', error);
        this.$message.error('下载分析报告失败');
      }
    },
  },
  mounted() {
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
    if (this.stockChart) {
      this.stockChart.dispose();
      this.stockChart = null;
    }
  },
};
</script>

<style scoped>
.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 400px;
  width: 100%;
}

.stock-prediction-container {
  max-width: 1200px;
  margin: 0 auto;
}

.input-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-container {
  margin-top: 30px;
}

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

.reasoning-container {
  margin-top: 20px;
}

.reasoning-container h3 {
  margin-bottom: 15px;
  color: #303133;
}

.reasoning-content {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  max-height: 500px;
  overflow-y: auto;
}

.reasoning-content pre {
  white-space: pre-wrap;
  font-family: 'Courier New', Courier, monospace;
  line-height: 1.5;
}

.prediction-date, .prediction-direction, .prediction-price, .prediction-change {
  margin-bottom: 10px;
  font-size: 16px;
}
</style>