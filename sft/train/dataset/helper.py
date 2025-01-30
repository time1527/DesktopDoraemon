import re
import os
import json
import glob
import sys

sys.path.append("../..")
from utils.schema import PREFIX_PROMPT


def reformat_json(json_path, output_path):
    """
    partial conversation -> conversation
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    system_prompt = PREFIX_PROMPT

    def stripn(item: dict):
        new_content = item["content"].strip("\n")
        item["content"] = new_content
        return item

    new_data = []
    for d in data:
        new_item = []
        item = d["conversation"]
        for i, m in enumerate(item):
            # 第一个是用户的提问，直接添加
            if i == 0:
                new_q = system_prompt + m["content"].replace("Question: ", "").strip(
                    "\n"
                )
                m["content"] = new_q
                new_item.append(m)
                continue
            if i == 1:
                new_item.append(stripn(m))
                continue
            # 第三个是action/fa
            if m["role"] == new_item[-1]["role"]:
                new_item[-1]["content"] += "\n" + m["content"].strip("\n")

            else:
                new_item.append(stripn(m))

        new_data.append({"conversations": new_item})

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)


def remove_links(text):
    # 定义正则表达式，用于匹配链接
    url_pattern = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )

    # 使用sub方法将匹配到的链接替换为空字符串
    wourl_text = url_pattern.sub("", text)
    wourl_text = wourl_text.replace(" ", "")
    return wourl_text


def remove_path(text):
    if "上传了" not in text:
        return text
    return text.split("\n\n")[-1]


def detect_dev_in_train(dev_dir, train_dir):
    """
    检查eval数据是否在train数据出现过
    """
    dev_data = []
    train_data = []

    dev_paths = glob.glob(os.path.join(dev_dir, "*.json"))
    train_paths = glob.glob(os.path.join(train_dir, "*.json"))

    for f in dev_paths:
        with open(f, "r", encoding="utf-8") as f:
            dev_data.extend(json.load(f))

    for f in train_paths:
        with open(f, "r", encoding="utf-8") as f:
            train_data.extend(json.load(f))

    dev_q = [
        remove_links(remove_path(d["conversation"][0]["content"])) for d in dev_data
    ]

    train_q = [
        remove_links(remove_path(d["conversation"][0]["content"])) for d in train_data
    ]

    # print(train_q[10])

    intersection = list(set(dev_q) & set(train_q))
    assert len(intersection) == 0
    print(len(dev_q))
    print(len(train_q))


def merge_json(json_dir, output_path):
    """
    合并json文件
    """
    json_paths = glob.glob(os.path.join(json_dir, "*.json"))
    data = []
    for f in json_paths:
        with open(f, "r", encoding="utf-8") as f:
            data.extend(json.load(f))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    fs = glob.glob("partial_dataset/*.json")
    print(fs)
    for f in fs:
        input_path = f
        output_path = f.replace("partial_dataset", "msg_dataset")
        reformat_json(input_path, output_path)

    merge_json(
        "msg_dataset/",
        "train.json",
    )
