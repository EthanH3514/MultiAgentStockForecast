from flask import Flask, request, jsonify, send_from_directory
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from flask_cors import CORS
from websocket_server import WebSocketServer

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入预测模块
from stock_prediction.predict_by_agent import predict_by_agent, get_format_predict_result_by_agent, get_format_result_from_content
from stock_prediction.fetch_stock_data import fetch_stock_data

app = Flask(__name__)
CORS(app)  # 启用CORS支持跨域请求
ws_server = WebSocketServer(app)  # 初始化WebSocket服务器

@app.route('/')
def index():
    return jsonify({"message": "股票预测系统API服务已启动"})

@app.route('/api/test/predict/agent', methods=['POST'])
def test_predict_stock_by_agent():
    """测试使用代理模型预测股票"""
    stock_code = request.args.get('stock_code')
    api_key = request.args.get('api_key')

    # 获取当前日期和时间
    now = datetime.now()
    current_hour = now.hour
    
    # 如果当前时间在15点之后，预测下一个交易日，否则预测当日
    target_date = now.strftime("%Y%m%d")
    if current_hour >= 15:
        target_date = (now + timedelta(days=1)).strftime("%Y%m%d")
    
    # 计算20天前的日期作为开始日期
    start_date = (datetime.now() - timedelta(days=20)).strftime("%Y%m%d")

    try:
        result = jsonify({
            "success": True,
            "data": {
                "stock_code": stock_code,
                "target_date": target_date,
                "reasoning": '测试思考过程',
                "decision": '测试思考结果',
                "direction": -1,
                "predicted_price": 13.00,
            }
        })
        print('result:', result)
        return result
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/predict/agent', methods=['POST'])
def predict_stock_by_agent():
    """使用代理模型预测股票"""
    data = request.json
    stock_code = data.get('stock_code')
    api_key = data.get('api_key')
    
    start_date = "20100101"
    end_date = datetime.now().strftime("%Y%m%d")
    
    # 拉取股票相关数据
    fetch_stock_data(stock_code, start_date, end_date, ws_server)
    
    if not stock_code:
        return jsonify({"error": "请提供股票代码"}), 400
    
    # 获取当前日期和时间
    now = datetime.now()
    current_hour = now.hour
    
    # 如果当前时间在15点之后，预测下一个交易日，否则预测当日
    target_date = now.strftime("%Y%m%d")
    if current_hour >= 15:
        target_date = (now + timedelta(days=1)).strftime("%Y%m%d")
    
    # 计算20天前的日期作为开始日期
    start_date = (datetime.now() - timedelta(days=20)).strftime("%Y%m%d")
    
    try:
        # 获取预测结果，传入WebSocket服务器实例
        reasoning, decision = predict_by_agent(stock_code, start_date, target_date, ws_server, api_key)
        
        # 获取格式化的预测结果
        direction, predicted_price = get_format_result_from_content(reasoning, decision)
        
        return jsonify({
            "success": True,
            "data": {
                "stock_code": stock_code,
                "target_date": target_date,
                "reasoning": reasoning,
                "decision": decision,
                "direction": direction,
                "predicted_price": predicted_price,
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取项目根目录的绝对路径
def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.route('/api/predict/traditional', methods=['POST'])
def predict_stock_traditional():
    """使用传统模型预测股票"""
    data = request.json
    method = data.get('method')
    stock_code = data.get('stock_code')
    
    if not stock_code:
        return jsonify({"error": "请提供股票代码"}), 400
    
    if method not in ['LSTM', 'SVM', 'Transformer']:
        return jsonify({"error": "无效的预测方法"}), 400

    try:
        # 获取项目根目录
        root_dir = get_project_root()
        
        # 构建数据路径
        data_path = os.path.join(root_dir, "stock_prediction", "data", stock_code, "股票日线数据.csv")
        if method == 'LSTM':
            model_path = os.path.join(root_dir, "stock_prediction", "traditional_model", method, "best_model.h5")
            scaler_path = os.path.join(root_dir, "stock_prediction", "traditional_model", method, "scaler.npy")
            
            from stock_prediction.traditional_model.LSTM.predict import predict_next_day
            
            # 预测下一天股价
            result = predict_next_day(model_path, data_path, scaler_path)
        elif method == 'SVM':
            model_path = os.path.join(root_dir, "stock_prediction", "traditional_model", method, "best_model.pkl")
            scaler_path = os.path.join(root_dir, "stock_prediction", "traditional_model", method, "scaler.npy")

            from stock_prediction.traditional_model.SVM.predict import predict_next_day

            # 预测下一天股价
            result = predict_next_day(model_path, data_path, scaler_path)
        elif method == 'Transformer':
            model_path = os.path.join(root_dir, "stock_prediction", "traditional_model", method, "best_model.pt")
            scaler_path = os.path.join(root_dir, "stock_prediction", "traditional_model", method, "scaler.pt")

            from stock_prediction.traditional_model.transformer.predict import predict_next_day

            # 预测下一天股价
            result = predict_next_day(model_path, data_path, scaler_path)

        # 提取预测结果
        prediction_date = result['日期'].iloc[0].strftime("%Y-%m-%d")
        predicted_price = float(result['预测收盘价'].iloc[0]) if '预测收盘价' in result else float(result['当前价格'].iloc[0])
        
        response_data = {
            "stock_code": stock_code,
            "prediction_date": prediction_date,
            "predicted_price": predicted_price,
        }
        
        # 根据不同模型添加特定的返回数据
        if method == 'LSTM':
            response_data.update({
                "predicted_price": float(result['预测收盘价'].iloc[0]),
                "direction": int(result['涨跌方向'].iloc[0]),
                "change_rate": float(result['涨跌幅'].iloc[0])
            })
        elif method == 'SVM':
            response_data.update({
                "direction": int(result['涨跌方向'].iloc[0]),
                "confidence": float(result['预测概率'].iloc[0]),
                "current_price": float(result['当前价格'].iloc[0])
            })
        elif method == 'Transformer':
            response_data.update({
                "predicted_price": float(result['predicted_price']),
                "direction": int(result['direction']),
                "change_rate": float(result['change_rate'])
            })
        
        return jsonify({
            "success": True,
            "data": response_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/stock/historical/<stock_code>', methods=['GET'])
def get_historical_data(stock_code):
    """获取股票历史数据"""
    try:
        # 获取项目根目录
        root_dir = get_project_root()
        
        # 构建数据路径
        data_path = os.path.join(root_dir, "stock_prediction", "data", stock_code, "股票日线数据.csv")
        
        # 检查文件是否存在
        if not os.path.exists(data_path):
            # 如果文件不存在，尝试获取数据
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            end_date = datetime.now().strftime("%Y%m%d")
            fetch_stock_data(stock_code, start_date, end_date, ws_server)
            
            # 再次检查文件是否存在
            if not os.path.exists(data_path):
                return jsonify({"error": "无法获取股票历史数据"}), 404
        
        # 读取CSV文件
        df = pd.read_csv(data_path)
        
        # 只返回最近20天的数据
        df = df.tail(20)
        
        # 转换为JSON格式
        result = []
        for _, row in df.iterrows():
            result.append({
                "date": row["日期"],
                "open": float(row["开盘"]),
                "close": float(row["收盘"]),
                "low": float(row["最低"]),
                "high": float(row["最高"]),
            })
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    ws_server.run(app, debug=True, host='0.0.0.0', port=5000)