import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.schema import Message, ContentItem, MessageRole
from llms import get_chat_model
from settings import (
    REPO_PATH,
    DEFAULT_OLLAMA_CFG,
    DEFAULT_DASHSCOPE_CFG,
    DEFAULT_VLLM_CFG,
)

# 命令行:
# ollama serve
# ollama run qwen2.5:0.5b
# 或者
# vllm serve Qwen/Qwen2.5-3B-Instruct


functions = [
    {
        "name": "image_gen",
        "description": "AI绘画（图像生成）服务，输入文本描述和图像分辨率，返回根据文本信息绘制的图片URL。",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "详细描述了希望生成的图像具有什么内容，例如人物、环境、动作等细节描述，使用英文",
                },
            },
            "required": ["prompt"],
        },
    }
]


def test_llm(llm_cfg, fn=True):
    llm = get_chat_model(llm_cfg)
    messages = [
        Message(
            role=MessageRole.USER,
            content=[
                ContentItem(text="你好"),
                ContentItem(image=os.path.join(REPO_PATH, "assets/ui/chat/head1.jpg")),
            ],
        ),
    ]

    response = llm.chat(messages, functions=functions if fn else None, stream=True)
    response = list(response)[-1]
    print(response)


if __name__ == "__main__":
    test_llm(DEFAULT_DASHSCOPE_CFG)
