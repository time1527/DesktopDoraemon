import os
import sys
from pprint import pprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from memory.base import BaseMemory
from settings import DEFAULT_MEMORY_CFG


def test_memory():
    memory = BaseMemory(DEFAULT_MEMORY_CFG)
    query_list = ["大雄喜欢吃什么啊", "哆啦美是谁", "胖虎和静香谁更适合参加选秀比赛"]
    for query in query_list:
        result = memory.query(query, num_return=2)
        pprint(result)


if __name__ == "__main__":
    test_memory()
