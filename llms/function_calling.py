# copy and modify from:
# https://github.com/QwenLM/Qwen-Agent/blob/main/qwen_agent/llm/function_calling.py

import copy
from abc import ABC
from typing import Dict, Iterator, List, Literal, Optional, Union

from .base import BaseChatModel
from utils.schema import MessageRole, ContentItem, Message


class BaseFnCallModel(BaseChatModel, ABC):
    """
    The class of function calling model.

    Different from BaseChatModel:
    1. self._preprocess_messages(): more preprocessing for function calling
    2. self._postprocess_messages(): more postprocessing for function calling
    3. implement self._chat_with_functions()
    4. implement self._continue_assistant_response()
    """

    def __init__(self, cfg: Optional[Dict] = None):
        super().__init__(cfg)
        # 存在的问题:
        # openai generate_cfg报错
        # TypeError: Completions.create() got an unexpected keyword argument 'fncall_prompt_type'
        # 原：fncall_prompt_type = self.generate_cfg.get('fncall_prompt_type', 'qwen')

        # 设置self.fncall_prompt
        fncall_prompt_type = self.generate_cfg.pop("fncall_prompt_type", "qwen")
        if fncall_prompt_type == "qwen":
            from .fncall_prompts.qwen_fncall_prompt import (
                FN_STOP_WORDS,
                QwenFnCallPrompt,
            )

            self.fncall_prompt = QwenFnCallPrompt()
            stop = self.generate_cfg.get("stop", [])
            self.generate_cfg["stop"] = stop + [
                x for x in FN_STOP_WORDS if x not in stop
            ]
        elif fncall_prompt_type == "nous":
            from .fncall_prompts.nous_fncall_prompt import NousFnCallPrompt

            self.fncall_prompt = NousFnCallPrompt()
        else:
            raise NotImplementedError

    def _preprocess_messages(
        self,
        messages: List[Message],
        lang: Literal["en", "zh"],
        generate_cfg: dict,
        functions: Optional[List[Dict]] = None,
    ) -> List[Message]:
        messages = super()._preprocess_messages(
            messages, lang=lang, generate_cfg=generate_cfg
        )
        # 当chat没传入functions参数/llm的generate_cfg中传入了function_choice='none'时
        if (not functions) or (generate_cfg.get("function_choice", "auto") == "none"):
            messages = self._remove_fncall_messages(messages, lang=lang)
        else:
            validate_num_fncall_results(
                messages=messages,
                support_multimodal_input=self.support_multimodal_input,
            )
            messages = self.fncall_prompt.preprocess_fncall_messages(
                messages=messages,
                functions=functions,
                lang=lang,
                parallel_function_calls=generate_cfg.get(
                    "parallel_function_calls", False
                ),
                function_choice=generate_cfg.get("function_choice", "auto"),
            )
        return messages

    def _postprocess_messages(
        self,
        messages: List[Message],
        fncall_mode: bool,
        generate_cfg: dict,
    ) -> List[Message]:
        messages = super()._postprocess_messages(
            messages, fncall_mode=fncall_mode, generate_cfg=generate_cfg
        )
        # 当chat传入了functions参数
        # 且 llm的generate_cfg中传入了function_choice?
        #       传入且不为'none'时
        #       没传入时
        if fncall_mode:
            messages = self.fncall_prompt.postprocess_fncall_messages(
                messages=messages,
                parallel_function_calls=generate_cfg.get(
                    "parallel_function_calls", False
                ),
                function_choice=generate_cfg.get("function_choice", "auto"),
            )
        return messages

    def _remove_fncall_messages(
        self, messages: List[Message], lang: Literal["en", "zh"]
    ) -> List[Message]:
        # Change function calls into user messages so that the model won't try
        # to generate function calls when given functions and function_choice="none".
        new_messages = []
        for msg in messages:
            if (msg.role == MessageRole.FUNCTION) or msg.function_call:
                if (not new_messages) or (new_messages[-1].role != MessageRole.USER):
                    new_messages.append(Message(role=MessageRole.USER, content=[]))
                if msg.function_call:
                    tool_name = msg.function_call.name
                    tool_args = msg.function_call.arguments
                    if lang == "zh":
                        tool_text = f'\n\n工具"{tool_name}"被调用时使用了以下参数：\n{tool_args}'
                    else:
                        tool_text = f'\n\nThe tool "{tool_name}" was called with these arguments:\n{tool_args}'
                else:
                    assert msg.role == MessageRole.FUNCTION
                    if msg.content:
                        assert len(msg.content) == 1
                        assert isinstance(msg.content[0], ContentItem)
                        assert isinstance(msg.content[0].text, str)
                        tool_result = msg.content[0].text
                    else:
                        tool_result = "No result."
                    if lang == "zh":
                        tool_text = f"\n\n该工具返回了以下结果：\n{tool_result}"
                    else:
                        tool_text = f"\n\nThe tool has returned the following result:\n{tool_result}"
                new_messages[-1].content.append(ContentItem(text=tool_text))
            else:
                if (
                    (msg.role == MessageRole.USER)
                    and new_messages
                    and (new_messages[-1].role == MessageRole.USER)
                ):
                    # Separate two user messages with an assistant message to make the bot focus on the latter:
                    new_messages.append(
                        Message(
                            role=MessageRole.ASSISTANT,
                            content=[ContentItem(text="...")],
                        )
                    )
                new_messages.append(msg)
        return new_messages

    def _chat_with_functions(
        self,
        messages: List[Message],
        functions: List[Dict],
        stream: bool,
        delta_stream: bool,
        generate_cfg: dict,
        lang: Literal["en", "zh"],
    ) -> Union[List[Message], Iterator[List[Message]]]:
        if delta_stream:
            raise NotImplementedError(
                "Please use stream=True with delta_stream=False, because delta_stream=True"
                " is not implemented for function calling due to some technical reasons."
            )
        generate_cfg = copy.deepcopy(generate_cfg)
        for k in ["parallel_function_calls", "function_choice"]:
            if k in generate_cfg:
                del generate_cfg[k]
        return self._continue_assistant_response(
            messages, generate_cfg=generate_cfg, stream=stream
        )

    def _continue_assistant_response(
        self,
        messages: List[Message],
        generate_cfg: dict,
        stream: bool,
    ) -> Iterator[List[Message]]:
        messages = simulate_response_completion_with_chat(messages)
        return self._chat(
            messages, stream=stream, delta_stream=False, generate_cfg=generate_cfg
        )


