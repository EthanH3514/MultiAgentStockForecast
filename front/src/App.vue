<template>
  <div class="app-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>基于机器学习的股票涨跌预测系统</h1>
          <div class="nav-menu">
            <router-link to="/" class="nav-link">股票预测</router-link>
            <router-link to="/settings" class="nav-link">系统设置</router-link>
          </div>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
      <el-footer>
        <div class="footer-content">
          <p>© 2025 股票预测系统 - 毕业设计</p>
        </div>
      </el-footer>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'App',
};
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

#app {
  height: 100%;
}

.app-container {
  height: 100%;
}

.el-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.el-header {
  background-color: #409EFF;
  color: white;
  line-height: 60px;
  text-align: center;
  padding: 0 20px;
}

.el-main {
  flex: 1;
  padding: 20px;
  background-color: #f5f7fa;
}

.el-footer {
  background-color: #545c64;
  color: #eee;
  text-align: center;
  line-height: 60px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
}

.nav-menu {
  display: flex;
  gap: 20px;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.footer-content p {
  margin: 0;
  font-size: 14px;
}
</style>