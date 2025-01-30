import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
import time
import random
from pprint import pprint
from tqdm import trange
from agents import DoraemonAgent, ReAct
from tools import TOOL_REGISTRY, BaseTool
from llms import QwenChatAtDS, get_chat_model, BaseChatModel
from utils.schema import (
    Message,
    MessageRole,
    REACT_OBS_TOKEN,
    REACT_TOOL_TOKEN,
    REACT_ARGS_TOKEN,
)
from utils.utils import read_text_from_file
from log import logger
from settings import DEFAULT_FUNCS, DEFAULT_OLLAMA_CFG, DEFAULT_DASHSCOPE_CFG, REPO_PATH


file_dir = os.path.dirname(os.path.abspath(__file__))


def write_json_file(file_path, data):
    dir = os.path.dirname(file_path)
    os.makedirs(dir, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def detect_thought(text: str):
    thought, fa = None, None
    i = text.rfind("Thought:")
    j = text.rfind("\nFinal Answer:")
    if 0 <= i < j:
        thought = text[i + len("Thought:") : j].strip()
        fa = text[j + len("\nFinal Answer:") :].strip()
    return (thought is not None and fa is not None), thought, fa


def gen_one_round(tool: str, llm: BaseChatModel):
    name = tool.lower()

    few_shot = read_text_from_file(os.path.join(file_dir, f"prompts/{name}.txt"))
    prompts = read_text_from_file(
        os.path.join(file_dir, f"user_input/{name}.txt")
    ).split("\n")

    prompts = list(set(prompts))
    random.shuffle(prompts)

    one_round = []
    more_round = []

    for i in trange(len(prompts)):
        agent = ReAct(function_list=[tool], llm=llm)
        agent.system_prompt = few_shot

        time.sleep(1)
        p = prompts[i].strip()
        if p == "":
            continue

        # 处理 removeimagebackground 工具的特殊情况
        if name == "removeimagebackground" and "上传了" in p:
            p = p.replace("%%%%%%%%%%", "\n\n")

        conversation = []  # 用于保存，便于检查
        messages = []  # 用于llm对话

        conversation.append({"role": "user", "content": p})
        messages.append({"role": "user", "content": f"Question: {p}"})

        # 拆写 react：
        # thought/action/action input: assistant
        # observation: user
        num_llm_calls_available = 5
        use_tool = False

        while num_llm_calls_available > 0:
            num_llm_calls_available -= 1

            output = agent._call_llm(messages=messages, stream=False)
            has_action, action, action_input, thought = agent._detect_tool(
                output[-1].content
            )

            if has_action:
                use_tool = True
            if not has_action:
                has_thought, thought, fa = detect_thought(output[-1].content)
                if not has_thought:
                    logger.info("no thought,wait for another round")
                    continue
                messages.append(
                    {
                        "role": "assistant",
                        "content": f"Thought: {thought}\nFinal Answer: {fa}",
                    }
                )

                conversation.append(
                    {
                        "role": "assistant",
                        "content": f"Thought: {thought}",
                    }
                )
                conversation.append(
                    {
                        "role": "assistant",
                        "content": f"Final Answer: {fa}",
                    }
                )
                # pprint(conversation)
                break

            messages.append(
                {
                    "role": "assistant",
                    "content": thought
                    + f"{REACT_TOOL_TOKEN} {action}{REACT_ARGS_TOKEN} {action_input}",
                }
            )

            tool_token = REACT_TOOL_TOKEN.strip("\n")
            args_token = REACT_ARGS_TOKEN.strip("\n")
            conversation.append(
                {
                    "role": "assistant",
                    "content": f"{thought}",
                }
            )
            conversation.append(
                {
                    "role": "assistant",
                    "content": f"{tool_token} {action}",
                }
            )
            conversation.append(
                {
                    "role": "assistant",
                    "content": f"{args_token} {action_input}",
                }
            )

            observation = agent._call_tool(action, action_input, **{"simulate": True})
            obs_token = REACT_OBS_TOKEN.strip("\n")
            messages.append({"role": "user", "content": f"{obs_token} {observation}"})
            conversation.append(
                {
                    "role": "user",
                    "content": f"{obs_token} {observation}",
                }
            )

        # pprint(conversation)
        if use_tool:
            one_round.append({"conversation": conversation})
        else:
            more_round.append({"conversation": conversation})

        # 将 one_round 和 more_round 列表写入到 JSON 文件中
        write_json_file(f"one_round/{name}_progress.json", one_round)
        write_json_file(f"more_round/{name}_progress.json", more_round)

    # 将最终的 one_round 和 more_round 列表写入到 JSON 文件中
    write_json_file(f"one_round/{name}.json", one_round)
    write_json_file(f"more_round/{name}.json", more_round)


if __name__ == "__main__":
    llm = QwenChatAtDS(cfg={"model": "qwen-turbo"})
    for t in DEFAULT_FUNCS:
        gen_one_round(t, llm)