def simulate_response_completion_with_chat(messages: List[Message]) -> List[Message]:
    if messages and (messages[-1].role == MessageRole.ASSISTANT):
        assert (len(messages) > 1) and (messages[-2].role == MessageRole.USER)
        assert messages[-1].function_call is None
        usr = messages[-2].content
        bot = messages[-1].content
        sep = "\n\n"
        if isinstance(usr, str) and isinstance(bot, str):
            usr = usr + sep + bot
        elif isinstance(usr, list) and isinstance(bot, list):
            usr = usr + [ContentItem(text=sep)] + bot
        else:
            raise NotImplementedError
        text_to_complete = copy.deepcopy(messages[-2])
        text_to_complete.content = usr
        messages = messages[:-2] + [text_to_complete]
    return messages


def validate_num_fncall_results(
    messages: List[Message], support_multimodal_input: bool
):
    fn_results = []
    i = len(messages) - 1
    while messages[i].role == MessageRole.FUNCTION:
        fn_results = [messages[i].name] + fn_results
        content = messages[i].content
        if isinstance(content, list):
            for item in content:
                if item.file:
                    raise ValueError(
                        'Tool call results with content type="file" are not supported.'
                    )
                if item.image and (not support_multimodal_input):
                    raise ValueError(
                        "The current model service does not accept images as tool results."
                    )
        i -= 1

    fn_calls = []
    while messages[i].function_call:
        fn_calls = [messages[i].function_call.name] + fn_calls
        i -= 1

    if len(fn_calls) != len(fn_results):
        raise ValueError(
            f'Expecting {len(fn_calls)} function results (i.e., messages with role="function") '
            f"but received {len(fn_results)} function results. "
            "The number of function results must match that of the function_call messages."
        )
    for fc_name, fr_name in zip(fn_calls, fn_results):
        if fr_name and (fc_name != fr_name):
            raise ValueError(
                'The function results (i.e., the messages with role="function" ) must be '
                "put in the same order as the function_call messages. And the function names must match."
                f"The function results are currently {fn_results}. But {fn_calls} are expected."
            )
