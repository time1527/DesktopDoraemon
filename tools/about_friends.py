import json
from typing import Union

from memory.base import BaseMemory
from tools.base import BaseTool, register_tool
from settings import DEFAULT_MEMORY_CFG


@register_tool("AboutFriends")
class AboutFriends(BaseTool):
    description = (
        "查询关于大雄、静香、小夫、胖虎、哆啦美的相关问题。输入人物相关问题，返回回答。"
    )
    name = "AboutFriends"
    parameters: list = [
        {
            "name": "query",
            "description": "关于大雄或静香或小夫或胖虎或哆啦美的问题，问题是关于基本信息、人际关系、性格、优点、缺点、喜恶、能力、外观等。",
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
        params = self._verify_json_format_args(params)
        query = params.get("query")

        mem = kwargs.get("memory")
        if not mem or mem is None:
            mem = BaseMemory(DEFAULT_MEMORY_CFG)
        results = mem.vector_store.as_retriever(search_kwargs={"k": 3}).invoke(query)
        return json.dumps(
            {"text": "\n\n".join([result.page_content for result in results])},
            ensure_ascii=False,
        )
