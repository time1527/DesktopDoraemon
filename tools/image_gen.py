# copy and modify from:
# https://github.com/QwenLM/Qwen-Agent/blob/main/qwen_agent/tools/image_gen.py

import json
import urllib
from typing import Union

from tools.base import BaseTool,register_tool
from utils.utils import get_save_path,save_url_to_local_work_dir


@register_tool('ImageGen')
class ImageGen(BaseTool):
    description = 'AI绘画（图像生成）服务，输入文本描述和图像分辨率，返回根据文本信息绘制的图片路径。'
    name = 'ImageGen'
    parameters = [
        {
            'name': 'prompt',
            'type': 'string',
            'description': '详细描述了希望生成的图像具有什么内容，例如人物、环境、动作等细节描述，使用英文',
            'required': True
        }, 
        {
            'name': 'resolution',
            'type': 'string',
            'description': '格式是 数字*数字，表示希望生成的图像的分辨率大小，选项有[1024*1024, 720*1280, 1280*720]'
        }
    ]

    def call(self, params: Union[str, dict], **kwargs) -> str:
        """"
        call the image gen tool.

        Args:
            params (Union[str, dict]): The input parameters.

        Returns:
            str: The output of the image gen tool.
        """
        # 1. 检验参数是否符合要求
        params = self._verify_json_format_args(params)
        prompt = params.get('prompt',"")

        # TODO:如果有中文，需要翻译或者llm能够将其转换成英文

        # 2. 调用接口
        prompt = urllib.parse.quote(prompt)
        image_url = f'https://image.pollinations.ai/prompt/{prompt}'

        # 3. 保存图片
        image_path = get_save_path(type = "png")
        save_url_to_local_work_dir(image_url,image_path)
        return json.dumps({"image":image_path},ensure_ascii=False)