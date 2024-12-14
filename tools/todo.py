import os
import json
from fuzzywuzzy import process
from typing import Optional, Dict, Union

from tools.base import BaseTool, register_tool
from utils.utils import read_text_from_file, save_text_to_file
from settings import REPO_PATH


@register_tool("TODO")
class TODO(BaseTool):
    description = "待办事项，输入操作及相应的待办事项，返回所有待办事项。"
    name = "TODO"
    parameters: list = [
        {
            "name": "operation",
            "description": "操作，选项有[添加, 完成, 查看, 重置]。其中，添加表示添加待办事项，完成表示完成待办事项，查看表示查看所有待办事项，重置表示将待办事项清零。",
            "required": True,
            "type": "string",
        },
        {
            "name": "item",
            "description": "事项，添加时输入事项，完成时输入事项，查看时无需输入，重置时无需输入。",
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
        self.file = os.path.join(REPO_PATH, "data/tools/content/todo_list.txt")
        self.list = read_text_from_file(self.file).split("\n")

    def call(self, params: Union[str, dict], **kwargs) -> dict:
        """
        Call the TODO tool.

        Args:
            params (Union[str, dict]): The input parameters.

        Returns:
                dict: The output of the TODO tool.
        """
        # 1. 检验参数是否符合要求
        params = self._verify_json_format_args(params)
        op = self.ops_map[params.get("operation", "查看").strip()]
        item = params.get("item", "")

        # 2. 执行操作
        res = ""
        if op == "reset":
            self.list = []
            save_text_to_file(self.file, "")
            res = "重置待办事项成功！"
        elif op == "check":
            if len(self.list) == 0:
                res = "当前无待办事项！"
            else:
                res = "当前待办事项有：\n" + "\n".join(self.list)
        elif op == "insert":
            if item.strip() == "":
                res = "待办事项不能为空！"
            else:
                self.list.append(item.strip())
                save_text_to_file(self.file, "\n".join(self.list))
                res = "添加待办事项成功！当前待办事项有：\n" + "\n".join(self.list)
        elif op == "finish":
            if item.strip() == "":
                res = "待办事项不能为空！"
            else:
                # 模糊匹配
                match = process.extract(item.strip(), self.list, limit=1)
                self.list.remove(match[0][0])
                save_text_to_file(self.file, "\n".join(self.list))
                res = f"完成 {item.strip()}！当前待办事项有：\n" + "\n".join(self.list)

        return json.dumps({"text": res}, ensure_ascii=False)
