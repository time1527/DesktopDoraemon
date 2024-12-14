import json
from rembg import remove
from typing import Union

from tools.base import BaseTool, register_tool
from utils.utils import get_save_path, save_image_to_file

# Downloading data from 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx' to file 'C:\Users\ethel\.u2net\u2net.onnx'.


@register_tool("RemoveImageBackground")
class RemoveImageBackground(BaseTool):
    description = "去除图像背景，输入需要去除背景的图片路径，返回去除背景后的图片路径。"
    name = "RemoveImageBackground"
    parameters: list = [
        {
            "name": "img_path",
            "description": "需要去除背景的图片路径",
            "required": True,
            "type": "string",
        }
    ]

    def call(self, params: Union[str, dict], **kwargs) -> str:
        """
        Call the RemoveImageBackground tool.

        Args:
            params (Union[str, dict]): The parameters for the RemoveImageBackground tool.

        Returns:
            str: The results of the RemoveImageBackground tool.
        """
        # 1. 检验参数是否符合要求
        params = self._verify_json_format_args(params)
        img_path = params.get("img_path", "")

        if img_path.strip() == "":
            return "请输入图片路径。"

        # 2. 读取图片
        with open(img_path, "rb") as img:
            input_image = img.read()

        # 3. 去除背景
        output_image = remove(input_image)

        # 4. 输出保存
        output_path = get_save_path(type="png")
        save_image_to_file(output_image, output_path)
        return json.dumps({"image": output_path}, ensure_ascii=False)
