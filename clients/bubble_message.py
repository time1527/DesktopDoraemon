# copy and modify from:
# https://github.com/LC044/pyqt_component_library/blob/master/bubble_message/bubble_message.py

import os
import time
import pygame

from PIL import Image
from PyQt5 import QtGui
from PyQt5.QtCore import QSize, pyqtSignal, Qt, QThread
from PyQt5.QtGui import QPainter, QFont, QColor, QPixmap, QPolygon, QFontMetrics
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QSpacerItem,
    QScrollArea,
    QScrollBar,
    QPushButton,
    QProgressBar,
)


from utils.schema import MessageRole, MessageType

# TODO：file


class TextMessage(QLabel):
    heightSingal = pyqtSignal(int)

    def __init__(self, text, role=MessageRole.ASSISTANT, parent=None):
        super(TextMessage, self).__init__(text, parent)
        font = QFont("微软雅黑", 12)
        self.setFont(font)
        self.setWordWrap(True)
        self.setMaximumWidth(800)
        self.setMinimumWidth(100)
        self.setMinimumHeight(45)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        if role == MessageRole.USER:
            self.setAlignment(Qt.AlignCenter | Qt.AlignRight)
            self.setStyleSheet(
                """
                background-color:#b2e281;
                border-radius:10px;
                padding:10px;
                """
            )
        else:
            self.setStyleSheet(
                """
                background-color:white;
                border-radius:10px;
                padding:10px;
                """
            )
        font_metrics = QFontMetrics(font)
        rect = font_metrics.boundingRect(text)
        self.setMaximumWidth(rect.width() + 30)

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        super(TextMessage, self).paintEvent(a0)


class Triangle(QLabel):
    def __init__(self, type, role=MessageRole.ASSISTANT, parent=None):
        super().__init__(parent)
        self.type = type
        self.role = role
        self.setFixedSize(6, 45)

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        super(Triangle, self).paintEvent(a0)
        if self.type == MessageType.TEXT:
            painter = QPainter(self)
            triangle = QPolygon()
            if self.role == MessageRole.USER:
                painter.setPen(QColor("#b2e281"))
                painter.setBrush(QColor("#b2e281"))
                triangle.setPoints(0, 20, 0, 34, 6, 27)
            else:
                painter.setPen(QColor("white"))
                painter.setBrush(QColor("white"))
                triangle.setPoints(0, 27, 6, 20, 6, 34)
            painter.drawPolygon(triangle)


class Notice(QLabel):
    def __init__(self, text, type_="UNK", parent=None):
        super().__init__(text, parent)
        self.type_ = type_
        self.setFont(QFont("微软雅黑", 12))
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setAlignment(Qt.AlignCenter)


class Avatar(QLabel):
    def __init__(self, avatar, parent=None):
        super().__init__(parent)
        if isinstance(avatar, str):
            self.setPixmap(QPixmap(avatar).scaled(45, 45))
            self.image_path = avatar
        elif isinstance(avatar, QPixmap):
            self.setPixmap(avatar.scaled(45, 45))
        self.setFixedSize(QSize(45, 45))


class OpenImageThread(QThread):
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self) -> None:
        image = Image.open(self.image_path)
        image.show()


class ImageMessage(QLabel):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image = QLabel(self)
        if isinstance(image_path, str):
            self.setPixmap(QPixmap(image_path))
            self.image_path = image_path
        elif isinstance(image_path, QPixmap):
            self.setPixmap(image_path)
        self.setMaximumWidth(600)
        self.setMaximumHeight(600)
        self.setScaledContents(True)

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:  # 左键按下
            self.open_image_thread = OpenImageThread(self.image_path)
            self.open_image_thread.start()


