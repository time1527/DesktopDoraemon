# copy and modify from:
# https://github.com/QwenLM/Qwen-Agent/blob/main/qwen_agent/tools/base.py

import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

from utils.schema import ContentItem
from utils.utils import json_loads
from log import logger


TOOL_DESC = (
    "{name_for_model}: Call this tool to interact with the {name_for_human} API. "
    "What is the {name_for_human} API useful for? {description} Parameters: {parameters} Format the arguments as a JSON object."
)

TOOL_REGISTRY = {}


def register_tool(name, allow_overwrite=False):

    def decorator(cls):
        if name in TOOL_REGISTRY:
            if allow_overwrite:
                logger.warning(
                    f"Tool `{name}` already exists! Overwriting with class {cls}."
                )
            else:
                raise ValueError(
                    f"Tool `{name}` already exists! Please ensure that the tool name is unique."
                )
        if cls.name and (cls.name != name):
            raise ValueError(
                f'{cls.__name__}.name="{cls.name}" conflicts with @register_tool(name="{name}").'
            )
        cls.name = name
        TOOL_REGISTRY[name] = cls

        return cls

    return decorator


def is_tool_schema(obj: dict) -> bool:
    """
    Check if obj is a valid JSON schema describing a tool compatible with OpenAI's tool calling.
    Example valid schema:
    {
      "name": "get_current_weather",
      "description": "Get the current weather in a given location",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city and state, e.g. San Francisco, CA"
          },
          "unit": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"]
          }
        },
        "required": ["location"]
      }
    }
    """
    import jsonschema

    try:
        assert set(obj.keys()) == {"name", "description", "parameters"}
        assert isinstance(obj["name"], str)
        assert obj["name"].strip()
        assert isinstance(obj["description"], str)
        assert isinstance(obj["parameters"], dict)

        assert set(obj["parameters"].keys()) == {"type", "properties", "required"}
        assert obj["parameters"]["type"] == "object"
        assert isinstance(obj["parameters"]["properties"], dict)
        assert isinstance(obj["parameters"]["required"], list)
        assert set(obj["parameters"]["required"]).issubset(
            set(obj["parameters"]["properties"].keys())
        )
    except AssertionError:
        return False
    try:
        jsonschema.validate(instance={}, schema=obj["parameters"])
    except jsonschema.exceptions.SchemaError:
        return False
    except jsonschema.exceptions.ValidationError:
        pass
    return True


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    parameters: Union[List[dict], dict] = []

    def __init__(self, cfg: Optional[Dict] = None):
        self.cfg = cfg or {}

        if not self.name:
            raise ValueError(
                f"You must set {self.__class__.__name__}.name, either by @register_tool(name=...) or explicitly setting {self.__class__.__name__}.name"
            )

        # 如果self.parameters是dict，需要检查是否符合openai-compatible JSON schema
        # 注意: 实现的tool的parameters是list，不会进行这个检查
        if isinstance(self.parameters, dict):
            if not is_tool_schema(
                {
                    "name": self.name,
                    "description": self.description,
                    "parameters": self.parameters,
                }
            ):
                raise ValueError(
                    "The parameters, when provided as a dict, must confirm to a valid openai-compatible JSON schema."
                )

    @abstractmethod
    def call(
        self, params: Union[str, dict], **kwargs
    ) -> Union[str, list, dict, List[ContentItem]]:
        """
        The interface for calling tools.

        Each tool needs to implement this function, which is the workflow of the tool.

        Args:
            params: The parameters of func_call.
            kwargs: Additional parameters for calling tools.

        Returns:
            The result returned by the tool, implemented in the subclass.
        """
        raise NotImplementedError

    def _verify_json_format_args(
        self, params: Union[str, dict], strict_json: bool = False
    ) -> dict:
        """Verify the parameters of the function call"""
        if isinstance(params, str):
            try:
                if strict_json:
                    params_json: dict = json.loads(params)
                else:
                    params_json: dict = json_loads(params)
            except json.decoder.JSONDecodeError:
                raise ValueError("Parameters must be formatted as a valid JSON!")
        else:
            params_json: dict = params

        if isinstance(self.parameters, list):
            for param in self.parameters:
                if "required" in param and param["required"]:
                    if param["name"] not in params_json:
                        raise ValueError("Parameters %s is required!" % param["name"])
        elif isinstance(self.parameters, dict):
            import jsonschema

            jsonschema.validate(instance=params_json, schema=self.parameters)
        else:
            raise ValueError
        return params_json

    @property
    def info(self) -> dict:
        """
        Return the tool's info in dict.
        """
        return {
            "name_for_human": self.name_for_human,
            "name_for_model": self.name_for_model,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    @property
    def info_text(self) -> str:
        """
        Return the tool's info in plain text.
        """
        return TOOL_DESC.format(
            name_for_model=self.info["name_for_model"],
            name_for_human=self.info["name_for_human"],
            description=self.info["description"],
            parameters=json.dumps(self.info["parameters"], ensure_ascii=False),
        )

    @property
    def name_for_human(self) -> str:
        return self.cfg.get("name_for_human", self.name)

    @property
    def name_for_model(self) -> str:
        return self.cfg.get("name_for_model", self.name)
