<template>
  <div class="analysis-progress">
    <div class="progress-item" v-for="(status, type) in analysisStatus" :key="type">
      <div class="agent-type">{{ getAgentTitle(type) }}</div>
      <div class="status" :class="{ 'in-progress': status.inProgress }">
        {{ status.message || '等待进行...' }}
      </div>
      <div v-if="status.reasoning" class="reasoning">
        <pre>{{ status.reasoning }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import { io } from 'socket.io-client';

export default {
  name: 'AnalysisProgress',
  data() {
    return {
      socket: null,
      analysisStatus: {
        data_preparation: { inProgress: false, message: '', reasoning: '' },
        market: { inProgress: false, message: '', reasoning: '' },
        news: { inProgress: false, message: '', reasoning: '' },
        fundamental: { inProgress: false, message: '', reasoning: '' },
        macro: { inProgress: false, message: '', reasoning: '' },
        decision: { inProgress: false, message: '', reasoning: '' },
      },
      analysisResults: {
        market: '',
        news: '',
        fundamental: '',
        macro: '',
        decision: '',
      },
    };
  },
  methods: {
    getAgentTitle(type) {
      const titles = {
        data_preparation: '数据准备',
        market: '市场分析',
        news: '新闻分析',
        fundamental: '基本面分析',
        macro: '宏观经济分析',
        decision: '决策分析',
      };
      return titles[type] || type;
    },
    setupWebSocket() {
      this.socket = io('http://localhost:5000');
      
      this.socket.on('connect', () => {
        console.log('WebSocket connected');
      });

      this.socket.on('analysis_progress', (data) => {
        const { agent_type, message, reasoning } = data;
        if (this.analysisStatus[agent_type]) {
          this.analysisStatus[agent_type].inProgress = true;
          this.analysisStatus[agent_type].message = message;
          if (reasoning) {
            // 追加推理内容而不是替换，以实现实时更新效果
            if (this.analysisStatus[agent_type].reasoning) {
              this.analysisStatus[agent_type].reasoning += reasoning;
            } else {
              this.analysisStatus[agent_type].reasoning = reasoning;
            }
            // 更新分析结果
            if (Object.prototype.hasOwnProperty.call(this.analysisResults, agent_type)) {
              this.analysisResults[agent_type] = this.analysisStatus[agent_type].reasoning;
            }
          }
        }
      });
    },
    resetStatus() {
      Object.keys(this.analysisStatus).forEach(type => {
        this.analysisStatus[type].inProgress = false;
        this.analysisStatus[type].message = '';
        this.analysisStatus[type].reasoning = '';
      });
      Object.keys(this.analysisResults).forEach(type => {
        this.analysisResults[type] = '';
      });
    },
    getAgentAnalysis(agentType) {
      return this.analysisResults[agentType] || '';
    },
  },
  mounted() {
    this.setupWebSocket();
  },
  beforeUnmount() {
    if (this.socket) {
      this.socket.disconnect();
    }
  },
};
</script>

<style scoped>
.analysis-progress {
  margin: 20px;
  padding: 15px;
  border-radius: 8px;
  background-color: #f5f5f5;
}

.progress-item {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 4px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.agent-type {
  font-weight: bold;
  margin-bottom: 5px;
  color: #333;
}

.status {
  color: #666;
  font-size: 0.9em;
}

.status.in-progress {
  color: #2196F3;
}

.reasoning {
  margin-top: 10px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
  font-size: 0.9em;
  white-space: pre-wrap;
  overflow-x: auto;
}
</style>