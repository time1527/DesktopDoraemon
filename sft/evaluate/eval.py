import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
import time
import random
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from pprint import pprint
from tqdm import trange
from agents import DoraemonAgent
from llms import QwenChatAtDS, get_chat_model, BaseChatModel
from utils.schema import (
    Message,
    MessageRole,
    ContentItem,
    REACT_OBS_TOKEN,
    REACT_TOOL_TOKEN,
    REACT_ARGS_TOKEN,
    PREFIX_PROMPT,
)
from utils.utils import json_loads
from log import logger
from settings import (
    DEFAULT_FUNCS,
    DEFAULT_OLLAMA_CFG,
    DEFAULT_DASHSCOPE_CFG,
    REPO_PATH,
    DEFAULT_VLLM_CFG,
    DEFAULT_FT_CFG,
)

# notice: 要测试的函数在DEFAULT_FUNCS里必须有
tool_token = REACT_TOOL_TOKEN.strip("\n")
args_token = REACT_ARGS_TOKEN.strip("\n")
obs_token = REACT_OBS_TOKEN.strip("\n")


def detect_thought(text: str):
    thought, fa = None, None
    i = text.rfind("Thought:")
    j = text.rfind("\nFinal Answer:")
    if 0 <= i < j:
        thought = text[i + len("Thought:") : j].strip()
        fa = text[j + len("\nFinal Answer:") :].strip()
    return (thought is not None and fa is not None), thought, fa


def calculate_res(true_dev, pred_dev):
    with open(true_dev, "r", encoding="utf-8") as f:
        dev_data = json.load(f)

    with open(pred_dev, "r", encoding="utf-8") as f:
        pred_data = json.load(f)

    tool_cnt = Counter()
    # 错误类型
    error_map = {"action": 0, "action input": 1, "json format": 2, "obs in fa": 3}
    tool_map = {k: v for v, k in enumerate(DEFAULT_FUNCS)}
    res = np.zeros((len(tool_map), len(error_map)))

    error_list = [[] for _ in range(len(pred_data))]

    for i in range(len(dev_data)):
        d = dev_data[i]["conversation"]
        true_tool = d[1]["content"][len("Action:") :].strip()
        true_args = json_loads(d[2]["content"][len("Action Input:") :].strip())
        tool_cnt[true_tool] += 1

        pred_con = pred_data[i]
        call_res = dict()
        for msg in pred_con[::-1]:
            if msg["role"] == "assistant" and "Final Answer" in msg["content"]:
                call_res["fa"] = msg["content"]
            elif msg["role"] == "user" and obs_token in msg["content"]:
                call_res["ob"] = msg["content"][len(obs_token) :].strip()
            elif msg["role"] == "assistant" and args_token in msg["content"]:
                call_res["args"] = msg["content"][len(args_token) :].strip()
            elif msg["role"] == "assistant" and tool_token in msg["content"]:
                call_res["action"] = msg["content"][len(tool_token) :].strip()
            if all([k in call_res.keys() for k in ["fa", "ob", "action", "args"]]):
                break
        if not all([k in call_res.keys() for k in ["fa", "ob", "action", "args"]]):
            for e in range(res.shape[1]):
                res[tool_map[true_tool]][e] += 1
            error_list[i] = ["all"]
            continue

        # action
        if call_res["action"] != true_tool:
            error_list[i].append("action")
            res[tool_map[true_tool]][error_map["action"]] += 1
            # continue

        # json
        try:
            call_args = json_loads(call_res["args"])
        except:
            error_list[i].append("json format")
            res[tool_map[true_tool]][error_map["json format"]] += 1
            # continue

        # action input
        tool_key_map = {
            "ImageGen": ["prompt"],
            "RemoveImageBackground": ["img_path"],
            "GithubTrending": ["date_range"],
            "ToDo": ["operation"],
            "TreasureBag": ["tool"],
            "DoraemonMemory": ["query"],
        }
        try:
            call_args = json_loads(call_res["args"])
            if not all(k in call_args.keys() for k in tool_key_map[true_tool]):
                error_list[i].append("action input")
                res[tool_map[true_tool]][error_map["action input"]] += 1
            else:
                # imagegen
                call_args.pop("prompt", None)
                true_args.pop("prompt", None)

                if true_tool == "DoraemonMemory":
                    # 要注意的是：人物出现在query里
                    character = dev_data[i]["character"]
                    if not all(
                        person in call_args.get("query") for person in character
                    ):
                        error_list[i].append("action input")
                        res[tool_map[true_tool]][error_map["action input"]] += 1
                elif true_tool == "ImageGen":
                    # 要注意的是：图片大小
                    w_true = true_args.get("width", 1024)
                    w_pred = call_args.get("width", 1024)

                    h_true = true_args.get("height", 1024)
                    h_pred = call_args.get("height", 1024)

                    if w_pred != w_true or h_pred != h_true:
                        error_list[i].append("action input")
                        res[tool_map[true_tool]][error_map["action input"]] += 1
                elif true_tool == "RemoveImageBackground":
                    # 要注意的是：图片路径
                    if call_args.get("img_path") != true_args.get("img_path"):
                        error_list[i].append("action input")
                        res[tool_map[true_tool]][error_map["action input"]] += 1
                elif true_tool == "GithubTrending":
                    # 要注意的是：语言可能为空
                    if (
                        call_args.get("language", "").lower()
                        != true_args.get("language", "").lower()
                    ):
                        error_list[i].append("action input")
                        res[tool_map[true_tool]][error_map["action input"]] += 1
                elif true_tool == "ToDo":
                    # 要注意的是：item可能不一样
                    if call_args.get("operation", "") != true_args.get("operation", ""):
                        error_list[i].append("action input")
                        res[tool_map[true_tool]][error_map["action input"]] += 1
                    elif not ("item" in call_args) == ("item" in true_args):
                        error_list[i].append("action input")
                        res[tool_map[true_tool]][error_map["action input"]] += 1

                elif call_args != true_args:
                    error_list[i].append("action input")
                    res[tool_map[true_tool]][error_map["action input"]] += 1
        except:
            error_list[i].append("action input")
            res[tool_map[true_tool]][error_map["action input"]] += 1

        # obs -> fa
        if true_tool == "ImageGen" or true_tool == "RemoveImageBackground":
            try:
                ob = json_loads(call_res["ob"])
                if "image" in ob and ob["image"] not in call_res["fa"]:
                    error_list[i].append("obs in fa")
                    res[tool_map[true_tool]][error_map["obs in fa"]] += 1
            except:
                error_list[i].append("obs in fa")
                res[tool_map[true_tool]][error_map["obs in fa"]] += 1

    false_conv = [
        {",".join(error_list[i]): pred_data[i]}
        for i in range(len(pred_data))
        if len(error_list[i])
    ]

    save_name = ".".join(os.path.basename(pred_dev).split(".")[:-1])
    save_dir = save_name[: -len("_res")]
    np.save(f"{save_dir}/{save_name}.npy", res)
    with open(f"{save_dir}/{save_name}_false.json", "w", encoding="utf-8") as f:
        json.dump(false_conv, f, ensure_ascii=False, indent=4)

    row_labels = DEFAULT_FUNCS
    col_labels = list(error_map.keys())

    plt.figure(figsize=(10, 8))
    plt.matshow(res, fignum=0, cmap="viridis")

    plt.xticks(range(len(col_labels)), col_labels, rotation=45, fontsize=10)
    plt.yticks(range(len(row_labels)), row_labels, fontsize=10)

    # print(tool_cnt)
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            plt.text(
                j,
                i,
                f"{100*res[i, j] / tool_cnt[row_labels[i]]:.2f}%",
                ha="center",
                va="center",
                color="black",
            )
    plt.savefig(f"{save_dir}/{save_name}.png", dpi=400)


