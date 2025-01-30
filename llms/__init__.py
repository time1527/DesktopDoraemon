# copy and modify from:
# https://github.com/QwenLM/Qwen-Agent/blob/main/qwen_agent/llm/__init__.py

import copy
from typing import Union

from .base import LLM_REGISTRY, BaseChatModel
from .function_calling import BaseFnCallModel
from .oai import TextChatAtOAI
from .qwen_dashscope import QwenChatAtDS


def get_chat_model(cfg: Union[dict, str]) -> BaseChatModel:
    """
    The interface of instantiating LLM objects.

    Args:
        cfg: The LLM configuration, one example is:
          cfg = {
              # Use ollama: 需要在本地启动ollama: ollama serve，并且ollama run qwen2.5:0.5b
              'model': 'qwen2.5:0.5b',
              'model_server': 'http://localhost:11434/v1/',
              'api_key': 'EMPTY'

              # (Optional) LLM hyper-parameters:
              'generate_cfg': {
                  'top_p': 0.8,
                  'max_input_tokens': 6500,
                  'max_retries': 10,
              }
          }

    Returns:
        LLM object.
    """
    if isinstance(cfg, str):
        cfg = {"model": cfg}

    if "model_type" in cfg:
        model_type = cfg["model_type"]
        if model_type in LLM_REGISTRY:
            if model_type in ("oai", "qwenvl_oai"):
                if cfg.get("model_server", "").strip() == "dashscope":
                    cfg = copy.deepcopy(cfg)
                    cfg["model_server"] = (
                        "https://dashscope.aliyuncs.com/compatible-mode/v1"
                    )
            return LLM_REGISTRY[model_type](cfg)
        else:
            raise ValueError(f"Please set model_type from {str(LLM_REGISTRY.keys())}")

    # Deduce model_type from model and model_server if model_type is not provided:

    if "azure_endpoint" in cfg:
        model_type = "azure"
        return LLM_REGISTRY[model_type](cfg)

    if "model_server" in cfg:
        if cfg["model_server"].strip().startswith("http"):
            model_type = "oai"
            return LLM_REGISTRY[model_type](cfg)

    model = cfg.get("model", "")

    if "qwen-vl" in model:
        model_type = "qwenvl_dashscope"
        return LLM_REGISTRY[model_type](cfg)

    if "qwen" in model:
        model_type = "qwen_dashscope"
        return LLM_REGISTRY[model_type](cfg)

    raise ValueError(f"Invalid model cfg: {cfg}")


__all__ = [
    "BaseChatModel",
    "BaseFnCallModel",
    "TextChatAtOAI",
    "ModelServiceError",
    "QwenChatAtDS",
    "get_chat_model",
]
