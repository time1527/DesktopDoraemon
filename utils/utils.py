# copy and modify from:
# https://github.com/QwenLM/Qwen-Agent/blob/main/qwen_agent/utils/utils.py

import re
import os
import sys
import json
import copy
import uuid
import time
import json5
import urllib
import shutil
import requests
import traceback
from PIL import Image
from pydantic import BaseModel
from typing import List, Literal, Optional, Tuple, Union

from utils.schema import (
    ContentItem,
    Message,
    MessageRole,
    MessageType,
    DEFAULT_SYSTEM_PROMPT,
)
from settings import WORK_DIR
from log import logger


class PydanticJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)


def has_chinese_chars(data) -> bool:
    """Check if the input data contains Chinese characters."""
    # 将输入的数据转换为字符串
    text = f"{data}"
    # 使用正则表达式查找中文字符，并根据结果判断是否包含中文字符
    return len(re.findall(r"[\u4e00-\u9fff]+", text)) > 0


def get_basename_from_url(path_or_url: str) -> str:
    if re.match(r"^[A-Za-z]:\\", path_or_url):
        # "C:\\a\\b\\c" -> "C:/a/b/c"
        path_or_url = path_or_url.replace("\\", "/")

    # "/mnt/a/b/c" -> "c"
    # "https://github.com/here?k=v" -> "here"
    # "https://github.com/" -> ""
    basename = urllib.parse.urlparse(path_or_url).path
    basename = os.path.basename(basename)
    basename = urllib.parse.unquote(basename)
    basename = basename.strip()

    # "https://github.com/" -> "" -> "github.com"
    if not basename:
        basename = [x.strip() for x in path_or_url.split("/") if x.strip()][-1]

    return basename


def json_dumps_compact(obj: dict, ensure_ascii=False, indent=None, **kwargs) -> str:
    return json.dumps(
        obj, ensure_ascii=ensure_ascii, indent=indent, cls=PydanticJSONEncoder, **kwargs
    )


def print_traceback(is_error: bool = True):
    tb = "".join(traceback.format_exception(*sys.exc_info(), limit=3))
    if is_error:
        logger.error(tb)
    else:
        logger.warning(tb)


def json_loads(text: str) -> dict:
    text = text.strip("\n")
    if text.startswith("```") and text.endswith("\n```"):
        text = "\n".join(text.split("\n")[1:-1])
    try:
        return json.loads(text)
    except json.decoder.JSONDecodeError as json_err:
        try:
            return json5.loads(text)
        except ValueError:
            raise json_err


def save_url_to_local_work_dir(url: str, save_dir: str, save_filename: str = "") -> str:
    if not save_filename:
        save_filename = get_basename_from_url(url)
    new_path = os.path.join(save_dir, save_filename)
    if os.path.exists(new_path):
        os.remove(new_path)
    logger.info(f"Downloading {url} to {new_path}...")
    start_time = time.time()
    if not is_http_url(url):
        url = sanitize_chrome_file_path(url)
        shutil.copy(url, new_path)
    else:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(new_path, "wb") as file:
                file.write(response.content)
        else:
            raise ValueError(
                "Can not download this file. Please check your network or the file link."
            )
    end_time = time.time()
    logger.info(
        f"Finished downloading {url} to {new_path}. Time spent: {end_time - start_time} seconds."
    )
    return new_path


def is_http_url(path_or_url: str) -> bool:
    if path_or_url.startswith("https://") or path_or_url.startswith("http://"):
        return True
    return False


def sanitize_chrome_file_path(file_path: str) -> str:
    if os.path.exists(file_path):
        return file_path

    # Dealing with "file:///...":
    new_path = urllib.parse.urlparse(file_path)
    new_path = urllib.parse.unquote(new_path.path)
    new_path = sanitize_windows_file_path(new_path)
    if os.path.exists(new_path):
        return new_path

    return sanitize_windows_file_path(file_path)


