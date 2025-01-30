import os
import json
from fuzzywuzzy import process
from typing import Optional, Dict, Union

from tools.base import BaseTool, register_tool
from utils.utils import read_text_from_file, save_text_to_file
from settings import REPO_PATH
import random


@register_tool("ToDo")
class ToDo(BaseTool):
    description = "待办事项，输入操作及相应的待办事项，返回待办事项情况。"
    name = "ToDo"
    parameters: list = [
        {
            "name": "operation",
            "description": "操作，选项有[添加, 完成, 查看, 重置]。其中，添加表示添加待办事项，完成表示完成待办事项，查看表示查看所有待办事项，重置表示将待办事项清零。",
            "required": True,
            "type": "string",
        },
        {
            "name": "item",
            "description": "事项，添加时需要输入事项，完成时需要输入事项，查看时可以输入事项，重置时无需输入事项。",
            "required": False,
            "type": "string",
        },
    ]

    def __init__(self, cfg: Optional[Dict] = None, **kwargs):
        super().__init__(cfg)
        self.ops_map = {
            "添加": "insert",
            "完成": "finish",
            "查看": "check",
            "重置": "reset",
        }
        self.file = os.path.join(REPO_PATH, "assets/tools/content/todo_list.txt")
        # 如果不存在初始的todo文件，则创建一个空文件
        if not os.path.exists(self.file):
            save_text_to_file(self.file, "")
        self.list = read_text_from_file(self.file).split("\n")

    def call(self, params: Union[str, dict], **kwargs) -> str:
        """
        Call the ToDo tool.

        Args:
            params (Union[str, dict]): The input parameters.

        Returns:
            str: The output of the ToDo tool.
        """
        # 1. 检验参数格式
        try:
            params = self._verify_json_format_args(params)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

        # 2. 提取参数
        op = self.ops_map[params.get("operation", "查看").strip()]
        item = params.get("item", "")

        # 根据是模拟还是真实执行：
        simulate = kwargs.get("simulate", False)
        if simulate:
            return self.simulate_call(op, item)

        # 3. 执行操作
        res = ""
        error = False

        if op == "reset":
            self.list = []
            save_text_to_file(self.file, "")
            res = "重置待办事项成功。"

        elif op == "check":
            if item.strip():
                match = self.match_list(item)
                if match:
                    res = f"{item} 在待办事项中。"
                else:
                    res = (
                        f"{item} 不在待办事项中。当前待办事项有："
                        + self.todo_text
                        + "。"
                    )
            else:
                res = "当前待办事项有：" + self.todo_text + "。"

        elif op == "insert":
            if not item.strip():
                res = "添加的待办事项不能为空。"
                error = True
            elif self.match_list(item):
                res = f"{item} 已经在待办事项中。"
            else:
                self.list.append(item.strip())
                res = "添加待办事项成功，当前待办事项有：" + self.todo_text + "。"
                save_text_to_file(self.file, "\n".join(self.list))

        elif op == "finish":
            if not item.strip():
                res = "完成的待办事项不能为空。"
                error = True
            else:
                # 模糊匹配
                match = self.match_list(item)
                if match:
                    self.list.remove(match)
                res = (
                    f"恭喜你完成 {item.strip()}，剩余待办事项有："
                    + self.todo_text
                    + "。"
                )
                save_text_to_file(self.file, "\n".join(self.list))

        if error:
            return json.dumps({"error": res}, ensure_ascii=False)
        return json.dumps({"text": res}, ensure_ascii=False)

    def match_list(self, item: str) -> str:
        """
        Match the item with the list.

        Args:
            item (str): The item to be matched.

        Returns:
            str: The matched item.
        """
        if not self.list:
            return ""
        match, score = process.extractOne(item.strip(), self.list)
        if score > 80:  # 超参数
            return match
        else:
            return ""

    @property
    def todo_text(self) -> str:
        """
        List the text.
        Returns:
            str: The list of text.
        """
        self.list = [i for i in self.list if i.strip()]
        return "[" + "；".join(self.list) + "]"

    def simulate_call(self, op: str, item: str) -> str:
        """
        Simulate the call.
        Args:
            op (str): The operation.
            item (str): The item.
        Returns:
            str: The simulated result.
        Notice: Cannot be used in multi-turns cause of the randomness.
        """

        def rdn_text(sout: str = "", sin: str = ""):
            """
            Args:
                sout (str): str must out of list.
                sin (str): str must in list.
            Returns:
                str: The simulated list.
            """
            all_todo = self.list.copy()
            n = random.randint(1, min(4, len(all_todo)))
            rt = list(set([random.choice(all_todo) for _ in range(n)]))

            if sout:
                match, score = process.extractOne(sout, rt)
                if score > 80:
                    rt.remove(match)
            if sin:
                if rt:
                    match, score = process.extractOne(sin, rt)
                    if score > 80:
                        rt.remove(match)
                rt.append(sin)
            return "[" + "；".join(rt) + "]"

        res = ""
        error = False

        if op == "reset":
            res = "重置待办事项成功。"

        elif op == "check":
            if item.strip():
                rdn1 = random.random()
                if rdn1 < 0.8:
                    res = f"{item} 在待办事项中。"
                else:
                    res = (
                        f"{item} 不在待办事项中。当前待办事项有："
                        + rdn_text(sout=item.strip())
                        + "。"
                    )
            else:
                res = "当前待办事项有：" + rdn_text() + "。"

        elif op == "insert":
            if not item.strip():
                res = "添加的待办事项不能为空。"
                error = True
            else:
                rdn2 = random.random()
                if rdn2 < 0.3:
                    res = f"{item} 已经在待办事项中。"
                else:
                    res = (
                        "添加待办事项成功，当前待办事项有："
                        + rdn_text(sin=item.strip())
                        + "。"
                    )

        elif op == "finish":
            if not item.strip():
                res = "完成的待办事项不能为空。"
                error = True
            else:
                res = (
                    f"恭喜你完成 {item.strip()}，剩余待办事项有："
                    + rdn_text(sout=item.strip())
                    + "。"
                )

        if error:
            return json.dumps({"error": res}, ensure_ascii=False)
        return json.dumps({"text": res}, ensure_ascii=False)
