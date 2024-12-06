from typing import Union

from memory.base import BaseMemory
from tools.base import BaseTool,register_tool
from settings import DEFAULT_MEMORY_CFG

@register_tool('AboutFriends')
class AboutFriends(BaseTool):
    description = "查询关于哆啦A梦及大雄、静香、小夫、胖虎、哆啦美的相关问题。输入人物相关问题，返回回答。"
    name = 'AboutFriends'
    parameters: list = [
        {
            'name': 'query',
            'description': '关于哆啦A梦或大雄或静香或小夫或胖虎或哆啦美的问题。',
            'required': True,
            'type':'string',
        }
    ]

    def call(self, params: Union[str, dict], **kwargs) -> dict:
        """
        Call the tool with the given parameters.

        Args:
            params (Union[str, dict]): The parameters to use for the tool.

        Returns:
            dict: The output of the tool.
        """
        params = self._verify_json_format_args(params)
        query = params.get('query')

        mem = kwargs.get("memory",BaseMemory(DEFAULT_MEMORY_CFG))
        results = mem.vector_store.as_retriever(search_kwargs={'k': 3}).invoke(query)
        return dict(type = "text",content = "\n\n".join([result.page_content for result in results]))