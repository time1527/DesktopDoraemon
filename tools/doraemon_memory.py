import json
from typing import Union

from memory.base import BaseMemory
from tools.base import BaseTool, register_tool
from settings import DEFAULT_MEMORY_CFG


@register_tool("DoraemonMemory")
class DoraemonMemory(BaseTool):
    description = "查询关于哆啦A梦、大雄、静香、小夫、胖虎、哆啦美的相关问题。输入相关问题，返回回答。"
    name = "DoraemonMemory"
    parameters: list = [
        {
            "name": "query",
            "description": "关于哆啦A梦、大雄、静香、小夫、胖虎、哆啦美的问题，问题是关于基本信息、人际关系、性格、优点、缺点、喜恶、能力、外观等。",
            "required": True,
            "type": "string",
        }
    ]

    def call(self, params: Union[str, dict], **kwargs) -> str:
        """
        Call the tool with the given parameters.

        Args:
            params (Union[str, dict]): The parameters to use for the tool.

        Returns:
            str: The output of the tool.
        """
        # 1. 检查参数格式
        try:
            params = self._verify_json_format_args(params)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

        # 2. 检查参数
        query = params.get("query")
        if not query:
            return json.dumps(
                {"error": "query is required."},
                ensure_ascii=False,
            )

        mem = kwargs.get("memory")
        if not mem or mem is None:
            mem = BaseMemory(DEFAULT_MEMORY_CFG)

        # 3. 调用知识库
        try:
            results = mem.query(query, num_return=3)
            text_results = "\n".join(results)
            if results:
                return json.dumps(
                    {"text": f"在哆啦A梦的记忆里：{text_results}"},
                    ensure_ascii=False,
                )
            else:
                return json.dumps(
                    {"text": f"在哆啦A梦的记忆里：我不知道“{query}”。"},
                    ensure_ascii=False,
                )
        except Exception as e:
            return json.dumps(
                {"error": str(e)},
                ensure_ascii=False,
            )