class PlayAudioThread(QThread):
    progress_update = pyqtSignal(int)  # 进度更新信号
    playback_finished = pyqtSignal()  # 播放完成信号

    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path
        self.is_playing = True  # 控制播放状态

    def run(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.audio_path)
        pygame.mixer.music.play()

        audio_length = pygame.mixer.Sound(self.audio_path).get_length()  # 获取音频长度
        start_time = time.time()

        while pygame.mixer.music.get_busy() and self.is_playing:
            elapsed_time = time.time() - start_time
            progress = int((elapsed_time / audio_length) * 100)
            self.progress_update.emit(progress)
            time.sleep(0.1)

        self.progress_update.emit(100)  # 确保进度条最终满格
        self.playback_finished.emit()

    def stop(self):
        self.is_playing = False
        pygame.mixer.music.stop()


class AudioMessage(QWidget):
    def __init__(self, audio_path, parent=None):
        super().__init__(parent)
        self.audio_path = audio_path
        self.is_playing = False

        # 播放按钮
        self.play_button = QPushButton("▶", self)
        self.play_button.setFixedSize(40, 40)
        self.play_button.clicked.connect(self.toggle_playback)

        # 进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(200)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.play_button)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        self.audio_thread = None  # 线程

    def toggle_playback(self):
        if self.is_playing:
            self.stop_audio()
        else:
            self.play_audio()

    def play_audio(self):
        if self.audio_thread and self.audio_thread.isRunning():
            self.stop_audio()

        self.audio_thread = PlayAudioThread(self.audio_path)
        self.audio_thread.progress_update.connect(self.progress_bar.setValue)
        self.audio_thread.playback_finished.connect(self.on_audio_finished)
        self.audio_thread.start()

        self.is_playing = True
        self.play_button.setText("⏸")  # 切换成暂停按钮

    def stop_audio(self):
        if self.audio_thread:
            self.audio_thread.stop()
        self.is_playing = False
        self.play_button.setText("▶")
        self.progress_bar.setValue(0)

    def on_audio_finished(self):
        self.is_playing = False
        self.play_button.setText("▶")
        self.progress_bar.setValue(0)


class FileMessage(QLabel):
    def __init__(self, file_path, role=MessageRole.ASSISTANT, parent=None):
        super(FileMessage, self).__init__(parent)
        self.file_path = file_path
        self.role = role
        # 设置字体
        font = QFont("微软雅黑", 12)
        self.setFont(font)
        self.setWordWrap(True)
        self.setMaximumWidth(800)
        self.setMinimumWidth(100)
        self.setMinimumHeight(45)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        if role == MessageRole.USER:
            self.setAlignment(Qt.AlignCenter | Qt.AlignRight)
            self.setStyleSheet(
                """
                background-color:#b2e281;
                border-radius:10px;
                padding:10px;
                """
            )
        else:
            self.setStyleSheet(
                """
                background-color:white;
                border-radius:10px;
                padding:10px;
                """
            )
        # 显示文件名称
        file_name = file_path.split("/")[-1]
        self.setText(file_name)
        # 可以添加文件图标或其他标识元素，这里使用一个简单的标签作为示例
        self.file_icon = QLabel(self)
        self.file_icon.setText("📄")
        self.file_icon.setGeometry(10, 10, 20, 20)
        self.file_icon.setStyleSheet(
            """
            font-size: 20px;
            """
        )
        # 可以添加点击事件，例如打开文件
        self.setMouseTracking(True)
        self.mousePressEvent = self.open_file

    def open_file(self, event):
        # 这里可以添加打开文件的逻辑，例如使用系统默认程序打开文件
        pass


