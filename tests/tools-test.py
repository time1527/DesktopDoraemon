import os
import sys
import shutil
from pprint import pprint

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from tools import (
    AboutFriends,
    GithubTrending,
    RemoveImageBackground,
    ImageGen,
    ToDo,
    TreasureBag,
)
from settings import REPO_PATH, WORK_DIR, DEFAULT_MEMORY_CFG


def test_about_friends(params):
    tool = AboutFriends()
    pprint(tool.call(params))


def test_github_trending(params):
    tool = GithubTrending()
    pprint(tool.call(params))


def test_rm_image_background(params):
    tool = RemoveImageBackground()
    pprint(tool.call(params))


def test_image_gen(params):
    tool = ImageGen()
    pprint(tool.call(params))


def test_todo(params):
    tool = ToDo()
    pprint(tool.call(params))


def test_treasure_bag(params):
    tool = TreasureBag()
    pprint(tool.call(params))


if __name__ == "__main__":
    # shutil.rmtree(WORK_DIR, ignore_errors=True)

    test_about_friends({"query": "大雄有什么糗事吗"})

    # test_github_trending({"language": "c++", "date_range": ""})
    # test_github_trending({"language": "", "date_range": "今日"})
    # test_github_trending({"language": "java"})

    # test_image_gen({"prompt": "pandas playing on the beach", "width": "2048"})

    # test_rm_image_background(
    #     {"img_path": "https://image.pollinations.ai/prompt/%E5%A4%A7%E7%86%8A%E7%8C%AB"}
    # )

    # test_todo({"operation": "添加", "item": "agent微调"})
    # test_todo({"operation": "查看"})
    # test_todo({"operation": "完成", "item": "传到Github了"})
    # test_todo({"operation": "查看"})

    # test_treasure_bag({"tool": "时光机"})
