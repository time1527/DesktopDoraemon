import os
import sys
import shutil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.react import ReAct
from utils.schema import Message,ContentItem,MessageRole
from settings import REPO_PATH,DEFAULT_FUNCS,DEFAULT_QWEN_MAX_CFG,WORK_DIR


def test_react():
    agent = ReAct(llm=DEFAULT_QWEN_MAX_CFG,function_list=DEFAULT_FUNCS)

    messages = [Message(
        role=MessageRole.USER,
        content=[
            ContentItem(text = "帮我生成一张图片，大小1280*720，背景是红色的，内容是一只可爱的小猫。"),
            # ContentItem(image = os.path.join(REPO_PATH,
            #                                  "data/tools/image/rm-img-bg-test.jpg"))
            ])]
    *_, last = agent.run(messages)
    print(last)

if __name__ == '__main__':
    shutil.rmtree(WORK_DIR, ignore_errors=True)
    test_react()
