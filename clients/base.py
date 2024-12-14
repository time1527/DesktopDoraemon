# copy and modify from:
# https://github.com/llq20133100095/DeskTopPet/blob/main/talk_show.py

import os
from PyQt5 import QtGui
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from threading import Thread
from typing import List, Union

from clients.bubble_message import BubbleMessage, ChatWidget
from utils.schema import ContentItem, MessageType, MessageRole, Message
from utils.utils import is_image, is_file
from log import logger
from settings import REPO_PATH


class BaseClient(QWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)

        # 头像
        self.send_avatar = os.path.join(REPO_PATH, "data/ui/chat/head2.jpeg")
        self.receive_avatar = os.path.join(REPO_PATH, "data/ui/chat/head1.jpg")

        # 聊天背景 TODO：怎么铺满窗口
        palette = QtGui.QPalette()
        self.bg = QtGui.QPixmap(os.path.join(REPO_PATH, "data/ui/chat/background.jpg"))
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
            "你好，我是哆啦A梦！",
            self.receive_avatar,
            type=MessageType.TEXT,
            role=MessageRole.SYSTEM,
        )
        self.msg_show_frame.add_message_item(bubble_message)

        bubble_message = BubbleMessage(
            os.path.join(REPO_PATH, "data/ui/chat/head1.jpg"),
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
        """generate response"""
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

        # 生成回复
        output = self.generate()
        bmsgs = self.message_to_bubble_messages(output)
        for bmsg in bmsgs:
            self.msg_show_frame.add_message_item(bmsg)
            self.add_history(bmsg)

        # logger.info(f"current history:{self.history}")

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
        self, message: Message
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
        elif isinstance(content, list):  # multiple content
            for item in message.content:
                k, v = item.get_type_and_value()
                bmsgs.append(BubbleMessage(v, avatar, type=k, role=role))
        else:
            raise ValueError("不支持的消息类型")
        return bmsgs
