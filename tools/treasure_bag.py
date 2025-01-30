import os
import json
from typing import Optional, Dict, Union

from tools.base import BaseTool, register_tool
from settings import REPO_PATH


@register_tool("TreasureBag")
class TreasureBag(BaseTool):
    description = "哆啦A梦的百宝袋，里面有任意门、竹蜻蜓、放大灯、记忆面包、缩小灯和时光机。输入需要取出的道具，返回道具的使用方法和图片。"
    name = "TreasureBag"
    parameters: list = [
        {
            "name": "tool",
            "description": "想要取出的道具，选项有[任意门, 竹蜻蜓, 放大灯, 记忆面包, 缩小灯, 时光机]。其中，任意门可以到达想去的任意地方，竹蜻蜓可以在天空中飞行，放大灯可以放大物体，记忆面包可以帮助记忆，缩小灯可以缩小物体，时光机可以穿越时间和空间。",
            "required": True,
            "type": "string",
        }
    ]

    def __init__(self, cfg: Optional[Dict] = None, **kwargs):
        super().__init__(cfg)
        self.tools_map = {
            "任意门": "anywhere_door",
            "竹蜻蜓": "bamboo_copter",
            "放大灯": "larger_light",
            "记忆面包": "memory_bread",
            "缩小灯": "smaller_light",
            "时光机": "time_machine",
        }

    def call(self, params: Union[str, dict], **kwargs) -> str:
        """
        Call the treasure bag tool.

        Args:
            params (Union[str, dict]): The input parameters.

        Returns:
            str: The output of the treasure bag tool.
        """
        # 1. 检查参数格式
        try:
            params = self._verify_json_format_args(params)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

        tool = params.get("tool", "")
        tool = tool.strip()
        if tool not in self.tools_map:
            return json.dumps({"error": f"{tool} 不在百宝袋中。"}, ensure_ascii=False)

        # 2. 读取工具信息
        try:
            tool_path = os.path.join(
                REPO_PATH, f"assets/tools/content/{self.tools_map[tool]}.json"
            )
            with open(tool_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            use = data["use"]
            image_path = os.path.join(REPO_PATH, data["image_path"])
            return json.dumps({"text": use, "image": image_path}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
