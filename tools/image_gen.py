# copy and modify from:
# https://github.com/QwenLM/Qwen-Agent/blob/main/qwen_agent/tools/image_gen.py
# learn from:
# https://github.com/pollinations/pollinations/blob/master/APIDOCS.md

import os
import time
import json
import uuid
import urllib
import random
from typing import Union

from tools.base import BaseTool, register_tool
from utils.utils import get_save_path, save_url_to_local_work_dir


@register_tool("ImageGen")
class ImageGen(BaseTool):
    description = "AI绘画（图像生成）服务，输入文本描述和期望生成的图像的高和宽，返回根据文本信息绘制的图片路径。"
    name = "ImageGen"
    parameters = [
        {
            "name": "prompt",
            "type": "string",
            # prompt* (required): Text description of the image you want to generate. Should be URL-encoded.
            "description": "详细描述了希望生成的图像具有什么内容，例如人物、环境、动作等细节描述",
            "required": True,
        },
        {
            "name": "width",
            "type": "number",
            "description": "格式是 数字，表示希望生成的图像的宽，默认是 1024",
            "required": False,
        },
        {
            "name": "height",
            "type": "number",
            "description": "格式是 数字，表示希望生成的图像的高，默认是 1024",
            "required": False,
        },
    ]

    def call(self, params: Union[str, dict], **kwargs) -> str:
        """ "
        call the image gen tool.

        Args:
            params (Union[str, dict]): The input parameters.

        Returns:
            str: The output of the image gen tool.
        """
        # 1. 检验参数是否符合要求
        try:
            params = self._verify_json_format_args(params)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

        prompt = params.get("prompt")

        if not prompt:
            return json.dumps(
                {"error": "请输入希望生成的图像的文本描述。"}, ensure_ascii=False
            )
        # 没有检查中英文，因为中文也能生成

        width = params.get("width", 1024)
        height = params.get("height", 1024)

        simulate = kwargs.get("simulate", False)
        if simulate:
            return self.simulate_call()
        # 2. 调用接口

        # 固定seed的用处可能在于用户之后的追问，比如要求生成大熊猫图片，没有指定高和宽，返回的是1024x1024
        # 当把图片返回时，用户要求重新生成某一高宽的图片，但这种情况下，
        # prompt相同，seed相同，width和height不同，生成的内容也是不同的
        # eg. https://image.pollinations.ai/prompt/pandas?width=800&height=600&seed=42
        # https://image.pollinations.ai/prompt/pandas?width=600&height=800&seed=42

        # 随机seed：
        seed = random.randint(0, 1000000000)
        prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&seed={seed}"

        # 3. 保存图片
        try:
            image_path = get_save_path(type="png")
            save_url_to_local_work_dir(image_url, image_path)
            return json.dumps({"image": image_path}, ensure_ascii=False)
        except Exception as e:
            return json.dumps(
                {"error": "图像下载或生成出错，请检查网络或尝试重新生成图像。"},
                ensure_ascii=False,
            )

    def simulate_call(self) -> str:
        """
        Returns:
            str: Simulate output of the image gen tool.
        """

        def generate_random_path():
            # 随机选择操作系统类型
            os_type = random.choice(["windows", "linux", "mac"])
            file = f"{int(time.time())}-{uuid.uuid4().int}.png"

            if os_type == "windows":
                # Windows文件夹路径示例（不包括系统盘）
                drive_letter = random.choice("DEFGHIJKLMNOPQRSTUVWXYZ")
                path = f"{drive_letter}:\\{random.choice(['Data', 'Users', 'Files'])}\\{random.choice(['Folder1', 'Folder2', 'Folder3'])}\\{file}"
            elif os_type == "linux":
                # Linux文件夹路径示例
                path = f"/home/{random.choice(['user1', 'user2', 'user3'])}/{random.choice(['Folder1', 'Folder2', 'Folder3'])}/{file}"
            elif os_type == "mac":
                # Mac文件夹路径示例
                path = f"/Users/{random.choice(['user1', 'user2', 'user3'])}/{random.choice(['Folder1', 'Folder2', 'Folder3'])}/{file}"

            return path

        rdn = random.random()
        if rdn < 0.1:
            return json.dumps(
                {"error": "图像下载或生成出错，请检查网络或尝试重新生成图像。"},
                ensure_ascii=False,
            )

        return json.dumps(
            {"image": generate_random_path()},
            ensure_ascii=False,
        )
