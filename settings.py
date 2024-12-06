from pathlib import Path
from typing import List

# path
REPO_PATH = Path(__file__).parent
DEFAULT_LOG_STORAGE_PATH: str = REPO_PATH / 'log'
DEFAULT_MODEL_STORAGE_PATH: str = REPO_PATH / 'models'
WORK_DIR: str = REPO_PATH / 'work_dir'

# llm
DEFAULT_MAX_INPUT_TOKENS: int = 5800  # The LLM will truncate the input messages if they exceed this limit
DEFAULT_OAI_CFG: dict = { # openai format api config
    'model':'qwen2.5:0.5b',
    'model_server':"http://localhost:11434/v1/",
    'api_key': 'EMPTY',
    'generate_cfg': {
        'top_p': 0.8,
        'max_input_tokens': 6500,
        'fncall_prompt_type': 'qwen',
    }
}
DEFAULT_QWEN_MAX_CFG: dict = { # dashscope 
    'model': 'qwen-max'
}

# memory
DEFAULT_MEMORY_CFG: dict = {
    'files': REPO_PATH / 'data' / 'tools' / 'content' / 'characters.md',
    'embedding_cfg': 
    {
        # write your own model path here
        'model_name': DEFAULT_MODEL_STORAGE_PATH / "jinaai/jina-embeddings-v3", 
        'model_kwargs': {
            'device': 'cpu',
            'trust_remote_code': True,
        },
        'encode_kwargs': {
          'normalize_embeddings': True
        }
    },
    'vector_store_path': WORK_DIR / 'vector_store',
}
MEMORY_TOOL_NAME = 'AboutFriends'

# agent
MAX_LLM_CALL_PER_RUN: int = 8
DEFAULT_FUNCS: List[str] = [ # functions
    'GithubTrending',
    'ImageGen',
    'RemoveImageBackground',
    'TreasureBag',
    'TODO',
    MEMORY_TOOL_NAME
]

# client
DEFAULT_CLIENT_TYPE: str = 'react' # react or chat
DEFAULT_CHAT_LLM_CFG: dict = DEFAULT_OAI_CFG # llm cfg used in chat client
DEFAULT_REACT_LLM_CFG: dict = DEFAULT_QWEN_MAX_CFG # llm cfg used in react client