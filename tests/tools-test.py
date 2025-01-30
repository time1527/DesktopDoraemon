import os
import sys
import shutil
from pprint import pprint

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from tools import (
    DoraemonMemory,
    GithubTrending,
    RemoveImageBackground,
    ImageGen,
    ToDo,
    TreasureBag,
)
from settings import REPO_PATH, WORK_DIR, DEFAULT_MEMORY_CFG


def test_about_friends(params, **kwargs):
    tool = DoraemonMemory()
    pprint(tool.call(params, **kwargs))


def test_github_trending(params, **kwargs):
    tool = GithubTrending()
    pprint(tool.call(params, **kwargs))


def test_rm_image_background(params, **kwargs):
    tool = RemoveImageBackground()
    pprint(tool.call(params, **kwargs))


def test_image_gen(params, **kwargs):
    tool = ImageGen()
    pprint(tool.call(params, **kwargs))


def test_todo(params, **kwargs):
    tool = ToDo()
    pprint(tool.call(params, **kwargs))


def test_treasure_bag(params, **kwargs):
    tool = TreasureBag()
    pprint(tool.call(params, **kwargs))


if __name__ == "__main__":
    # shutil.rmtree(WORK_DIR, ignore_errors=True)

    test_about_friends({"query": "静香喜欢吃火锅吗"})

    test_github_trending({"language": "c++", "date_range": ""})
    test_github_trending({"language": "pytorch", "date_range": "本日"})
    test_github_trending({"language": "java"})

    test_image_gen(
        {
            "prompt": "夜晚的城市天际线，高楼大厦灯火辉煌，闪烁的霓虹灯点缀其间，街道上车辆行人穿梭，展现城市的繁华与活力",
            "width": 2048,
            "height": 2048,
        },
        # **{"simulate": True}
    )

    test_rm_image_background(
        '{"img_path": "https://image.pollinations.ai/prompt/%E5%A4%A7%E7%86%8A%E7%8C%AB"}'
    )

    test_todo(
        {"operation": "添加", "item": "agent微调"},
        # **{"simulate": True}
    )
    test_todo({"operation": "查看"})
    test_todo({"operation": "添加", "item": "学习使用新手机"})
    test_todo(
        {"operation": "完成", "item": "看电影"},
        #   **{"simulate": True}
    )

    test_treasure_bag({"tool": "时光机"})
