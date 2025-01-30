import os
import sys
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents import ReAct, DoraemonAgent
from utils.schema import Message, ContentItem, MessageRole
from settings import (
    REPO_PATH,
    DEFAULT_FUNCS,
    DEFAULT_DASHSCOPE_CFG,
    WORK_DIR,
    DEFAULT_MEMORY_CFG,
    DEFAULT_FT_CFG,
)


def test_react(config):
    agent = ReAct(
        llm=config,
        function_list=DEFAULT_FUNCS,
        memory=DEFAULT_MEMORY_CFG,
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content=[
                # # doraemonmemory
                ContentItem(text="哆啦美最近在做什么？"),
                # # githubtrending
                # ContentItem(text="今天github有什么热门的pytorch项目？"),
                # # imagegen
                # ContentItem(text="请帮我生成一个画面，飞机在海里飞行，要求宽是800。")
                # # removeimagebackground
                # ContentItem(
                #     text="（上传了![图片](G:/DesktopDoraemon/work_dir/1734165033-366666666.png)）\n\n感觉把这张的背景去掉会更好看一些。"
                # )
                # # todo
                # ContentItem(text="帮我看看今天还有什么任务？")
                # # treasurebag
                # ContentItem(text="哆啦A梦的百宝袋里面有什么东西？")
            ],
        )
    ]
    *_, last = agent.run(messages)
    print(last[0]["content"])


def test_doraemon(config):
    agent = DoraemonAgent(
        llm=config,
        function_list=DEFAULT_FUNCS,
        memory=DEFAULT_MEMORY_CFG,
    )
    messages = [
        Message(
            role=MessageRole.USER,
            content=[
                ContentItem(text="哆啦美今天干嘛去了"),
            ],
        )
    ]
    *_, last = agent.run(messages)
    print(last[0]["content"])


if __name__ == "__main__":
    # shutil.rmtree(WORK_DIR, ignore_errors=True)
    # test_doraemon()
    test_react(DEFAULT_FT_CFG)
