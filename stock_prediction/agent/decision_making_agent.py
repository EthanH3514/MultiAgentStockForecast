import os
from .market_analysis_agent import MarketAnalysisAgent
from .news_analysis_agent import NewsAnalysisAgent
from .fundamental_analysis_agent import FundamentalAnalysisAgent
from .agent import Agent
from .macro_analysis_agent import MacroAnalysisAgent
import time
from datetime import datetime

class DecisionMakingAgent(Agent):
    def __init__(self, stock_code: str, data_path: str = None, api_key: str = None) -> None:
        """
        data_path:
            
        """
        super().__init__(api_key=api_key)

        self.agent_type = 'decision'
        self.status_messages = ['开始决策分析...', '决策分析完成']
        
        self.stock_code = stock_code
        self.data_path = data_path
        
        self.market_analysis_agent = MarketAnalysisAgent(stock_code=self.stock_code, data_path=self.data_path, api_key=api_key)
        self.news_analysis_agent = NewsAnalysisAgent(stock_code=self.stock_code, data_path=self.data_path, api_key=api_key)
        self.fundamental_analysis_agent = FundamentalAnalysisAgent(stock_code=self.stock_code, data_path=self.data_path, api_key=api_key)
        self.macro_analysis_agent = MacroAnalysisAgent(data_path=self.data_path, api_key=api_key)

        self.agent_name = '决策制定代理'

    def make_decision(self, target_date: str = None, ws_server=None) -> tuple[str, str]:
        """
        做出投资决策
        :param target_date: 目标日期, 格式%Y%m%d, 如果为None则使用最新数据
        :param ws_server: WebSocket服务器实例，用于实时推送分析进度
        :return: (推理过程, 决策建议)
        """
        start_time = time.time()
        
        market_analysis_result = self.market_analysis_agent.analyze_market(target_date=target_date, ws_server=ws_server)
        news_analysis_result = self.news_analysis_agent.analyze_news(target_date=target_date, ws_server=ws_server)
        fundamentals_analysis_result = self.fundamental_analysis_agent.analyze_fundamentals(target_date=target_date, ws_server=ws_server)
        macro_analysis_result = self.macro_analysis_agent.analyze_macro_data(target_date=target_date, ws_server=ws_server)

        # 综合分析结果
        print('🔍 开始综合分析结果')
        reasoning, decision = self.generate_decision_suggestion(
            market_analysis_result, 
            news_analysis_result, 
            fundamentals_analysis_result, 
            macro_analysis_result,
            target_date,
            ws_server=ws_server
        )
        print('✅ 综合分析结果获取完成')
        
        end_time = time.time()
        total_time = end_time - start_time
        print(f'⏰ 所有分析完成，总耗时 {total_time:.2f}秒')
        
        return reasoning, decision
    
    def generate_decision_suggestion(self, market_analysis_result: tuple[str, str], news_analysis_result: tuple[str, str], fundamentals_analysis_result: tuple[str, str], macro_analysis_result: tuple[str, str], target_date: str = None, ws_server = None) -> tuple[str, str]:
        """
        根据三个分析结果生成最终决策建议
        :param market_analysis_result: 市场分析结果
        :param news_analysis_result: 新闻分析结果
        :param fundamentals_analysis_result: 基本面分析结果
        :param macro_analysis_result: 宏观分析结果
        :return: (思考过程, 决策建议)
        """
        start_time = time.time()

        # 构建系统提示词
        system_prompt = """你是一个短线交易员，擅长综合各类分析结果做出对下一日股价的涨跌预测。
        在分析时，请遵循以下原则：
        1. 综合考虑技术面、消息面和基本面三个维度
        2. 评估各个维度的权重和可信度
        3. 识别关键影响因素
        4. 给出大致的价格预测
        """
        
        # 构建分析提示词
        content = f"""
        市场技术分析报告：
        {market_analysis_result[1]}
        
        新闻消息分析报告：
        {news_analysis_result[1]}
        
        基本面分析报告：
        {fundamentals_analysis_result[1]}

        宏观经济分析报告：
        {macro_analysis_result[1]}

        输出时，请只按照如下格式组织内容：
        第一部分为看涨或看跌
        第二部分为价格预测
        不需要分析过程
        你的涨跌预测非常重要，请认真对待

        例如：
        看跌 25.98
        """
        
        # 获取模型响应
        reasoning_content, content = self.ask_agent_streaming_output(content=content, messages=[{"role": "system", "content": system_prompt}], ws_server=ws_server)
        
        end_time = time.time()
        process_time = end_time - start_time
        print(f'⏰ 决策分析完成，耗时 {process_time:.2f}秒')
        
        # 保存输出
        if target_date is not None:
            self.save_output(f"{self.stock_code}决策分析_{str(target_date).replace(' ', '_').replace(':', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md")
        else:
            self.save_output()

        # 返回思考过程和决策建议
        return reasoning_content, content


if __name__ == '__main__':
    # 测试代码
    agent = DecisionMakingAgent(stock_code='600415')
    
    # 获取决策建议
    reasoning, decision = agent.make_decision(target_date='2025-03-31')
    
    print("思考过程：")
    print(reasoning)
    print("\n决策建议：")
    print(decision)
    
