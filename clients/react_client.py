import sys
from typing import Optional
from PyQt5.QtWidgets import QApplication

from agents import ReAct
from clients.base import BaseClient
from utils.schema import ContentItem
from utils.utils import is_image,is_file,extract_markdown_urls,extract_final_answer
from log import logger
from settings import DEFAULT_REACT_LLM_CFG,DEFAULT_FUNCS,DEFAULT_MEMORY_CFG


class ReActClient(BaseClient):
    def __init__(self, 
                 parent=None, 
                 **kwargs):
        super().__init__(parent)

    def init_model(self,agent: Optional[ReAct] = None):
        self.agent = agent or ReAct(
            function_list=DEFAULT_FUNCS,
            llm=DEFAULT_REACT_LLM_CFG,
            memory=DEFAULT_MEMORY_CFG)
        self.agent.system_prompt = "你在扮演哆啦A梦，请按照其人物特征以第一人称进行对话。"


    def generate(self):
        *_,output = self.agent.run(self.history)
        output = output[-1]

        logger.info(f"agent output: {output}")
        # 提取final answer和url
        fa = extract_final_answer(output.content) # str -> str
        urls = extract_markdown_urls(fa) # str -> list[str]
        if len(urls) == 0:
            output.content = [ContentItem(text = fa)]
            return output
        
        # 将url添加到content中
        content = [ContentItem(text = fa)]
        for url in urls:
            if is_image(url):
                content.append(ContentItem(image = url))
            elif is_file(url):
                content.append(ContentItem(file = url))
        output.content = content
        logger.info(f"agent output: {output}")
        return output


if __name__ == '__main__':
    app = QApplication(sys.argv)

    client = ReActClient()
    client.msg_show_frame.update()
    client.msg_show_frame.verticalScrollBar().setValue(200)
    client.show()
    client.msg_show_frame.verticalScrollBar().setValue(200)
    # 1. 进入时间循环；
    # 2. wait，直到响应app可能的输入；
    # 3. QT接收和处理用户及系统交代的事件（消息），并传递到各个窗口；
    # 4. 程序遇到exit()退出时，机会返回exec()的值。
    sys.exit(app.exec_())
