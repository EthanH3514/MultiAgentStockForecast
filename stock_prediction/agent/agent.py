import os
from datetime import datetime
# 升级方舟 SDK 到最新版本 pip install -U 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark

class Agent:
    def __init__(self, api_key: str = None) -> None:
        # 自定义 deepseek-R1 接入点
        self.model = "ep-20250218214614-mhts7"
        self.timeout = 1800
        self.client = Ark(
            # 优先使用传入的API Key，如果未传入则从环境变量读取
            api_key = api_key or os.environ.get("ARK_API_KEY"),
            # 深度推理模型耗费时间会较长，请您设置较大的超时时间，避免超时，推荐30分钟以上
            timeout = self.timeout,
        )
        self.reasoning_content = ""
        self.content = ""
        self.log_file_path = "agent/suggestions"

    def ask_agent(self, content: str, messages = None):
        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages + [
                {"role": "user", "content": content}
            ]
        )
        return response

    def get_reasoning_content(self, response) -> str:
        # 当触发深度推理时，打印思维链内容
        if hasattr(response.choices[0].message, 'reasoning_content'):
            print(response.choices[0].message.reasoning_content)
            return response.choices[0].message.reasoning_content
        print("Error: 未触发深度推理, 返回None")
        return None

    def get_answer(self, response) -> str:
        return response.choices[0].message.content
    
    def ask_agent_streaming_output(self, content: str, messages = None, ws_server = None) -> tuple[str, str]:
        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages + [
                {"role": "user", "content": content}
            ],
            stream = True
        )
        if ws_server is None:
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                    self.reasoning_content += chunk.choices[0].delta.reasoning_content
                    print(chunk.choices[0].delta.reasoning_content, end="")
                else:
                    self.content += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end="")
            print("\n")
        else:
            for chunk in response:
                tmp_content = ""
                if hasattr(chunk.choices[0].delta,'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                    tmp_content = chunk.choices[0].delta.reasoning_content
                    # 实时推送推理过程                    
                    self.reasoning_content += tmp_content
                else:
                    tmp_content = chunk.choices[0].delta.content
                    self.content += tmp_content
                ws_server.emit_analysis_progress(self.agent_type, self.status_messages[0], tmp_content)
            # 结束推理
            ws_server.emit_analysis_progress(self.agent_type, self.status_messages[1])
        return self.reasoning_content, self.content
    
    def save_output(self, file_name: str = None):
        """
        保存输出内容到文件
        """
        # 获取当前类名
        derived_class_name = self.__class__.__name__
        if file_name is None:
            file_name = f"{derived_class_name}_{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.md"
        
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        file_path = os.path.join(root_dir, self.log_file_path, file_name)

        # 创建文件夹
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            if self.reasoning_content:
                f.write(self.reasoning_content)
            if self.content:
                f.write(self.content)


if __name__ == '__main__':
    agent = Agent()
    response = agent.ask_agent('你好呀')
    print(agent.get_reasoning_content(response))
    print(agent.get_answer(response))
