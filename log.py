# copy and modify from:
# https://github.com/QwenLM/Qwen-Agent/blob/main/qwen_agent/log.py

import logging


def setup_logger(level=None):
    if level is None:
        level = logging.INFO

    handler = logging.StreamHandler()
    # Do not run handler.setLevel(level) so that users can change the level via logger.setLevel later
    formatter = logging.Formatter(
        "%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    _logger = logging.getLogger("doraemon_logger")
    _logger.setLevel(level)
    _logger.addHandler(handler)
    return _logger


logger = setup_logger()
