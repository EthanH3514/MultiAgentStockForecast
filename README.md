# 基于机器学习的股票涨跌预测系统

这是我的毕业设计，题目为基于机器学习的股票涨跌预测系统的设计与实现，系统能够使用智能代理和传统模型两种方式预测股票的涨跌情况。

### 智能代理预测流程图

智能代理预测模式会综合最近20天的股价数据、个股新闻、公司基本面、宏观经济四个方向的数据进行分析，给出下一日股价的涨跌预测。同时使用WebSocket在前端实时显示分析过程，并支持保存。

![代码流程图.drawio](https://github.com/EthanH3514/MultiAgentStockForecast/blob/master/pictures/%E4%BB%A3%E7%A0%81%E6%B5%81%E7%A8%8B%E5%9B%BE.drawio.png?raw=true)

### 系统用例图

![用例图](https://github.com/EthanH3514/MultiAgentStockForecast/blob/master/pictures/%E7%94%A8%E4%BE%8B%E5%9B%BE.png?raw=true)

## 系统结构

- `stock_prediction/`: 核心算法和模型
  - `agent/`: 智能代理模型
  - `traditional_model/`: 传统机器学习模型
  - `util/`: 工具函数
  - `data/`: 股票数据
  - `temp_data/`: 临时数据

- `front/`: 前端Vue应用
  - 提供用户界面，允许用户输入股票代码并选择预测方法
  - 可视化展示预测结果和分析过程

- `backend/`: 后端Flask应用
  - 提供API接口，连接前端和预测模型
  - 处理预测请求并返回结果

## 实验结果

以下是智能代理模型在小商品城（SH600415）2025年3月1日到2025年3月31日的股价上的实验结果，涨跌预测准确率有57.1%。

![智能代理实验结果](https://github.com/EthanH3514/MultiAgentStockForecast/blob/master/pictures/%E6%99%BA%E8%83%BD%E4%BB%A3%E7%90%86%E5%AE%9E%E9%AA%8C%E7%BB%93%E6%9E%9C.png?raw=true)



经过多次实验发现，预测波动率较大，大概率是因为时间跨度太小。爬取新闻数据使用的是Akshare的免费接口，只能获取最近100条个股新闻，时间上大约覆盖最近一个月。扩展新闻的话需要手写爬虫，不太想搞。

## 功能特点

1. 支持两种预测方法：
   - 智能代理预测：综合分析市场、新闻、基本面和宏观经济数据
   - 传统模型预测：使用机器学习模型预测股票价格

2. 可视化展示预测结果和分析过程

3. 使用最近20天的数据预测下一日股票涨跌

## 安装和运行

### 后端安装

```bash
cd backend
pip install -r requirements.txt
```

### 前端安装

```bash
cd front
npm install
```

### 启动系统

1. 启动后端服务

```bash
cd backend
python app.py
```

2. 启动前端服务

```bash
cd front
npm run serve
```

3. 访问系统

打开浏览器，访问 http://localhost:8080

## 使用方法

1. 在输入框中输入股票代码（如：600415）
2. 选择预测方法（智能代理预测或传统模型预测）
3. 点击"开始预测"按钮
4. 查看预测结果和分析过程

## 注意事项

- 确保系统已安装Python 3.8+和Node.js 14+
- 预测结果仅供参考，不构成投资建议
- 系统需要联网获取最新股票数据