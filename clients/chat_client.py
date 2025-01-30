import sys
from typing import Optional
from PyQt5.QtWidgets import QApplication

from agents.base import ChatAgent
from clients.base import BaseClient
from utils.utils import extract_final_answer
from log import logger
from settings import DEFAULT_CHAT_LLM_CFG


class ChatClient(BaseClient):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)

    def init_model(
        self,
        agent: Optional[ChatAgent] = None,
    ):
        self.agent = agent or ChatAgent(llm=DEFAULT_CHAT_LLM_CFG)
        self.agent.system_prompt = (
            "你在扮演哆啦A梦，请按照其人物特征以第一人称进行对话。"
        )

    def generate(self):
        *_, output = self.agent.run(self.history)
        output = extract_final_answer(output[-1])
        logger.info(f"agent output: {output}")
        return output, ""


if __name__ == "__main__":
    app = QApplication(sys.argv)

    client = ChatClient()
    client.msg_show_frame.update()
    client.msg_show_frame.verticalScrollBar().setValue(200)
    client.show()
    client.msg_show_frame.verticalScrollBar().setValue(200)

    sys.exit(app.exec_())
