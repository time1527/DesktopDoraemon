# copy and modify from:
# https://github.com/llq20133100095/DeskTopPet/blob/main/talk_show.py

import os
import pygame
import requests
from PyQt5 import QtGui
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal
from threading import Thread
from typing import List, Union

from clients.bubble_message import BubbleMessage, ChatWidget
from utils.schema import ContentItem, MessageType, MessageRole, Message
from utils.utils import is_image, is_file, get_save_path
from log import logger
from settings import REPO_PATH, TTS


class GenerateReplyThread(QThread):
    replyGenerated = pyqtSignal(Message, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        output, action = self.parent.generate()
        self.replyGenerated.emit(output, action)


class BaseClient(QWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)

        # 头像
        self.send_avatar = os.path.join(REPO_PATH, "assets/ui/chat/head2.jpeg")
        self.receive_avatar = os.path.join(REPO_PATH, "assets/ui/chat/head1.jpg")

        # 聊天背景 TODO：怎么铺满窗口
        palette = QtGui.QPalette()
        self.bg = QtGui.QPixmap(
            os.path.join(REPO_PATH, "assets/ui/chat/background.jpg")
        )
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(self.bg))
        self.setPalette(palette)

        self.resize(800, 600)

        self.history = []
        self.init_ui()
        self.init_model()

    def add_history(self, bmsg: BubbleMessage) -> None:
        """Convert BubbleMessage to Message and add to history"""
        role = bmsg.role
        type = bmsg.type

        if type == MessageType.AUDIO:
            return
        msg_ci = ContentItem(
            text=bmsg.content if type == MessageType.TEXT else None,
            image=bmsg.content if type == MessageType.IMAGE else None,
            file=bmsg.content if type == MessageType.FILE else None,
        )

        if len(self.history) == 0:
            self.history.append(Message(role=role, content=[msg_ci]))
            return

        # 如果这条消息和上条消息都是同一个人发送：合并到上一条消息
        last_msg = self.history[-1]
        last_role = last_msg.role

        if role == last_role:
            self.history[-1].content.append(msg_ci)
        else:
            self.history.append(Message(role=role, content=[msg_ci]))

    def init_ui(self) -> None:
        """load ui"""
        self.msg_show_frame = ChatWidget()

        # 初始化时展示一些对话
        bubble_message = BubbleMessage(
            "你好，我是哆啦A梦~✨✨✨",
            self.receive_avatar,
            type=MessageType.TEXT,
            role=MessageRole.SYSTEM,
        )
        self.msg_show_frame.add_message_item(bubble_message)

        bubble_message = BubbleMessage(
            os.path.join(REPO_PATH, "assets/ui/chat/head1.jpg"),
            self.receive_avatar,
            type=MessageType.IMAGE,
            role=MessageRole.SYSTEM,
        )
        self.msg_show_frame.add_message_item(bubble_message)

        # 消息输入框
        self.msg_input_frame = QLineEdit(self)
        self.msg_input_frame.setPlaceholderText("请输入发送内容")
        # 设置可拉伸
        self.msg_input_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 按钮
        self.msg_send_button = QPushButton("发送", self)
        self.msg_send_button.setFont(QFont("微软雅黑", 10, QFont.Bold))
        self.file_select_button = QPushButton("打开", self)
        self.file_select_button.setFont(QFont("微软雅黑", 10, QFont.Bold))
        # 设置固定大小
        self.msg_send_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.file_select_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # 获取按钮的高度，并设置为消息输入框的最大高度
        button_height = (
            self.msg_send_button.sizeHint().height()
            + self.file_select_button.sizeHint().height()
        )
        self.msg_input_frame.setMaximumHeight(button_height)

        # 整个程序 layout: 上边是 msg_show layout，下边是 msg_input layout
        self.layout = QVBoxLayout()
        self.msg_show_layout = QVBoxLayout()
        self.msg_input_layout = QHBoxLayout()
        self.layout.addLayout(self.msg_show_layout)
        self.layout.addLayout(self.msg_input_layout)

        # buttons layout: 上面是 file_select_button，下面是 msg_send_button
        self.buttons = QVBoxLayout()
        self.buttons.addWidget(self.file_select_button)
        self.buttons.addWidget(self.msg_send_button)
        self.msg_show_layout.addWidget(self.msg_show_frame)

        # msg_input layout: 左边是 msg_input，右边是 buttons
        self.msg_input_layout.addWidget(self.msg_input_frame)
        self.msg_input_layout.addLayout(self.buttons)
        self.setLayout(self.layout)

        # 设置拉伸因子，让 msg_show_frame 可拉伸
        self.msg_show_layout.setStretchFactor(self.msg_show_frame, 1)
        self.add_open_btn()
        self.add_send_btn()

    def init_model(self):
        """load model"""
        return NotImplementedError

    def generate(self):
        """generate response and action"""
        return NotImplementedError

    def send_msg(self):
        """send message and get response"""
        # 注意: 这里默认文本消息发送后，llm生成回复
        # 因此：有图像/文件要发送，需要先发送，最后再发文本

        # 发送消息
        msg = self.msg_input_frame.text()
        bubble_message = BubbleMessage(
            msg, self.send_avatar, type=MessageType.TEXT, role=MessageRole.USER
        )
        self.msg_show_frame.add_message_item(bubble_message)
        self.add_history(bubble_message)

        if msg.upper() == "Q":
            self.destroy()
        self.msg_input_frame.clear()

        # 创建一个新线程来生成回复
        # 问题：用户发送消息后，llm生成回复的时间过长，导致界面卡死
        # 解决：将生成回复的任务放到新线程中执行，避免阻塞主线程
        thread = GenerateReplyThread(self)
        thread.replyGenerated.connect(self.display_reply)
        thread.start()

    def display_reply(self, output, action):
        # 将回复转换为BubbleMessage对象
        bmsgs = self.message_to_bubble_messages(output, action)
        for bmsg in bmsgs:
            self.msg_show_frame.add_message_item(bmsg)
            self.add_history(bmsg)

    def open_file(self):
        """open and send file/image"""
        path = QFileDialog.getOpenFileName(self, "Open File", "~")
        # ('G:/DesktopDoraemon/clients/base_client.py', 'All Files (*)')

        if is_image(path[0]):
            bubble_message = BubbleMessage(
                path[0], self.send_avatar, type=MessageType.IMAGE, role=MessageRole.USER
            )
            self.msg_show_frame.add_message_item(bubble_message)
            self.add_history(bubble_message)
        elif is_file(path[0]):
            bubble_message = BubbleMessage(
                path[0], self.send_avatar, type=MessageType.FILE, role=MessageRole.USER
            )
            self.msg_show_frame.add_message_item(bubble_message)
            self.add_history(bubble_message)
        else:
            raise ValueError("不支持的文件类型")

    def btn_send(self):
        self.msg_send_button.clicked.connect(self.send_msg)

    def add_open_btn(self):
        self.file_select_button.clicked.connect(self.open_file)

    def add_send_btn(self):
        Thread(target=self.btn_send).start()

    def closeEvent(self, event):
        self.destroy()

    def message_to_bubble_messages(
        self, message: Message, action: str = ""
    ) -> Union[List[BubbleMessage], BubbleMessage]:
        """Convert Message to BubbleMessage"""
        bmsgs = []
        role = message.role
        avatar = self.send_avatar if role == MessageRole.USER else self.receive_avatar
        content = message.content
        if isinstance(content, str):  # only text
            bmsgs.append(
                BubbleMessage(content, avatar, type=MessageType.TEXT, role=role)
            )
            if TTS and role == MessageRole.ASSISTANT:
                if action == "TreasureBag":
                    self.tsbg_bgm()
                elif action not in [
                    "GithubTrending",
                    "RemoveImageBackground",
                    "ImageGen",
                ]:
                    save_path = get_save_path("wav")
                    self.tts(content, save_path)
                    if os.path.exists(save_path):
                        bmsgs.append(
                            BubbleMessage(
                                save_path, avatar, type=MessageType.AUDIO, role=role
                            )
                        )
        elif isinstance(content, list):  # multiple content
            for item in message.content:
                k, v = item.get_type_and_value()
                bmsgs.append(BubbleMessage(v, avatar, type=k, role=role))
                if TTS and role == MessageRole.ASSISTANT and k == MessageType.TEXT:
                    if action == "TreasureBag":
                        self.tsbg_bgm()
                    elif action not in [
                        "GithubTrending",
                        "RemoveImageBackground",
                        "ImageGen",
                    ]:
                        save_path = get_save_path("wav")
                        self.tts(v, save_path)
                        if os.path.exists(save_path):
                            bmsgs.append(
                                BubbleMessage(
                                    save_path, avatar, type=MessageType.AUDIO, role=role
                                )
                            )
        else:
            raise ValueError("不支持的消息类型")
        return bmsgs

    def tts(self, text: str, save_path: str):
        """text to speech"""
        # 构造请求数据
        payload = {
            "text": text,  # str.(required) text to be synthesized
            "text_lang": "zh",  # str.(required) language of the text to be synthesized
            "ref_audio_path": os.path.join(
                REPO_PATH, "assets/tts/ref1.wav"
            ),  # str.(required) reference audio path
            "aux_ref_audio_paths": [
                os.path.join(REPO_PATH, "assets/tts/ref2.wav"),
                os.path.join(REPO_PATH, "assets/tts/ref3.wav"),
            ],  # list.(optional) auxiliary reference audio paths for multi-speaker tone fusion
            "prompt_text": "初次见面，你们好，我叫做哆啦A梦，今后要麻烦你们多多照顾了，请多指教。",  # str.(optional) prompt text for the reference audio
            "prompt_lang": "zh",  # str.(required) language of the prompt text for the reference audio
            "top_k": 15,  # int. top k sampling
            "top_p": 1,  # float. top p sampling
            "temperature": 1,  # float. temperature for sampling
            "text_split_method": "cut5",  # str. text split method, see text_segmentation_method.py for details.
            "batch_size": 1,  # int. batch size for inference
            "batch_threshold": 0.75,  # float. threshold for batch splitting.
            "split_bucket": True,  # bool. whether to split the batch into multiple buckets.
            "speed_factor": 1,  # float. control the speed of the synthesized audio.
            "streaming_mode": False,  # bool. whether to return a streaming response.
            "seed": -1,  # int. random seed for reproducibility.
            "parallel_infer": True,  # bool. whether to use parallel inference.
            "repetition_penalty": 1.15,  # float. repetition penalty for T2S model.
            "media_type": "wav",
        }

        try:
            url = "http://127.0.0.1:9880/tts"
            # 文件保存路径
            output_audio_file = save_path  # 根据实际音频类型调整后缀

            # 发送 POST 请求
            response = requests.post(url, json=payload)

            # 检查响应状态码
            if response.status_code == 200:
                # 将音频数据保存到文件
                with open(output_audio_file, "wb") as f:
                    f.write(response.content)
                print(f"Audio saved to {output_audio_file}")
            else:
                print(f"Request failed with status code: {response.status_code}")
                print("Response Content:", response.text)

        except Exception as e:
            print("An error occurred:", str(e))

    def tsbg_bgm(self):
        pygame.mixer.init()
        pygame.mixer.music.load(
            os.path.join(
                REPO_PATH,
                "assets/tts/哆啦A梦拿出道具音效_耳聆网_[声音ID：37762].mp3",
            )
        )
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():  # 等待播放结束
            pass
