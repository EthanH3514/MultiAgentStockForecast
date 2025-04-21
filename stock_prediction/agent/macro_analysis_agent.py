import os
from .agent import Agent
from stock_prediction.util.data_reader import get_latest_data_from_directory
import time
from datetime import datetime


class MacroAnalysisAgent(Agent):
    def __init__(self, data_path: str = None, api_key: str = None) -> None:
        super().__init__(api_key=api_key)

        self.agent_type = 'macro'
        self.status_messages = ['正在进行宏观经济分析...', '宏观经济分析完成']

        self.data_path = data_path

        system_prompt = """你是一位专业的宏观经济分析师，擅长分析中国的宏观经济数据。
        你的分析需要全面、客观，并能够从数据中提取关键信息，形成有价值的投资建议。
        请保持专业、客观的分析态度，避免过度主观判断。"""

        self.system_prompt = [
            {"role": "system", "content": system_prompt}
        ]

    def analyze_macro_data(self, target_date: str = None, ws_server=None) -> tuple[str, str]:
        """
        分析中国宏观经济数据并生成报告
        :param target_date: 目标日期, 格式%Y%m%d, 如果为None则使用最新数据
        :return: (推理过程, 投资建议)
        """
        print(f'🔍 开始宏观经济分析')
        start_time = time.time()

        macro_data_path = ('data' if self.data_path is None else self.data_path) + '/宏观数据/中国宏观数据'
        macro_data = get_latest_data_from_directory(macro_data_path)

        print('macro_data: ', macro_data)
        if macro_data is None or macro_data == "":
            print("❌ 宏观数据为空, 将不进行宏观分析")
            return "", ""

        content_template = f"""请基于以下中国宏观经济数据进行分析：

        {macro_data}

        请确保分析全面、客观，并给出具体的投资建议。"""

        reasoning_content, content = self.ask_agent_streaming_output(content=content_template, messages=self.system_prompt, ws_server=ws_server)  
        
        end_time = time.time()
        process_time = end_time - start_time
        print(f'⏰ 宏观分析完成，耗时 {process_time:.2f}秒')

        # 保存输出
        if target_date is not None:
            self.save_output(f"宏观分析_{str(target_date).replace(' ', '_').replace(':', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md")
        else:
            self.save_output()

        return reasoning_content, content

if __name__ == "__main__":
    # 测试代码
    data_path = "tmp_data"
    agent = MacroAnalysisAgent(data_path=data_path)
    
    # 示例数据
    reasoning, prediction = agent.analyze_macro_data(target_date='20250331')
    print(reasoning)
    print(prediction)
