import os
from .agent import Agent
from stock_prediction.util.data_reader import read_specific_csv, read_stock_news_csv_by_date
import time
from datetime import datetime

class NewsAnalysisAgent(Agent):
    def __init__(self, stock_code: int, data_path: str = None, api_key: str = None) -> None:
        super().__init__(api_key=api_key)

        self.agent_type = 'news'
        self.status_messages = ['正在进行新闻分析...', '新闻分析完成']

        self.stock_code = stock_code
        self.data_path = data_path

        self.news_path = ('data' if self.data_path is None else self.data_path) + '/' + str(stock_code) + '/股票新闻数据.csv'
        self.stock_info_path = ('data' if self.data_path is None else self.data_path) + '/' + str(stock_code) + '/股票基本面数据/主营介绍.csv'

        # 定义系统提示词，用于指导模型进行新闻分析
        system_prompt = """你是一个专业的股票新闻分析师，擅长分析新闻对股票市场的影响。
        在分析时，请遵循以下原则：
        1. 识别新闻的关键信息和影响范围
        2. 评估新闻对相关股票的直接和间接影响
        3. 考虑新闻的时间敏感性和持续性
        4. 分析新闻对市场情绪的影响
        5. 结合行业背景和市场环境进行分析
        
        在输出时，请按照以下格式组织内容：
        1. 新闻要点概述
        2. 影响分析
           - 直接影响
           - 间接影响
           - 市场情绪影响
        3. 投资建议
           - 短期影响
           - 中长期影响
        4. 预测下一交易日收盘价
        5. 风险提示
        6. 操作建议
        """
        
        self.system_prompt = [
            {"role": "system", "content": system_prompt}
        ]

        # 定义新闻分析提示词模板
        self.content_template = """请分析以下股票相关新闻并给出投资建议：

        新闻内容：
        {news_content}
        
        相关股票信息：
        {stock_info}
        
        请基于以上信息，给出详细的分析和投资建议。

        生成一份分析报告
        """
        
    def analyze_news(self, target_date: str = None, ws_server=None) -> tuple[str, str]:
        """
        分析新闻数据并返回推理过程和投资建议
        :param target_date: 目标日期, 如果为None则使用最新数据
        :return: (推理过程, 投资建议)
        """
        print(f'🔍 开始新闻分析 {self.stock_code}')
        start_time = time.time()

        tmp_news_content=read_stock_news_csv_by_date(self.news_path, target_date=target_date),
        tmp_stock_info=read_specific_csv(self.stock_info_path)
        
        if tmp_news_content is None or tmp_news_content == "":
            print("❌ 新闻数据为空, 将不进行新闻分析")
            return "", ""
        
        # 构建完整的提示词
        content = self.content_template.format(
            news_content=tmp_news_content,
            stock_info=tmp_stock_info
        )
        
        # 实时推送推理过程
        reasoning_content, content = self.ask_agent_streaming_output(content=content, messages=self.system_prompt, ws_server=ws_server)
        
        end_time = time.time()
        process_time = end_time - start_time
        print(f'⏰ 新闻分析完成，耗时 {process_time: .2f}秒')

        # 保存输出
        if target_date is not None:
            self.save_output(f"{self.stock_code}新闻分析_{str(target_date).replace(' ', '_').replace(':', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md")
        else:
            self.save_output()

        # 返回推理过程和投资建议
        return reasoning_content, content

if __name__ == '__main__':
    # 测试代码
    agent = NewsAnalysisAgent(stock_code=600415)
    
    # 示例数据
    reasoning, prediction = agent.analyze_news(target_date='2025-03-01')
    
