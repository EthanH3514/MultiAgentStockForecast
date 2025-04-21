import os
from .agent import Agent
from stock_prediction.util.data_reader import get_stock_price_data
import time
from datetime import datetime
class MarketAnalysisAgent(Agent):
    def __init__(self, stock_code: str, data_path: str = None, api_key: str = None) -> None:
        super().__init__(api_key=api_key)

        self.agent_type = 'market'
        self.status_messages = ['正在进行市场分析...', '市场分析完成']

        self.stock_code = stock_code
        self.data_path = data_path

        # 定义系统提示词，用于指导模型进行市场分析
        system_prompt = """你是一个专业的股票市场分析师，擅长技术分析和市场预测。
        在分析时，请遵循以下原则：
        1. 综合分析历史价格走势、成交量和技术指标
        2. 考虑市场情绪和外部因素
        3. 给出具体的支撑位和压力位
        4. 提供风险提示和止损建议
        5. 使用专业术语，但确保解释清晰易懂
        
        在输出时，请按照以下格式组织内容：
        1. 市场现状概述
        2. 技术指标分析
        3. 支撑位和压力位
        4. 下一交易日收盘价预测
        5. 风险提示
        6. 操作建议
        """
        
        self.system_prompt = [
            {"role": "system", "content": system_prompt}
        ]

        # 定义市场分析提示词模板
        self.content_template = """请分析以下股票数据并给出预测：

        历史数据及技术指标：
        {price_data}

        请基于以上数据，给出详细的市场分析和预测。
        """
        
    def analyze_market(self, target_date: str = None, ws_server=None) -> tuple[str, str]:
        """
        分析市场数据并返回推理过程和预测结果
        :param target_date: 目标预测日期, 格式%Y%m%d, 如果为None则使用最新数据
        :return: (推理过程, 预测结果)
        """
        print(f'🔍 开始市场分析 {self.stock_code}')
        start_time = time.time()

        tmp_price_data=get_stock_price_data(stock_code=self.stock_code, target_date=target_date, data_path=self.data_path),
        
        if tmp_price_data is None or tmp_price_data == "":
            print("❌ 市场数据为空, 将不进行市场分析")
            return "", ""

        # 构建完整的提示词
        content = self.content_template.format(
            price_data=tmp_price_data
        )
        
        # 获取模型响应
        reasoning_content, content = self.ask_agent_streaming_output(content=content, messages=self.system_prompt, ws_server=ws_server)
        
        end_time = time.time()
        process_time = end_time - start_time
        print(f'⏰ 市场分析完成，耗时 {process_time: .2f}秒')

        # 保存输出
        if target_date is not None:
            self.save_output(f"{self.stock_code}市场分析_{str(target_date).replace(' ', '_').replace(':', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md")
        else:
            self.save_output()
        
        # 返回推理过程和预测结果
        return reasoning_content, content


if __name__ == '__main__':
    # 测试代码
    agent = MarketAnalysisAgent(stock_code='600415')
    
    # 获取分析结果
    reasoning, prediction = agent.analyze_market(target_date='20240101')
    