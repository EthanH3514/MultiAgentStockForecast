import stock_prediction.agent.decision_making_agent as decision_making_agent
from stock_prediction.util.data_api import process_all_csvs_in_directory
import time
from datetime import timedelta, datetime
import os

def predict_by_agent(stock_code: str, start_date: str, target_date: str, ws_server=None, api_key: str = None) -> tuple[str, str]:
    """
    使用决策制定代理预测股票价格
    :param stock_code: 股票代码
    :param start_date: 数据开始日期(包含)
    :param target_date: 目标预测日期
    :param ws_server: WebSocket服务器实例
    :return: 决策建议 [reasoning: str, decision: str]
    """
    # 获取项目根目录
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 截取日期范围内的数据
    data_path = os.path.join(root_dir, "stock_prediction", "data")
    temp_data_path = os.path.join(root_dir, "stock_prediction", "temp_data")

    # 目标日期的前一天，因为目标日期的股价是未知的，所以不能使用目标日期的数据
    end_date = (datetime.strptime(target_date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")

    process_all_csvs_in_directory(data_path, temp_data_path, start_date, end_date)
    print("🔍 数据处理完成")

    # 创建决策制定代理
    decision_maker = decision_making_agent.DecisionMakingAgent(stock_code, data_path=temp_data_path, api_key=api_key)
    
    # 获取决策建议
    reasoning, decision = decision_maker.make_decision(target_date=target_date, ws_server=ws_server)

    # 返回决策建议
    return reasoning, decision


def get_format_predict_result_by_agent(stock_code: str, start_date: str, target_date: str) -> tuple[int, float]:
    """
    获取格式化后的决策建议
    :param stock_code: 股票代码
    :param start_date: 数据开始日期(包含)
    :param target_date: 目标预测日期
    :return: 格式化后的决策建议 [direction: 1/-1, price: float]
    """
    reasoning, decision = predict_by_agent(stock_code, start_date, target_date)
    predict_direction, predict_price = decision.strip().split(" ")
    
    predict_direction = 1 if predict_direction == "看涨" else -1
    predict_price = float(predict_price)

    return predict_direction, predict_price


def get_format_result_from_content(reasoning: str, decision: str) -> tuple[int, float]:
    """
    从内容中获取格式化后的决策建议
    :param reasoning: 推理过程
    :param decision: 决策
    :return: 格式化后的决策建议 [direction: 1/-1, price: float]
    """
    predict_direction, predict_price = decision.strip().split(" ")

    predict_direction = 1 if predict_direction == "看涨" else -1
    predict_price = float(predict_price)

    return predict_direction, predict_price
    

if __name__ == "__main__":
    stock_code = "600415"
    start_date = "20250201"
    target_date = "20250410"
    print(get_format_predict_result_by_agent(stock_code, start_date, target_date))

