import os
import json
from rembg import remove
from typing import Union

from tools.base import BaseTool, register_tool
from utils.utils import (
    get_save_path,
    save_image_to_file,
    is_http_url,
    save_url_to_local_work_dir,
)

# Downloading data from 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx' to file 'C:\Users\ethel\.u2net\u2net.onnx'.


@register_tool("RemoveImageBackground")
class RemoveImageBackground(BaseTool):
    description = (
        "去除图像背景，输入需要去除背景的图片路径或链接，返回去除背景后的图片路径。"
    )
    name = "RemoveImageBackground"
    parameters: list = [
        {
            "name": "img_path",
            "description": "需要去除背景的图片路径或链接",
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
        # 1. 检查参数格式
        try:
            params = self._verify_json_format_args(params)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

        # 2. 解析参数
        img_path = params.get("img_path", "")

        # 2.1 检查参数是否为空
        if img_path.strip() == "":
            return json.dumps(
                {"error": f"请输入图片路径或链接。"},
                ensure_ascii=False,
            )

        # 2.2 如果图片是网络路径，需要先下载到本地
        if is_http_url(img_path):
            url = img_path
            try:
                img_url = img_path
                img_extension = os.path.splitext(img_url)[1].lower()
                if img_extension:
                    if img_extension in [".jpg", ".jpeg", ".bmp", ".webp"]:
                        img_type = img_extension[1:]  # 去掉扩展名前面的点
                else:
                    img_type = "png"  # 默认使用png格式

                img_path = get_save_path(type=img_type)
                save_url_to_local_work_dir(img_url, img_path)
            except Exception as e:
                return json.dumps(
                    {"error": f"图片链接 {url} 不存在或无法访问。"},
                    ensure_ascii=False,
                )

        # 2.3 如果图片是本地路径，需要判断是否存在
        if not os.path.exists(img_path):
            return json.dumps(
                {"error": f"图片路径 {img_path} 不存在。"},
                ensure_ascii=False,
            )

        # 3. 去除背景
        try:
            # 3.1 读取图片
            with open(img_path, "rb") as img:
                input_image = img.read()

            # 3.2 去除背景
            output_image = remove(input_image)

            # 3.3 输出保存
            output_path = get_save_path(type="png")
            save_image_to_file(output_image, output_path)

            return json.dumps({"image": output_path}, ensure_ascii=False)
        except Exception as e:
            return json.dumps(
                {"error": str(e)},
                ensure_ascii=False,
            )
