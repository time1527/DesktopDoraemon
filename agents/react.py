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
    TEMPLETE_SUMMARY,
    MessageRole,
    Message,
)
from utils.utils import format_as_text_message, merge_generate_cfgs
from settings import MAX_LLM_CALL_PER_RUN


# NOTE：chat history的处理
# 1.messages里对话turn永远<self.messages_window_size
#   messages里turn>self.messages_window_size时，会使用llm总结前面的对话
#   追加：如果messages里是n*self.messages_window_size，追加总结
# TODO:
# 2.如果历史里有调用工具的历史，选择最近的一次正确调用作为one-shot，
# 当前这个也会被总结，只是除了总结之外还会被保留作为one-shot
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
        summary_llm: Optional[Union[Dict, BaseChatModel]] = None,
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
        if summary_llm is not None:
            if isinstance(summary_llm, BaseChatModel):
                self.summary_llm = summary_llm
            else:
                self.summary_llm = BaseChatModel.from_dict(summary_llm)
        else:
            self.summary_llm = self.llm
        self.summary_history = ""
        self.messages_window_size = 20
        self.raw_system_prompt = system_prompt

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
        # text messges里没有system prompt, system prompt在agent._call_llm时候自动添加
        # 所以需要变动的是self.system_prompt

        # 2.历史信息压缩
        if (
            len(text_messages) > 1
            and (len(text_messages) - 1) % (self.messages_window_size * 2) == 0
        ):
            # 截取messages的最后一个messages_window_size窗口消息
            to_summarize_messages = text_messages[
                -self.messages_window_size * 2 - 1 : -1
            ]
            if to_summarize_messages[-1]["role"] != "assistant":
                raise ValueError(
                    "The last message in to_summarize_messages should be from assistant."
                )
            if to_summarize_messages[0]["role"] != "user":
                raise ValueError(
                    "The first message in to_summarize_messages should be from user."
                )
            # 生成总结
            summary = self.summary_llm.chat(
                messages=[
                    Message(
                        role=MessageRole.USER,
                        content=TEMPLETE_SUMMARY.format(
                            previous_summary=self.summary_history,
                            new_conversation=to_summarize_messages,
                        ),
                    )
                ],
                stream=False,
                extra_generate_cfg=self.extra_generate_cfg,
            )
            summary = summary[0].content
            # 添加总结历史
            self.summary_history = summary
            # 截取messages
            text_messages = text_messages[-1:]
            # 更新system prompt
            self.system_prompt = (
                self.raw_system_prompt
                + f"\nSummary of the previous conversation:\n{self.summary_history}"
            )
        elif len(text_messages) > 1 and self.summary_history:
            # u1-a1-u2-a2-u3-a3-u4
            l = len(text_messages)
            idx = (l - 1) % (self.messages_window_size * 2)
            text_messages = text_messages[-idx - 1 :]  # 没有重叠

        # 3. 改写最后一条消息内容
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
