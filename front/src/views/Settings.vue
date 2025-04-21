<template>
  <div class="settings-container">
    <h2>系统设置</h2>
    <div class="settings-form">
      <div class="form-group">
        <label for="apiKey">API Key</label>
        <input
          type="password"
          id="apiKey"
          v-model="apiKey"
          placeholder="请输入您的API Key"
        />
      </div>
      <div class="button-group">
        <button @click="saveSettings" :disabled="!apiKey">保存设置</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Settings',
  data() {
    return {
      apiKey: localStorage.getItem('arkApiKey') || '',
    };
  },
  methods: {
    saveSettings() {
      localStorage.setItem('arkApiKey', this.apiKey);
      this.$message.success('设置保存成功');
    },
  },
};
</script>

<style scoped>
.settings-container {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.settings-form {
  margin-top: 20px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: bold;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.button-group {
  text-align: right;
}

button {
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background-color: #45a049;
}
</style>