def eval_agents(dev_path: str, llm: BaseChatModel, eval_name: str = ""):
    # dev 数据
    with open(dev_path, "r", encoding="utf-8") as f:
        dev_data = json.load(f)

    prefix = PREFIX_PROMPT

    save_conv = []
    for i in trange(len(dev_data)):
        # 实例化agent
        agent = DoraemonAgent(function_list=DEFAULT_FUNCS, llm=llm)
        agent.system_prompt = ""

        time.sleep(1)

        d = dev_data[i]["conversation"]
        p = d[0]["content"].strip()

        conversation = []  # 用于保存，便于检查
        messages = []  # 用于llm对话

        conversation.append({"role": "user", "content": p})
        messages.append(Message(role="user", content=f"{prefix + p}"))

        # 拆写 react：
        # thought/action/action input: assistant
        # observation: user
        num_llm_calls_available = 5

        while num_llm_calls_available > 0:
            num_llm_calls_available -= 1

            output = agent._call_llm(messages=messages, stream=False)
            has_action, action, action_input, thought = agent._detect_tool(
                output[-1].content
            )
            # print(output)
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

            observation = agent._call_tool(action, action_input)

            messages.append({"role": "user", "content": f"{obs_token} {observation}"})
            conversation.append(
                {
                    "role": "user",
                    "content": f"{obs_token} {observation}",
                }
            )
        # print(messages)
        save_conv.append(conversation)

    os.mkdir(eval_name)
    save_name = eval_name + "_res" if eval_name else "res"

    with open(f"{eval_name}/{save_name}.json", "w", encoding="utf-8") as f:
        json.dump(save_conv, f, ensure_ascii=False, indent=4)
    calculate_res(
        true_dev=dev_path,
        pred_dev=f"{eval_name}/{save_name}.json",
    )


if __name__ == "__main__":
    # eval_agents(
    #     dev_path="dataset/dev.json",
    #     llm=DEFAULT_DASHSCOPE_CFG,
    #     eval_name=DEFAULT_DASHSCOPE_CFG.get("model").split("/")[-1].lower(),
    # )
    eval_agents(
        dev_path="dataset/dev.json",
        llm=DEFAULT_FT_CFG,
        eval_name=DEFAULT_FT_CFG.get("model").split("/")[-1].lower(),
    )
