import os
import sys
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.react import ReAct
from utils.schema import Message, ContentItem, MessageRole
from settings import (
    REPO_PATH,
    DEFAULT_FUNCS,
    DEFAULT_QWEN_MAX_CFG,
    WORK_DIR,
    DEFAULT_MEMORY_CFG,
)


def test_react():
    agent = ReAct(
        llm=DEFAULT_QWEN_MAX_CFG, function_list=DEFAULT_FUNCS, memory=DEFAULT_MEMORY_CFG
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content=[
                ContentItem(text="今天github有什么热门的pytorch项目？"),
                # ContentItem(image = os.path.join(REPO_PATH,
                #                                  "data/tools/image/rm-img-bg-test.jpg"))
            ],
        )
    ]
    *_, last = agent.run(messages)
    print(last[0]["content"])


if __name__ == "__main__":
    # shutil.rmtree(WORK_DIR, ignore_errors=True)
    test_react()