def sanitize_windows_file_path(file_path: str) -> str:
    # For Linux and macOS.
    if os.path.exists(file_path):
        return file_path

    # For native Windows, drop the leading '/' in '/C:/'
    win_path = file_path
    if win_path.startswith("/"):
        win_path = win_path[1:]
    if os.path.exists(win_path):
        return win_path

    # For Windows + WSL.
    if re.match(r"^[A-Za-z]:/", win_path):
        wsl_path = f"/mnt/{win_path[0].lower()}/{win_path[3:]}"
        if os.path.exists(wsl_path):
            return wsl_path

    # For native Windows, replace / with \.
    win_path = win_path.replace("/", "\\")
    if os.path.exists(win_path):
        return win_path

    return file_path


def merge_generate_cfgs(
    base_generate_cfg: Optional[dict], new_generate_cfg: Optional[dict]
) -> dict:
    # 使用new_generate_cfg补充stop或覆盖/添加原cfg
    generate_cfg: dict = copy.deepcopy(base_generate_cfg or {})
    if new_generate_cfg:
        for k, v in new_generate_cfg.items():
            if k == "stop":
                stop = generate_cfg.get("stop", [])
                stop = stop + [s for s in v if s not in stop]
                generate_cfg["stop"] = stop
            else:
                generate_cfg[k] = v
    return generate_cfg


def format_as_multimodal_message(
    msg: Message,
    add_upload_info: bool,
    lang: Literal["auto", "en", "zh"] = "auto",
) -> Message:
    assert msg.role in (
        MessageRole.USER,
        MessageRole.ASSISTANT,
        MessageRole.SYSTEM,
        MessageRole.FUNCTION,
    )
    content: List[ContentItem] = []

    if isinstance(msg.content, str):  # if text content
        if msg.content:
            content = [ContentItem(text=msg.content)]
    elif isinstance(msg.content, list):  # if multimodal content
        files = []
        for item in msg.content:
            k, v = item.get_type_and_value()
            if k == "text":
                content.append(ContentItem(text=v))
            if k == "image":
                content.append(item)
            if k in ("file", "image"):
                # Move 'file' out of 'content' since it's not natively supported by models
                files.append(v)
        if (
            add_upload_info
            and files
            and (msg.role in (MessageRole.SYSTEM, MessageRole.USER))
        ):
            if lang == "auto":
                has_zh = has_chinese_chars(msg)
            else:
                has_zh = lang == "zh"
            upload = []
            # for f in [get_basename_from_url(f) for f in files]:
            for f in files:
                if is_image(f):
                    if has_zh:
                        upload.append(f"![图片]({f})")
                    else:
                        upload.append(f"![image]({f})")
                else:
                    if has_zh:
                        upload.append(f"[文件]({f})")
                    else:
                        upload.append(f"[file]({f})")
            upload = " ".join(upload)
            if has_zh:
                upload = f"（上传了 {upload}）\n\n"
            else:
                upload = f"(Uploaded {upload})\n\n"

            # Check and avoid adding duplicate upload info
            upload_info_already_added = False
            for item in content:
                if item.text and (upload in item.text):
                    upload_info_already_added = True

            if not upload_info_already_added:
                content = [ContentItem(text=upload)] + content
            # [ContentItem({'text': '你好'}),
            # ContentItem({'image': 'G:\\DesktopDoraemon\\data\tools\\image\rm-img-bg-test.jpg'})]
            # ->
            # [ContentItem({'text': '（上传了 ![图片](imagem-img-bg-test.jpg)）\n\n'}),
            # ContentItem({'text': '你好'}),
            # ContentItem({'image': 'G:\\DesktopDoraemon\\data\tools\\image\rm-img-bg-test.jpg'})]
    else:
        raise TypeError
    msg = Message(
        role=msg.role,
        content=content,
        name=msg.name if msg.role == MessageRole.FUNCTION else None,
        function_call=msg.function_call,
    )
    return msg


