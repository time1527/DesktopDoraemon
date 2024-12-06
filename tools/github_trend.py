# learn from: https://deepwisdom.feishu.cn/wiki/KhCcweQKmijXi6kDwnicM0qpnEf

import os
import re
import json
import asyncio
import aiohttp
from typing import Optional,Dict,Union
from bs4 import BeautifulSoup

from tools.base import BaseTool,register_tool
from utils.utils import read_text_from_file
from settings import REPO_PATH


@register_tool('GithubTrending')
class GithubTrending(BaseTool):
    description = "查看今日Github社区趋势，输入编程语言，返回今日Github社区该项编程语言的热门仓库信息。"
    name = 'GithubTrending'
    parameters: list = [
        {
            'name': 'language',
            'description': '编程语言',
            'required': False,
            'type':'string',
            'default': ''
        }
    ]

    def __init__(self, cfg: Optional[Dict] = None):
        super().__init__(cfg)
        self.url = "https://github.com/trending"
        self.show_k = 5
        # languages.txt is cleaned based on: 
        # https://github.com/github-linguist/linguist/blob/master/lib/linguist/languages.yml
        self.languages_list = read_text_from_file(os.path.join(REPO_PATH,"data/tools/content/languages.txt"))

    def call(self, params: Union[str, dict], **kwargs) -> str:
        """
        Call the GithubTrending tool.

        Args:
            params (Union[str, dict]): The parameters for the GithubTrending tool.

        Returns:
            str: The results of the GithubTrending tool.
        """
        # 1. 检验参数是否符合要求
        params = self._verify_json_format_args(params)
        language = params.get('language',"")

        # 2. 获取内容
        try:
            response = asyncio.run(self._get(language))
        except Exception as e:
            return json.dumps({"error":str(e)},ensure_ascii=False)
        
        # 3. 整理内容
        parsed_res = self._parse_results(response)
        return json.dumps({"text":str(parsed_res)},ensure_ascii=False)

    def _parse_results(self, html: str) -> str:
        """
        Parse the html results.
        
        Args:
            html (str): The hmtl content from Github Repository.
        
        Returns:
            str: The parsed Github Repository results.
        """
        soup = BeautifulSoup(html, 'html.parser')

        repositories = []
        show = 0
        for article in soup.select('article.Box-row'):
            show += 1
            if show > self.show_k:break

            repo_info = {}

            # https://b07ofnm9xj7.feishu.cn/wiki/UiQyw79ZOiK5BEkdBjscBwFvnkh
            repo_info['name'] = article.select_one('h2 a').text.strip().replace("\n", "").replace(" ", "")
            repo_info['url'] = "https://github.com" + article.select_one('h2 a')['href'].strip()

            # Description
            description_element = article.select_one('p')
            repo_info['description'] = description_element.text.strip() if description_element else None

            # Language
            language_element = article.select_one('span[itemprop="programmingLanguage"]')
            repo_info['language'] = language_element.text.strip() if language_element else None

            # Stars and Forks
            stars_element = article.select('a.Link--muted')[0]
            forks_element = article.select('a.Link--muted')[1]
            repo_info['stars'] = stars_element.text.strip()
            repo_info['forks'] = forks_element.text.strip()

            # Today's Stars
            today_stars_element = article.select_one('span.d-inline-block.float-sm-right')
            repo_info['today_stars'] = today_stars_element.text.strip() if today_stars_element else None

            repositories.append(repo_info)

        formatted_strings = []
        for item in repositories:
            formatted_item = "\n".join([f"{key}: {value}" for key, value in item.items()])
            formatted_strings.append(formatted_item)
        return "\n".join(formatted_strings)

    async def _get(self,language: str) -> str:
        if len(language):
            # TODO:空格的处理，可能是误触，也可能是需要使用'-'去链接
            ln = language.strip().lower()
            ln = re.sub(r'\s+', '', ln)
            if ln == "cpp":ln = "c++"
            if ln in self.languages_list:
                self.url = f"https://github.com/trending/{ln}?since=daily"
        try:
            async with aiohttp.ClientSession() as client:
                async with client.get(self.url, proxy="http://127.0.0.1:7890") as response:
                # async with client.get(self.url) as response:
                    response.raise_for_status()
                    html = await response.text()
            return html
        except Exception as e:
            return str(e)
        