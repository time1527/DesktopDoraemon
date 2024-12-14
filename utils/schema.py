# copy and modify from:
# https://github.com/QwenLM/Qwen-Agent/blob/main/qwen_agent/llm/schema.py

from typing import List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, field_validator, model_validator


ROLE = "role"
CONTENT = "content"
NAME = "name"
DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant."""


TEMPLETE_REACT = """Answer the following questions as best you can. You have access to the following tools:

{tool_descs}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can be repeated zero or more times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {query}
Thought: """

REACT_TOOL_TOKEN = "\nAction:"
REACT_ARGS_TOKEN = "\nAction Input:"
REACT_OBS_TOKEN = "\nObservation:"


class MessageRole:
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class MessageType:
    TEXT = "text"
    FILE = "file"
    IMAGE = "image"


class BaseModelCompatibleDict(BaseModel):

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)

    def model_dump_json(self, **kwargs):
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump_json(**kwargs)

    def get(self, key, default=None):
        try:
            value = getattr(self, key)
            if value:
                return value
            else:
                return default
        except AttributeError:
            return default

    def __str__(self):
        return f"{self.model_dump()}"


class FunctionCall(BaseModelCompatibleDict):
    name: str
    arguments: str

    def __init__(self, name: str, arguments: str):
        super().__init__(name=name, arguments=arguments)

    def __repr__(self):
        return f"FunctionCall({self.model_dump()})"


class ContentItem(BaseModelCompatibleDict):
    text: Optional[str] = None
    image: Optional[str] = None
    file: Optional[str] = None

    def __init__(
        self,
        text: Optional[str] = None,
        image: Optional[str] = None,
        file: Optional[str] = None,
    ):
        super().__init__(text=text, image=image, file=file)

    @model_validator(mode="after")
    def check_exclusivity(self):
        provided_fields = 0
        if self.text is not None:
            provided_fields += 1
        if self.image:
            provided_fields += 1
        if self.file:
            provided_fields += 1

        if provided_fields != 1:
            raise ValueError(
                "Exactly one of 'text', 'image', or 'file' must be provided."
            )
        return self

    def __repr__(self):
        return f"ContentItem({self.model_dump()})"

    def get_type_and_value(self) -> Tuple[Literal["text", "image", "file"], str]:
        ((t, v),) = self.model_dump().items()
        assert t in ("text", "image", "file")
        return t, v

    @property
    def type(self) -> Literal["text", "image", "file"]:
        t, v = self.get_type_and_value()
        return t

    @property
    def value(self) -> str:
        t, v = self.get_type_and_value()
        return v


class Message(BaseModelCompatibleDict):
    role: str
    content: Union[str, List[ContentItem]]
    name: Optional[str] = None
    function_call: Optional[FunctionCall] = None
    extra: Optional[dict] = None

    def __init__(
        self,
        role: str,
        content: Optional[Union[str, List[ContentItem]]],
        name: Optional[str] = None,
        function_call: Optional[FunctionCall] = None,
        extra: Optional[dict] = None,
        **kwargs,
    ):
        if content is None:
            content = ""
        super().__init__(
            role=role,
            content=content,
            name=name,
            function_call=function_call,
            extra=extra,
        )

    def __repr__(self):
        return f"Message({self.model_dump()})"

    @field_validator("role")
    def role_checker(cls, value: str) -> str:
        if value not in [
            MessageRole.USER,
            MessageRole.ASSISTANT,
            MessageRole.SYSTEM,
            MessageRole.FUNCTION,
        ]:
            l = [
                MessageRole.USER,
                MessageRole.ASSISTANT,
                MessageRole.SYSTEM,
                MessageRole.FUNCTION,
            ]
            raise ValueError(f'{value} must be one of {",".join(l)}')
        return value