class BubbleMessage(QWidget):
    def __init__(
        self, str_content, avatar, type, role=MessageRole.ASSISTANT, parent=None
    ):
        super().__init__(parent)
        self.content = str_content
        self.role = role
        self.type = type

        self.setStyleSheet(
            """
            border:none;
            """
        )
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 5, 5, 5)
        # self.resize(QSize(200, 50))
        self.avatar = Avatar(avatar)
        triangle = Triangle(type, role)
        if type == MessageType.TEXT:
            self.message = TextMessage(str_content, role)
            # self.message.setMaximumWidth(int(self.width() * 0.6))
        elif type == MessageType.IMAGE:
            self.message = ImageMessage(str_content)
        elif type == MessageType.FILE:
            self.message = FileMessage(str_content)
        elif type == MessageType.AUDIO:
            self.message = AudioMessage(str_content)
        else:
            raise ValueError("未知的消息类型")

        self.spacerItem = QSpacerItem(
            45 + 6, 45, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        if role == MessageRole.USER:
            layout.addItem(self.spacerItem)
            layout.addWidget(self.message, 1)
            layout.addWidget(triangle, 0, Qt.AlignTop | Qt.AlignLeft)
            layout.addWidget(self.avatar, 0, Qt.AlignTop | Qt.AlignLeft)
        else:
            layout.addWidget(self.avatar, 0, Qt.AlignTop | Qt.AlignRight)
            layout.addWidget(triangle, 0, Qt.AlignTop | Qt.AlignRight)
            layout.addWidget(self.message, 1)
            layout.addItem(self.spacerItem)
        self.setLayout(layout)


class ScrollAreaContent(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.adjustSize()


class ScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet(
            """
            border:none;
            """
        )


class ScrollBar(QScrollBar):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """
          QScrollBar:vertical {
              border-width: 0px;
              border: none;
              background:rgba(64, 65, 79, 0);
              width:5px;
              margin: 0px 0px 0px 0px;
          }
          QScrollBar::handle:vertical {
              background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
              stop: 0 #DDDDDD, stop: 0.5 #DDDDDD, stop:1 #aaaaff);
              min-height: 20px;
              max-height: 20px;
              margin: 0 0px 0 0px;
              border-radius: 2px;
          }
          QScrollBar::add-line:vertical {
              background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
              stop: 0 rgba(64, 65, 79, 0), stop: 0.5 rgba(64, 65, 79, 0),  stop:1 rgba(64, 65, 79, 0));
              height: 0px;
              border: none;
              subcontrol-position: bottom;
              subcontrol-origin: margin;
          }
          QScrollBar::sub-line:vertical {
              background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
              stop: 0  rgba(64, 65, 79, 0), stop: 0.5 rgba(64, 65, 79, 0),  stop:1 rgba(64, 65, 79, 0));
              height: 0 px;
              border: none;
              subcontrol-position: top;
              subcontrol-origin: margin;
          }
          QScrollBar::sub-page:vertical {
              background: rgba(64, 65, 79, 0);
          }

          QScrollBar::add-page:vertical {
              background: rgba(64, 65, 79, 0);
          }
            """
        )


class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(500, 200)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        self.adjustSize()

        # 生成滚动区域
        self.scrollArea = ScrollArea(self)
        scrollBar = ScrollBar()
        self.scrollArea.setVerticalScrollBar(scrollBar)
        # self.scrollArea.setGeometry(QRect(9, 9, 261, 211))
        # 生成滚动区域的内容部署层部件
        self.scrollAreaWidgetContents = ScrollAreaContent(self.scrollArea)
        self.scrollAreaWidgetContents.setMinimumSize(50, 100)
        # 设置滚动区域的内容部署部件为前面生成的内容部署层部件
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        layout.addWidget(self.scrollArea)
        self.layout0 = QVBoxLayout()
        self.layout0.setSpacing(0)
        self.scrollAreaWidgetContents.setLayout(self.layout0)
        self.setLayout(layout)

    def add_message_item(self, bubble_message, index=1):
        if index:
            self.layout0.addWidget(bubble_message)
        else:
            self.layout0.insertWidget(0, bubble_message)
        # self.set_scroll_bar_last()

    def set_scroll_bar_last(self):
        self.scrollArea.verticalScrollBar().setValue(
            self.scrollArea.verticalScrollBar().maximum()
        )

    def set_scroll_bar_value(self, val):
        self.verticalScrollBar().setValue(val)

    def verticalScrollBar(self):
        return self.scrollArea.verticalScrollBar()

    def update(self) -> None:
        super().update()
        self.scrollAreaWidgetContents.adjustSize()
        self.scrollArea.update()
        # self.scrollArea.repaint()
        # self.verticalScrollBar().setMaximum(self.scrollAreaWidgetContents.height())
