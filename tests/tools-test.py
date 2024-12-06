import os
import sys
import shutil
from pprint import pprint
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools import (
    AboutFriends,
    GithubTrending,
    RemoveImageBackground,
    ImageGen,
    TODO,
    TreasureBag
    )
from settings import REPO_PATH,WORK_DIR,DEFAULT_MEMORY_CFG


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
    tool = TODO()
    pprint(tool.call(params))

def test_treasure_bag(params):
    tool = TreasureBag()
    pprint(tool.call(params))


if __name__ == "__main__":
    shutil.rmtree(WORK_DIR, ignore_errors=True)
    # test_about_friends({'query': '大雄有什么糗事吗'})

    # test_github_trending({'language': 'c++'})

    # test_image_gen({
    #     "prompt":"pandas playing on the beach",
    #     "resolution":"512*512"
    # })

    # test_rm_image_background({'img_path': os.path.join(REPO_PATH,"data/tools/image/rm-img-bg-test.jpg")})

    test_todo({"operation":"添加","item":"上传到Github"})
    test_todo({"operation":"查看"})
    test_todo({"operation":"完成","item":"传到Github了"})
    test_todo({"operation":"查看"})

    test_treasure_bag({"tool":"时光机"})
