# copy and modify from:
# https://github.com/QwenLM/Qwen-Agent/blob/main/qwen_agent/agents/react_chat.py

from typing import List, Optional, Literal, Iterator, Union, Dict, Tuple

from agents.base import BaseAgent
from llms.base import BaseChatModel
from memory.base import BaseMemory
from tools.base import BaseTool
from utils.schema import (
    TEMPLETE_REACT,
    REACT_TOOL_TOKEN,
    REACT_ARGS_TOKEN,
    REACT_OBS_TOKEN,
    DEFAULT_SYSTEM_PROMPT,
    MessageRole,
    Message,
)
from utils.utils import format_as_text_message, merge_generate_cfgs
from settings import MAX_LLM_CALL_PER_RUN


class ReAct(BaseAgent):
    """
    A class of ReAct agent.

    Difference from Agent:
    1. self._run()
    2. self._detect_tool()
    """

    def __init__(
        self,
        function_list: Optional[List[Union[str, Dict, BaseTool]]] = None,
        llm: Optional[Union[Dict, BaseChatModel]] = None,
        memory: Optional[Union[Dict, BaseMemory]] = None,
        system_prompt: Optional[str] = DEFAULT_SYSTEM_PROMPT,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            function_list, llm, memory, system_prompt, name, description, **kwargs
        )
        # 添加stop words
        # 注意：如果llm类型是BaseFncallModel 且 fncall_prompt_type='qwen'（默认），也会添加stop words
        self.extra_generate_cfg = merge_generate_cfgs(
            base_generate_cfg=self.extra_generate_cfg,
            new_generate_cfg={"stop": ["Observation:", "Observation:\n"]},
        )

    def _format_react_messages(
        self, messages: List[Message], lang: Literal["en", "zh"]
    ) -> List[Message]:
        """
        Format the messages for ReAct agent.

        Args:
            messages: The messages to be formatted.
            lang: The language of the messages.

        Returns:
            The formatted messages.
        """
        assert messages[-1]["role"] == "user", "The last message should be user query."

        # 1. 转换为text_message
        text_messages = [
            format_as_text_message(m, add_upload_info=True, lang=lang) for m in messages
        ]

        # 2. 改写最后一条消息内容
        text_messages[-1].content = TEMPLETE_REACT.format(
            tool_descs="\n\n".join(self.get_tools_info()),
            tool_names=",".join(self.get_tools_names()),
            query=text_messages[-1]["content"],
        )
        return text_messages

    def _detect_tool(self, text: str) -> Tuple[bool, str, str, str]:
        """
        Detect the tool name and tool args from the text.

        Args:
            text: The text to be detected.

        Returns:
            A tuple of (has_action, func_name, func_args, text).
        """
        func_name, func_args = None, None
        i = text.rfind(REACT_TOOL_TOKEN)
        j = text.rfind(REACT_ARGS_TOKEN)
        k = text.rfind(REACT_OBS_TOKEN)
        if 0 <= i < j:  # If the text has `Action` and `Action input`,
            if k < j:  # but does not contain `Observation`,
                # then it is likely that `Observation` is ommited by the LLM,
                # because the output text may have discarded the stop word.
                text = text.rstrip() + REACT_OBS_TOKEN  # Add it back.
            k = text.rfind(REACT_OBS_TOKEN)
            func_name = text[i + len(REACT_TOOL_TOKEN) : j].strip()
            func_args = text[j + len(REACT_ARGS_TOKEN) : k].strip()
            text = text[:i]  # Return the response before tool call, i.e., `Thought`
        return (func_name is not None), func_name, func_args, text

    def _run(
        self, messages: List[Message], lang: Literal["en", "zh"] = "en", **kwargs
    ) -> Iterator[List[Message]]:
        """
        Run the agent.

        Args:
            messages: A list of messages.
            lang: The language of the messages.
            **kwargs: Additional arguments.

        Yields:
            The response generator.
        """
        # 1. 按照React Prompt模板格式化消息: ReAct类的_format_react_messages方法
        text_messages = self._format_react_messages(messages, lang=lang)

        num_llm_calls_available = MAX_LLM_CALL_PER_RUN
        response: str = "Thought: "

        # 不断更新text_messages[-1]的content再喂给llm
        while num_llm_calls_available > 0:
            num_llm_calls_available -= 1

            # 1. llm生成回复: Agent类的_call_llm方法
            # 1.1. Display the streaming response
            output = []
            for output in self._call_llm(messages=text_messages):
                if output:
                    yield [
                        Message(
                            role=MessageRole.ASSISTANT,
                            content=response + output[-1].content,
                        )
                    ]

            # 1.2. Accumulate the current response
            if output:
                response += output[-1].content

            # 2. 检测tool: ReAct类的_detect_tool方法
            has_action, action, action_input, thought = self._detect_tool(
                output[-1].content
            )
            if not has_action:
                break

            # 3. 调用tool: Agent类的_call_tool方法
            # Add the tool result
            observation = self._call_tool(
                action, action_input, messages=messages, **kwargs
            )
            observation = f"{REACT_OBS_TOKEN} {observation}\nThought: "
            response += observation
            yield [Message(role=MessageRole.ASSISTANT, content=response)]

            if (not text_messages[-1].content.endswith("\nThought: ")) and (
                not thought.startswith("\n")
            ):
                # Add the '\n' between '\nQuestion:' and the first 'Thought:'
                text_messages[-1].content += "\n"
            if action_input.startswith("```"):
                # Add a newline for proper markdown rendering of code
                action_input = "\n" + action_input
            text_messages[-1].content += (
                thought
                + f"{REACT_TOOL_TOKEN} {action}{REACT_ARGS_TOKEN} {action_input}"
                + observation
            )
