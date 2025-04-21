import os
from .agent import Agent
from stock_prediction.util.data_reader import get_stock_fundamentals_data
import time
from datetime import datetime

class FundamentalAnalysisAgent(Agent):
    def __init__(self, stock_code: str, data_path: str = None, api_key: str = None) -> None:
        super().__init__(api_key=api_key)

        self.agent_type = 'fundamental'
        self.status_messages = ['正在进行基本面分析...', '基本面分析完成']

        self.stock_code = stock_code
        self.data_path = data_path
        
        # 定义系统提示词，用于指导模型进行财务分析
        system_prompt = """你是一个专业的财务分析师，擅长分析公司财务报表和基本面。
        在分析时，请遵循以下原则：
        1. 全面分析财务报表的各个维度
        2. 关注关键财务指标的变化趋势
        3. 进行同行业对比分析
        4. 评估公司的经营效率和盈利能力
        5. 识别潜在的风险和机会
        
        在输出时，请按照以下格式组织内容：
        1. 公司概况
        2. 财务指标分析
        3. 同行业对比
        4. 风险评估
        5. 投资建议
        """
        
        self.system_prompt = [
            {"role": "system", "content": system_prompt}
        ]

        # 定义财务分析提示词模板
        self.content_template = """请分析以下公司财务数据并给出投资建议：
        
        {content}

        请基于以上信息，给出详细的分析和投资建议。
        生成一份完整的财务分析报告。
        """
        
    def analyze_fundamentals(self, target_date: str = None, ws_server=None) -> tuple[str, str]:
        """
        分析公司财务数据并返回推理过程和投资建议
        :param target_date: 目标日期, 格式%Y%m%d, 如果为None则使用最新数据
        :return: (推理过程, 投资建议)
        """
        print(f'🔍 开始基本面分析 {self.stock_code}')
        start_time = time.time()

        tmp_content = get_stock_fundamentals_data(stock_code=self.stock_code, target_date=target_date, data_path=self.data_path)
        if tmp_content is None or tmp_content == "":
            print("❌ 基本面数据为空, 将不进行基本面分析")
            return "", ""
        # 构建完整的提示词
        content = self.content_template.format(
            content=tmp_content
        )

        # print('content: ', content)

        reasoning_content, content = self.ask_agent_streaming_output(content=content, messages=self.system_prompt, ws_server=ws_server)
            
        end_time = time.time()
        process_time = end_time - start_time
        print(f'⏰ 基本面分析完成，耗时 {process_time: .2f}秒')

        # 保存输出
        if target_date is not None:
            self.save_output(f"{self.stock_code}基本面分析_{str(target_date).replace(' ', '_').replace(':', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md")
        else:
            self.save_output()

        # 返回推理过程和投资建议
        # return self.get_reasoning_content(response), self.get_answer(response)
        return reasoning_content, content

if __name__ == '__main__':
    # 测试代码
    agent = FundamentalAnalysisAgent(stock_code='600415')
    
    # 获取分析结果
    reasoning, prediction = agent.analyze_fundamentals(target_date='20250301')