def format_as_text_message(
    msg: Message,
    add_upload_info: bool,
    lang: Literal["auto", "en", "zh"] = "auto",
) -> Message:
    # [ContentItem({'text': '你好'}),
    # ContentItem({'image': 'G:\\DesktopDoraemon\\data\tools\\image\rm-img-bg-test.jpg'})]
    # format_as_multimodal_message->
    # [ContentItem({'text': '（上传了 ![图片](imagem-img-bg-test.jpg)）\n\n'}),
    # ContentItem({'text': '你好'}),
    # ContentItem({'image': 'G:\\DesktopDoraemon\\data\tools\\image\rm-img-bg-test.jpg'})]
    msg = format_as_multimodal_message(msg, add_upload_info=add_upload_info, lang=lang)
    text = ""
    for item in msg.content:
        if item.type == MessageType.TEXT:
            text += item.value
    msg.content = text
    # ->
    # [ContentItem({'text': '（上传了![图片](imagem-img-bg-test.jpg)）\n\n你好'})]
    return msg


def extract_text_from_message(
    msg: Message,
    add_upload_info: bool,
    lang: Literal["auto", "en", "zh"] = "auto",
) -> str:
    if isinstance(msg.content, list):
        text = format_as_text_message(
            msg, add_upload_info=add_upload_info, lang=lang
        ).content
    elif isinstance(msg.content, str):
        text = msg.content
    else:
        raise TypeError(
            f"List of str or str expected, but received {type(msg.content).__name__}."
        )
    return text.strip()


def has_chinese_messages(
    messages: List[Union[Message, dict]],
    check_roles: Tuple[str] = (MessageRole.SYSTEM, MessageRole.USER),
) -> bool:
    for m in messages:
        if m["role"] in check_roles:
            if has_chinese_chars(m["content"]):
                return True
    return False


def is_image(path_or_url: str) -> bool:
    filename = get_basename_from_url(path_or_url).lower()
    for ext in ["jpg", "jpeg", "png", "webp"]:
        if filename.endswith(ext):
            return True
    return False


def save_image_to_file(image: Image, path: str) -> None:
    with open(path, "wb") as output:
        output.write(image)


def get_save_path(type: str) -> str:
    os.makedirs(WORK_DIR, exist_ok=True)
    path = f"{int(time.time())}-{uuid.uuid4().int}.{type}"
    return os.path.join(WORK_DIR, path)


def build_text_completion_prompt(
    messages: List[Message],
    allow_special: bool = False,
    default_system: str = DEFAULT_SYSTEM_PROMPT,
) -> str:
    im_start = "<|im_start|>"
    im_end = "<|im_end|>"

    if messages[0].role == MessageRole.SYSTEM:
        sys = messages[0].content
        assert isinstance(sys, str)
        prompt = f"{im_start}{MessageRole.SYSTEM}\n{sys}{im_end}"
        messages = messages[1:]
    else:
        prompt = f"{im_start}{MessageRole.SYSTEM}\n{default_system}{im_end}"

    # Make sure we are completing the chat in the tone of the assistant
    if messages[-1].role != MessageRole.ASSISTANT:
        messages = messages + [Message(MessageRole.ASSISTANT, "")]

    for msg in messages:
        assert isinstance(msg.content, str)
        content = msg.content
        if allow_special:
            assert msg.role in (
                MessageRole.USER,
                MessageRole.ASSISTANT,
                MessageRole.SYSTEM,
                MessageRole.FUNCTION,
            )
            if msg.function_call:
                assert msg.role == MessageRole.ASSISTANT
                tool_call = msg.function_call.arguments
                try:
                    tool_call = {
                        "name": msg.function_call.name,
                        "arguments": json.loads(tool_call),
                    }
                    tool_call = json.dumps(tool_call, ensure_ascii=False, indent=2)
                except json.decoder.JSONDecodeError:
                    tool_call = (
                        '{"name": "'
                        + msg.function_call.name
                        + '", "arguments": '
                        + tool_call
                        + "}"
                    )
                if content:
                    content += "\n"
                content += f"<tool_call>\n{tool_call}\n</tool_call>"
        else:
            assert msg.role in (MessageRole.USER, MessageRole.ASSISTANT)
            assert msg.function_call is None
        prompt += f"\n{im_start}{msg.role}\n{content}{im_end}"

    assert prompt.endswith(im_end)
    prompt = prompt[: -len(im_end)]
    return prompt


