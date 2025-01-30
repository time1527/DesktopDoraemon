# copy and modify from:
# https://github.com/QwenLM/Qwen-Agent/blob/main/qwen_agent/agent.py

import copy
import json
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Iterator, List, Optional, Union, Tuple

from llms import BaseChatModel, get_chat_model
from memory.base import BaseMemory
from tools.base import BaseTool, TOOL_REGISTRY
from utils.schema import (
    MessageRole,
    Message,
    ContentItem,
    DEFAULT_SYSTEM_PROMPT,
    ROLE,
    CONTENT,
)
from utils.utils import merge_generate_cfgs, has_chinese_messages
from log import logger
from settings import MEMORY_TOOL_NAME


class BaseAgent(ABC):
    """
    A base class for Agent.

    An agent can receive messages and provide response by LLM or Tools.
    Different agents have distinct workflows for processing messages and generating responses in the `_run` method.
    """

    def __init__(
        self,
        function_list: Optional[List[Union[str, Dict, BaseTool]]] = None,
        llm: Optional[Union[dict, BaseChatModel]] = None,
        memory: Optional[Union[dict, BaseMemory]] = None,
        system_prompt: Optional[str] = DEFAULT_SYSTEM_PROMPT,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialization the agent.

        Args:
            function_list: One list of tool name, tool configuration or Tool object,
              such as 'code_interpreter', {'name': 'code_interpreter', 'timeout': 10}, or CodeInterpreter().
            llm: The LLM model configuration or LLM model object.
              Set the configuration as {'model': '', 'api_key': '', 'model_server': ''}.
            memory: The memory object.
            system_prompt: The specified system prompt for LLM chat.
            name: The name of this agent.
            description: The description of this agent, which will be used for multi_agent.
        """
        # llm
        if isinstance(llm, dict):
            self.llm = get_chat_model(llm)
        else:
            self.llm = llm
        self.extra_generate_cfg: dict = {}

        # function
        self.function_map = {}
        if function_list:
            for tool in function_list:
                self._init_tool(tool)

        # memory
        if MEMORY_TOOL_NAME not in self.function_map.keys():
            self.memory = None
        else:
            if isinstance(memory, dict):
                self.memory = BaseMemory(memory)
            else:
                self.memory = memory

        # 其他
        self.system_prompt = system_prompt
        self.name = name
        self.description = description

    def run_nonstream(
        self, messages: List[Union[Dict, Message]], **kwargs
    ) -> Union[List[Message], List[Dict]]:
        """Same as self.run, but with stream=False,
        meaning it returns the complete response directly
        instead of streaming the response incrementally."""
        *_, last_responses = self.run(messages, **kwargs)
        return last_responses

    def run(
        self, messages: List[Union[Dict, Message]], **kwargs
    ) -> Union[Iterator[List[Message]], Iterator[List[Dict]]]:
        """
        Return one response generator based on the received messages.

        This method performs a uniform type conversion for the inputted messages,
        and calls the _run method to generate a reply.

        Args:
            messages: A list of messages.

        Yields:
            The response generator.
        """
        # 1. messages整理成List[Message]
        messages = copy.deepcopy(messages)
        _return_message_type = "dict"
        new_messages = []
        # Only return dict when all input messages are dict
        if not messages:
            _return_message_type = "message"
        for msg in messages:
            if isinstance(msg, dict):
                new_messages.append(Message(**msg))
            else:
                new_messages.append(msg)
                _return_message_type = "message"

        # 2. 确认kwargs['lang']
        if "lang" not in kwargs:
            if has_chinese_messages(new_messages):
                kwargs["lang"] = "zh"
            else:
                kwargs["lang"] = "en"

        # 3. 调用self._run()
        for rsp in self._run(messages=new_messages, **kwargs):
            for i in range(len(rsp)):
                if not rsp[i].name and self.name:
                    rsp[i].name = self.name
            if _return_message_type == "message":
                yield [Message(**x) if isinstance(x, dict) else x for x in rsp]
            else:
                yield [x.model_dump() if not isinstance(x, dict) else x for x in rsp]

    @abstractmethod
    def _run(
        self, messages: List[Message], lang: str = "en", **kwargs
    ) -> Iterator[List[Message]]:
        """
        Return one response generator based on the received messages.

        The workflow for an agent to generate a reply.
        Each agent subclass needs to implement this method.

        Args:
            messages: A list of messages.
            lang: Language, which will be used to select the language of the prompt
              during the agent's execution process.

        Yields:
            The response generator.
        """
        raise NotImplementedError

    def _call_llm(
        self,
        messages: List[Message],
        functions: Optional[List[Dict]] = None,
        stream: bool = True,
        extra_generate_cfg: Optional[dict] = None,
    ) -> Iterator[List[Message]]:
        """
        The interface of calling LLM for the agent.

        We prepend the system_prompt of this agent to the messages, and call LLM.

        Args:
            messages: A list of messages.
            functions: The list of functions provided to LLM.
            stream: LLM streaming output or non-streaming output.
              For consistency, we default to using streaming output across all agents.

        Yields:
            The response generator of LLM.
        """
        # 1. messages整理: 添加上system_prompt
        messages = copy.deepcopy(messages)
        if self.system_prompt:
            # messages[0]的role不是system: 直接添加Message形式的system_prompt
            if messages[0][ROLE] != MessageRole.SYSTEM:
                messages.insert(
                    0, Message(role=MessageRole.SYSTEM, content=self.system_prompt)
                )
            # messages[0]的role是system 且 content是str: content前加上system_prompt
            elif isinstance(messages[0][CONTENT], str):
                messages[0][CONTENT] = (
                    self.system_prompt + "\n\n" + messages[0][CONTENT]
                )
            # messages[0]的role是system 且 content是list: content前加上ContentItem形式的system_prompt
            else:
                assert isinstance(messages[0][CONTENT], list)
                messages[0][CONTENT] = [
                    ContentItem(text=self.system_prompt + "\n\n")
                ] + messages[0][CONTENT]
        # 2. llm调用
        return self.llm.chat(
            messages=messages,
            functions=functions,
            stream=stream,
            extra_generate_cfg=merge_generate_cfgs(
                base_generate_cfg=self.extra_generate_cfg,
                new_generate_cfg=extra_generate_cfg,
            ),
        )

    def _call_tool(
        self, tool_name: str, tool_args: Union[str, dict] = "{}", **kwargs
    ) -> Union[str, List[ContentItem]]:
        """
        The interface of calling tools for the agent.

        Args:
            tool_name: The name of one tool.
            tool_args: Model generated or user given tool parameters.

        Returns:
            The output of tools.
        """
        # 1. 检查tool是否存在
        if tool_name not in self.function_map:
            return f"Tool {tool_name} does not exists."
        tool = self.function_map[tool_name]
        # 2. 调用tool: tool.call()内部有对参数的检查，所以无需在此检查
        try:
            # 对RAG工具的特殊处理
            if tool_name == MEMORY_TOOL_NAME:
                kwargs["memory"] = self.memory
            tool_result = tool.call(tool_args, **kwargs)
        except Exception as ex:
            exception_type = type(ex).__name__
            exception_message = str(ex)
            traceback_info = "".join(traceback.format_tb(ex.__traceback__))
            error_message = (
                f"An error occurred when calling tool `{tool_name}`:\n"
                f"{exception_type}: {exception_message}\n"
                f"Traceback:\n{traceback_info}"
            )
            logger.warning(error_message)
            return error_message
        # 3. 整理tool.call()结果
        if isinstance(tool_result, str):
            return tool_result
        elif isinstance(tool_result, list) and all(
            isinstance(item, ContentItem) for item in tool_result
        ):
            return tool_result  # multimodal tool results
        else:
            return json.dumps(tool_result, ensure_ascii=False, indent=4)

    def _init_tool(self, tool: Union[str, Dict, BaseTool]) -> None:
        """ "
        Add one tool to the agent function_map.

        Args:
            tool: One tool name, tool configuration or Tool object.
              such as 'code_interpreter', {'name': 'code_interpreter', 'timeout': 10}, or CodeInterpreter().
        """
        # tool是BaseTool: 未出现过则直接添加
        if isinstance(tool, BaseTool):
            tool_name = tool.name
            if tool_name in self.function_map:
                logger.warning(
                    f"Repeatedly adding tool {tool_name}, will use the newest tool in function list"
                )
            self.function_map[tool_name] = tool
        else:
            # tool是str或dict:
            # a. 获取tool_name和tool_cfg
            if isinstance(tool, dict):
                tool_name = tool["name"]
                tool_cfg = tool
            else:
                tool_name = tool
                tool_cfg = None

            # b. 检查tool_name是否存在于TOOL_REGISTRY中
            if tool_name not in TOOL_REGISTRY:
                raise ValueError(f"Tool {tool_name} is not registered.")

            # c. 未出现过则根据tool_cfg创建tool对象并添加到self.function_map中
            if tool_name in self.function_map:
                logger.warning(
                    f"Repeatedly adding tool {tool_name}, will use the newest tool in function list"
                )
            self.function_map[tool_name] = TOOL_REGISTRY[tool_name](tool_cfg)

    def _detect_tool(self, message: Message) -> Tuple[bool, str, str, str]:
        """
        A built-in tool call detection for func_call format message.

        Args:
            message: one message generated by LLM.

        Returns:
            Need to call tool or not, tool name, tool args, text replies.
        """
        func_name = None
        func_args = None

        if message.function_call:
            func_call = message.function_call
            func_name = func_call.name
            func_args = func_call.arguments
        text = message.content
        if not text:
            text = ""

        return (func_name is not None), func_name, func_args, text

    def get_tools_info(self) -> List[str]:
        """
        Return a list of tool info.
        """
        tools_text = []
        for tool in self.function_map.values():
            tools_text.append(tool.info_text)
        return tools_text

    def get_tools_names(self) -> List[str]:
        """
        Return a list of tool names.
        """
        return list(self.function_map.keys())


class ChatAgent(BaseAgent):
    """just a llm"""

    def _run(self, messages: List[dict], lang: str = "en", **kwargs):
        extra_generate_cfg = {"lang": lang}
        if kwargs.get("seed") is not None:
            extra_generate_cfg["seed"] = kwargs["seed"]
        return self._call_llm(messages, extra_generate_cfg=extra_generate_cfg)
