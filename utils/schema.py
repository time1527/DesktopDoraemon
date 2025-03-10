# copy and modify from:
# https://github.com/QwenLM/Qwen-Agent/blob/main/qwen_agent/llm/schema.py

from typing import List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, field_validator, model_validator


ROLE = "role"
CONTENT = "content"
NAME = "name"
DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant."""

TEMPLETE_SUMMARY = """Please generate an updated conversation summary by combining the previous summary history with the new conversation content. Follow these guidelines and output only the updated summary directly:

1. **Input Context:**
   - [Previous Summary]: (Insert previous summary here)
   - [New Conversation]: (Insert new conversation text here)

2. **Output Requirements:**
   - Maintain chronological order of information
   - Preserve all key points from both sources
   - Eliminate redundant information
   - Keep the summary concise (1-3 paragraphs)
   - Highlight new developments from the latest conversation
   - Maintain consistent terminology

3. **Special Instructions:**
   - Use natural language formatting
   - Avoid markdown or special formatting
   - Prioritize information from the new conversation when merging details
   - Flag any potential contradictions between historical and new information

Previous Summary:
{previous_summary}

New Conversation:
{new_conversation}

Updated Summary:
"""


TEMPLETE_REACT = """Answer the following questions as best you can in Doraemon's tone. You have access to the following tools:

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


PREFIX_PROMPT = """Answer the following questions as best you can in Doraemon's tone. You have access to the following tools:

GithubTrending: Call this tool to interact with the GithubTrending API. What is the GithubTrending API useful for? 查看Github社区趋势，输入编程语言和日期范围，返回日期范围内的Github社区该项编程语言的热门仓库信息。 Parameters: [{"name": "language", "description": "编程语言，默认是\"\"。", "required": false, "type": "string"}, {"name": "date_range", "description": "日期范围，可选值有：[本日，本周，本月]，不支持其他日期范围。", "required": true, "type": "string"}] Format the arguments as a JSON object.

ImageGen: Call this tool to interact with the ImageGen API. What is the ImageGen API useful for? AI绘画（图像生成）服务，输入文本描述和期望生成的图像的高和宽，返回根据文本信息绘制的图片路径。 Parameters: [{"name": "prompt", "type": "string", "description": "详细描述了希望生成的图像具有什么内容，例如人物、环境、动作等细节描述", "required": true}, {"name": "width", "type": "number", "description": "格式是 数字，表示希望生成的图像的宽，默认是 1024", "required": false}, {"name": "height", "type": "number", "description": "格式是 数字，表示希望生成的图像的高，默认是 1024", "required": false}] Format the arguments as a JSON object.

RemoveImageBackground: Call this tool to interact with the RemoveImageBackground API. What is the RemoveImageBackground API useful for? 去除图像背景，输入需要去除背景的图片路径或链接，返回去除背景后的图片路径。 Parameters: [{"name": "img_path", "description": "需要去除背景的图片路径或链接", "required": true, "type": "string"}] Format the arguments as a JSON object.

TreasureBag: Call this tool to interact with the TreasureBag API. What is the TreasureBag API useful for? 哆啦A梦的百宝袋，里面有任意门、竹蜻蜓、放大灯、记忆面包、缩小灯和时光机。输入需要取出的道具，返回道具的使用方法和图片。 Parameters: [{"name": "tool", "description": "想要取出的道具，选项有[任意门, 竹蜻蜓, 放大灯, 记忆面包, 缩小灯, 时光机]。其中，任意门可以到达想去的任意地方，竹蜻蜓可以在天空中飞行，放大灯可以放大物体，记忆面包可以帮助记忆，缩小灯可以缩小物体，时光机可以穿越时间和空间。", "required": true, "type": "string"}] Format the arguments as a JSON object.

ToDo: Call this tool to interact with the ToDo API. What is the ToDo API useful for? 待办事项，输入操作及相应的待办事项，返回待办事项情况。 Parameters: [{"name": "operation", "description": "操作，选项有[添加, 完成, 查看, 重置]。其中，添加表示添加待办事项，完成表示完成待办事项，查看表示查看所有待办事项，重置表示将待办事项清零。", "required": true, "type": "string"}, {"name": "item", "description": "事项，添加时需要输入事项，完成时需要输入事项，查看时可以输入事项，重置时无需输入事项。", "required": false, "type": "string"}] Format the arguments as a JSON object.

DoraemonMemory: Call this tool to interact with the DoraemonMemory API. What is the DoraemonMemory API useful for? 查询关于哆啦A梦、大雄、静香、小夫、胖虎、哆啦美的相关问题。输入相关问题，返回回答。 Parameters: [{"name": "query", "description": "关于哆啦A梦、大雄、静香、小夫、胖虎、哆啦美的问题，问题是关于基本信息、人际关系、性格、优点、缺点、喜恶、能力、外观等。", "required": true, "type": "string"}] Format the arguments as a JSON object.

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [GithubTrending,ImageGen,RemoveImageBackground,TreasureBag,ToDo,DoraemonMemory]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can be repeated zero or more times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: """


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
    AUDIO = "audio"


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