def get_file_type(
    path: str,
) -> Literal[
    "json",
    "jsonl",
    "md",
    "pdf",
    "docx",
    "pptx",
    "txt",
    "html",
    "csv",
    "tsv",
    "xlsx",
    "xls",
    "unk",
]:
    f_type = get_basename_from_url(path).split(".")[-1].lower()
    if f_type in [
        "json",
        "jsonl",
        "md",
        "pdf",
        "docx",
        "pptx",
        "txt",
        "csv",
        "tsv",
        "xlsx",
        "xls",
    ]:
        # Specially supported file types
        return f_type

    if is_http_url(path):
        # The HTTP header information for the response is obtained by making a HEAD request to the target URL,
        # where the Content-type field usually indicates the Type of Content to be returned
        content_type = get_content_type_by_head_request(path)
        if "application/pdf" in content_type:
            return "pdf"
        elif "application/msword" in content_type:
            return "docx"

        # Assuming that the URL is HTML by default,
        # because the file downloaded by the request may contain html tags
        return "html"
    else:
        # Determine by reading local HTML file
        try:
            content = read_text_from_file(path)
        except Exception:
            print_traceback()
            return "unk"

        if contains_html_tags(content):
            return "html"
        else:
            return "txt"


def get_content_type_by_head_request(path: str) -> str:
    try:
        response = requests.head(path, timeout=5)
        content_type = response.headers.get("Content-Type", "")
        return content_type
    except requests.RequestException:
        return "unk"


def save_text_to_file(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(text)


def read_text_from_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as file:
            file_content = file.read()
    except UnicodeDecodeError:
        print_traceback(is_error=False)
        from charset_normalizer import from_path

        results = from_path(path)
        file_content = str(results.best())
    return file_content


def contains_html_tags(text: str) -> bool:
    pattern = r"<(p|span|div|li|html|script)[^>]*?"
    return bool(re.search(pattern, text))


def is_file(path: str) -> bool:
    return get_file_type(path) != "unk"


def extract_markdown_urls(md_text: str) -> List[str]:
    pattern = r"!?\[[^\]]*\]\(([^\)]+)\)"
    urls = re.findall(pattern, md_text)
    return urls


def extract_final_answer(text: str) -> str:
    pattern = re.compile(r"\nFinal Answer:(.*)", re.DOTALL)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    else:
        return text


def extract_observation(text: str) -> str:
    pattern = re.compile(r"\nObservation:(.*?)\nThought", re.DOTALL)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    else:
        return ""


def save_url_to_local_work_dir(url: str, save_filename: str = "") -> str:
    if not save_filename:
        save_filename = get_basename_from_url(url)

    if os.path.abspath(save_filename).startswith(os.path.abspath(WORK_DIR)):
        new_path = save_filename
    else:
        new_path = os.path.join(WORK_DIR, save_filename)

    if os.path.exists(new_path):
        os.remove(new_path)
    logger.info(f"Downloading {url} to {new_path}...")
    start_time = time.time()
    if not is_http_url(url):
        url = sanitize_chrome_file_path(url)
        shutil.copy(url, new_path)
    else:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(new_path, "wb") as file:
                file.write(response.content)
        else:
            raise ValueError(
                "Can not download this file. Please check your network or the file link."
            )
    end_time = time.time()
    logger.info(
        f"Finished downloading {url} to {new_path}. Time spent: {end_time - start_time} seconds."
    )
    return new_path
