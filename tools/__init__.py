from .base import TOOL_REGISTRY, register_tool, BaseTool
from .about_friends import AboutFriends
from .github_trend import GithubTrending
from .image_gen import ImageGen
from .rm_image_background import RemoveImageBackground
from .todo import TODO
from .treasure_bag import TreasureBag


__all__ = [
    "AboutFriends",
    "GithubTrending",
    "ImageGen",
    "RemoveImageBackground",
    "TODO",
    "TreasureBag",
    "BaseTool",
    "register_tool",
    "TOOL_REGISTRY",
]
