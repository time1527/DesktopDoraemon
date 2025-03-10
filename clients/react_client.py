import sys
from typing import Optional
from PyQt5.QtWidgets import QApplication

from agents import ReAct
from clients.base import BaseClient
from utils.schema import ContentItem
from utils.utils import (
    is_image,
    is_file,
    json_loads,
    extract_final_answer,
    extract_observation,
)
from log import logger
from settings import DEFAULT_REACT_LLM_CFG, DEFAULT_FUNCS, DEFAULT_MEMORY_CFG


class ReActClient(BaseClient):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)

    def init_model(self, agent: Optional[ReAct] = None):
        self.agent = agent or ReAct(
            function_list=DEFAULT_FUNCS,
            llm=DEFAULT_REACT_LLM_CFG,
            memory=DEFAULT_MEMORY_CFG,
        )
        self.agent.system_prompt = (
            "你在扮演哆啦A梦，请按照其人物特征以第一人称进行对话。"
        )

    def generate(self):
        *_, output = self.agent.run(self.history)
        output = output[-1]

        logger.info(f"agent output: {output}")

        # 提取observation 和 final answer
        ob = extract_observation(output.content)  # str -> str
        fa = extract_final_answer(output.content)  # str -> str

        # 没有调用tool
        if not ob:
            if fa:
                output.content = [ContentItem(text=fa)]
            return output, ""

        # 提取action
        try:
            _, action, _, _ = self.agent._detect_tool(output.content)
            # 从observation提取image和file路径
            paths = json_loads(ob)  # str -> dict or str(error)
            if (
                not paths
                or isinstance(paths, str)
                or all(x == "text" for x in paths.keys())
            ):
                output.content = [ContentItem(text=fa)]
                return output, action

            # 将image和file路径添加到content中
            content = [ContentItem(text=fa)]
            for type in paths.keys():
                type = type.strip()
                if type == "image":
                    content.append(ContentItem(image=paths[type]))
                elif type == "file":
                    content.append(ContentItem(file=paths[type]))
            output.content = content
            return output, action
        except Exception as e:
            logger.error(f"extract error: {e}")
            return output, ""


if __name__ == "__main__":
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
