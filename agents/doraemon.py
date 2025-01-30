from typing import List, Literal, Iterator
import json
from agents.react import ReAct
from utils.schema import (
    REACT_TOOL_TOKEN,
    REACT_ARGS_TOKEN,
    REACT_OBS_TOKEN,
    MessageRole,
    Message,
)
from utils.utils import format_as_text_message
from settings import MAX_LLM_CALL_PER_RUN, MEMORY_TOOL_NAME


class DoraemonAgent(ReAct):

    def _format_text_messages(
        self, messages: List[Message], lang: Literal["en", "zh"]
    ) -> List[Message]:
        """
        Format the messages for text.

        Args:
            messages: The messages to be formatted.
            lang: The language of the messages.

        Returns:
            The formatted messages.
        """
        assert messages[-1]["role"] == "user", "The last message should be user query."
        text_messages = [
            format_as_text_message(m, add_upload_info=True, lang=lang) for m in messages
        ]
        return text_messages

    def _check(
        self,
        messages: List[Message],
        observation: str,
    ) -> str:
        """
        Memory chat.
        Args:
            messages: The messages.
            observation: The observation.
            action: The action.
            action_input: The action input.
        Returns:
            The response.
        """
        text_messages = self._format_text_messages(messages, lang="zh")
        prompt = f"判断{observation}是否能够回答{text_messages}的问题，如果可以回答，从中提取出相关部分并返回；如果不能回答，返回“不知道。”"
        check_messages = [
            Message(
                role=MessageRole.USER,
                content=prompt,
            )
        ]
        response = ""
        output = []
        for output in self._call_llm(messages=check_messages):
            if output:
                response = output[-1].content
        return json.dumps(
            {"text": f"在哆啦A梦的记忆中：{response}"}, ensure_ascii=False
        )

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

            # 额外处理：MemoryTool
            if action == MEMORY_TOOL_NAME:
                # 4. 记忆对话: Agent类的_memory_chat方法
                observation = self._check(messages=messages, observation=observation)

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
