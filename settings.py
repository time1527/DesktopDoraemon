from pathlib import Path
from typing import List

# path
REPO_PATH = Path(__file__).parent
DEFAULT_LOG_STORAGE_PATH: str = REPO_PATH / "log"
DEFAULT_MODEL_STORAGE_PATH: str = REPO_PATH / "models"
WORK_DIR: str = REPO_PATH / "work_dir"

# llm
DEFAULT_MAX_INPUT_TOKENS: int = (
    20000  # The LLM will truncate the input messages if they exceed this limit
)
DEFAULT_OLLAMA_CFG: dict = {  # ollama config
    "model": "qwen2.5:0.5b",
    "model_server": "http://localhost:11434/v1/",
    "api_key": "EMPTY",
    "generate_cfg": {
        "top_p": 0.8,
        "max_input_tokens": DEFAULT_MAX_INPUT_TOKENS,
        "fncall_prompt_type": "qwen",
        "repetition_penalty": 1.05,
    },
}
DEFAULT_VLLM_CFG: dict = {  # vllm config
    "model": "Qwen/Qwen2.5-3B-Instruct",
    "model_server": "http://localhost:8000/v1",
    "api_key": "EMPTY",
    "generate_cfg": {
        "top_p": 0.8,
        "max_input_tokens": DEFAULT_MAX_INPUT_TOKENS,
        "fncall_prompt_type": "qwen",
        "repetition_penalty": 1.05,
    },
}
DEFAULT_FT_CFG: dict = {  # vllm config
    "model": "/home/pika/Model/desktop-doraemon/r=4/merged/checkpoint-1000",
    "model_server": "http://localhost:8000/v1",
    "api_key": "EMPTY",
    "generate_cfg": {
        "top_p": 0.8,
        "max_input_tokens": DEFAULT_MAX_INPUT_TOKENS,
        "fncall_prompt_type": "qwen",
        "repetition_penalty": 1.05,
    },
}
DEFAULT_DASHSCOPE_CFG: dict = {  # dashscope
    "model": "qwen-turbo",
    "generate_cfg": {
        "top_p": 0.8,
        "repetition_penalty": 1.05,
    },
}

# memory
DEFAULT_MEMORY_CFG: dict = {
    "files": REPO_PATH / "assets" / "tools" / "content" / "characters.md",
    # write your own model path here or use dashscopeembeddings
    # # use local model path
    # 'embedding_cfg':
    # {
    #     'model_name': DEFAULT_MODEL_STORAGE_PATH / "jinaai/jina-embeddings-v3",
    #     'model_kwargs': {
    #         'device': 'cpu',
    #         'trust_remote_code': True,
    #     },
    #     'encode_kwargs': {
    #       'normalize_embeddings': True
    #     }
    # },
    # use dashscopeembeddings
    "embedding_cfg": {},
    "use_reranker": True,
    "reranker_cfg": {},
    "vector_store_path": WORK_DIR / "vector_store",
}
MEMORY_TOOL_NAME = "DoraemonMemory"

# agent
MAX_LLM_CALL_PER_RUN: int = 8
DEFAULT_FUNCS: List[str] = [  # functions
    "GithubTrending",
    "ImageGen",
    "RemoveImageBackground",  # done
    "TreasureBag",
    "ToDo",
    MEMORY_TOOL_NAME,
]

# client
DEFAULT_CLIENT_TYPE: str = "react"  # chat/react/doraemon
DEFAULT_CHAT_LLM_CFG: dict = DEFAULT_FT_CFG  # llm cfg used in chat client
DEFAULT_REACT_LLM_CFG: dict = DEFAULT_DASHSCOPE_CFG  # llm cfg used in react client
DEFAULT_DORAEMON_LLM_CFG: dict = (
    DEFAULT_FT_CFG  # llm cfg used in doraemon client ---react llm call + another llm call
)

# tts
TTS: bool = True
