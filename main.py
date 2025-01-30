# copy and modify from:
# https://github.com/llq20133100095/DeskTopPet/blob/main/main.py

import os
import sys
import glob
import shutil
import random
import datetime

from PyQt5.QtGui import QCursor, QMovie, QColor
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QLabel,
    QVBoxLayout,
    QMenu,
    qApp,
    QDesktopWidget,
)

from clients import ChatClient, DoraemonClient, ReActClient
from utils.utils import read_text_from_file
from settings import WORK_DIR, DEFAULT_CLIENT_TYPE, REPO_PATH


class DesktopPet(QWidget):
    def __init__(self, parent=None, **kwargs):
        super(DesktopPet, self).__init__(parent)
        # TODO Q: win11下“隐藏”后无法再次“显示”
        self.windowopacity = 1  # gif透明度，用于“隐藏”/“显示”
        self.init_window()  # 窗体初始化
        self.init_pet()  # 宠物初始化
        self.normal_state()  # 正常待机，实现随机切换动作

    def init_window(self):
        """initialize window: location, background, opacity"""
        # TODO Q:可以和self.init_pet()合起来吗

        # 设置窗口属性:窗口无标题栏且固定在最前面
        # FrameWindowHint:无边框窗口
        # WindowStaysOnTopHint: 窗口总显示在最上面
        # SubWindow: 新窗口部件是一个子窗口，而无论窗口部件是否有父窗口部件
        # https://blog.csdn.net/kaida1234/article/details/79863146
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow
        )
        self.setAutoFillBackground(False)  # True为自动填充背景,False为透明背景
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # 窗口透明，窗体空间不透明
        self.repaint()  # 重绘组件、刷新

    def get_screen_color(self, x, y):
        """get screen color of (x,y), avoid black text on black background"""
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0, x, y, 1, 1)
        image = screenshot.toImage()
        color = image.pixel(0, 0)
        return QColor(color).getRgb()[:3]

    def init_pet(self):
        """initialize pet: location, gif, text"""
        # 1.文本框
        self.textLabel = QLabel(self)  # 实例化文本框
        self.textLabel.setStyleSheet(  # 文本框样式
            "font:15pt '楷体';" "border-width: 1px;" "color:blue;"
        )

        # 2.gif
        self.image = QLabel(self)
        self.movie = QMovie(
            os.path.join(REPO_PATH, "assets/ui/coming.gif")
        )  # QMovie存放动态视频，一般配合QLabel使用，可用来存放GIF动态图
        self.movie.setScaledSize(QSize(500, 500))  # 设置gif大小
        self.image.setMovie(self.movie)  # 将movie在image中显示：对应QMovie - QLabel
        self.movie.start()
        self.resize(500, 500)

        # 3.位置，桌面随机位置
        self.random_position()

        # 4.布局设置
        vbox = QVBoxLayout()
        vbox.addWidget(self.textLabel)
        vbox.addWidget(self.image)
        self.setLayout(vbox)  # 加载布局：前面设置好的垂直布局

        self.show()

        # 将正常待机状态的动图放入normal_action中
        gif_files = glob.glob(
            os.path.join(REPO_PATH, "assets/ui/normal", "*.gif"), recursive=True
        )
        self.normal_action = [os.path.abspath(gif) for gif in gif_files]

        # todo_list
        self.todo_list = []

    def normal_state(self):
        """states"""
        # 1.动作切换
        self.action_timer = QTimer()  # 实例化定时器
        self.action_timer.timeout.connect(self.random_act)  # 到时自动执行
        self.action_timer.start(5000)  # 动作时间切换设置
        self.action_condition = 0  # 动作状态设置为正常

        # 2.text切换：待办/时间
        self.text_timer = QTimer()
        self.text_timer.timeout.connect(self.random_text)
        self.text_timer.start(5000)
        self.text_condition = 0
        self.random_text()

    def random_act(self):
        """random action of pet"""
        if not self.action_condition:  # 正常待机状态
            self.movie = QMovie(random.choice(self.normal_action))  # 随机选取gif
            self.movie.setScaledSize(QSize(500, 500))  # 宠物大小
            self.image.setMovie(self.movie)  # 将动画添加到label中
            self.movie.start()  # 播放gif
        elif self.action_condition == 1:
            self.movie = QMovie(
                os.path.join(REPO_PATH, "assets/ui/click.gif")
            )  # 读取特殊状态图片路径
            self.movie.setScaledSize(QSize(500, 500))
            self.image.setMovie(self.movie)
            self.movie.start()

            self.action_condition = 0
            self.text_condition = 0

    def get_todo(self):
        """get todo list"""
        todo_str = read_text_from_file(
            os.path.join(REPO_PATH, "assets/tools/content/todo_list.txt")
        )
        self.todo_list = todo_str.split("\n")
        self.todo_list = list(map(lambda x: f"别忘了 {x.strip()}!", self.todo_list))

    def random_text(self):
        """random text on pet"""
        current_time = datetime.datetime.now()  # 获取当前时间
        current_date = current_time.date()  # 当前日期
        formatted_time = current_time.strftime("%H:%M:%S")  # 当前时间
        timestr = f"{current_date} {formatted_time}"  # 整理时间

        color = self.get_screen_color(self.x, self.y)  # 文本颜色

        self.get_todo()
        show_text = (
            random.choice(self.todo_list + [timestr]) if self.todo_list else timestr
        )
        self.textLabel.setText(show_text)
        self.textLabel.setStyleSheet(
            "font: bold;"
            "font:15pt '楷体';"
            f"color:rgb({255-color[0]}, {255-color[1]}, {255-color[2]});"
            "background-color: red"
            "url(:/)"
        )
        self.textLabel.adjustSize()  # 根据内容自适应大小

    def random_position(self):
        """random position of pet on desktop"""
        screen_geo = (
            QDesktopWidget().screenGeometry()
        )  # 返回当前屏幕的几何信息，包括屏幕的位置、宽度和高度
        pet_geo = (
            self.geometry()
        )  # 获取部件在其父窗口坐标系统中的几何信息，包括部件的位置和大小

        width = int((screen_geo.width() - pet_geo.width()) * random.random())
        height = int((screen_geo.height() - pet_geo.height()) * random.random())
        self.move(width, height)
        self.x = width
        self.y = height

    def mousePressEvent(self, event):
        """press mouse's left button: pet will be bound to mouse"""
        self.action_condition = 1
        self.text_condition = 1
        self.random_text()
        self.random_act()

        if event.button() == Qt.LeftButton:
            self.is_follow_mouse = True
        self.mouse_drag_pos = event.globalPos() - self.pos()  # 计算鼠标相对位置
        event.accept()
        self.setCursor(QCursor(Qt.OpenHandCursor))  # 鼠标图形设置为手

    def mouseMoveEvent(self, event):
        """move mouse: pet will follow mouse"""
        if Qt.LeftButton and self.is_follow_mouse:
            delta = event.globalPos() - self.mouse_drag_pos
            self.x = delta.x()
            self.y = delta.y()
            self.move(delta)
        event.accept()

    def mouseReleaseEvent(self, event):
        """release mouse: pet will not follow mouse"""
        self.is_follow_mouse = False
        self.setCursor(QCursor(Qt.ArrowCursor))  # 鼠标图形设置为箭头

    def contextMenuEvent(self, event):
        """press mouse's right button: show menu"""
        menu = QMenu(self)

        # 选项1：显示/隐藏
        if self.windowopacity > 0:
            hide_or_exist = menu.addAction("隐藏")
        else:
            hide_or_exist = menu.addAction("显示")

        # 选项2：对话
        chat = menu.addAction("对话")
        menu.addSeparator()

        # 选项3: 喂食
        feedAction = menu.addAction("铜锣烧")

        # 选项4：退出
        quitAction = menu.addAction("退出")

        # # 选项5：设置
        # settingAction = menu.addAction("设置")
        # menu.addSeparator()

        # 使用exec_()方法显示菜单。从鼠标右键事件对象中获得当前坐标。mapToGlobal()方法把当前组件的相对坐标转换为窗口（window）的绝对坐标。
        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == hide_or_exist:
            if self.windowopacity > 0:
                self.setWindowOpacity(0)
                self.windowopacity = 0
            else:
                self.setWindowOpacity(1)
                self.windowopacity = 1
                self.movie = QMovie(os.path.join(REPO_PATH, "assets/ui/coming.gif"))
                self.movie.setScaledSize(QSize(500, 500))
                self.image.setMovie(self.movie)
                self.movie.start()

        if action == chat:
            if DEFAULT_CLIENT_TYPE == "doraemon":
                self.client = DoraemonClient()
            elif DEFAULT_CLIENT_TYPE == "react":
                self.client = ReActClient()
            else:
                self.client = ChatClient()
            self.client.show()

        if action == quitAction:
            self.movie = QMovie(os.path.join(REPO_PATH, "assets/ui/bye.gif"))
            self.movie.setScaledSize(QSize(500, 500))
            self.image.setMovie(self.movie)
            self.movie.start()
            QTimer.singleShot(1000, qApp.quit)  # 延迟一段时间再退出程序，实现退出效果

        if action == feedAction:
            self.movie = QMovie(os.path.join(REPO_PATH, "assets/ui/eat.gif"))
            self.movie.setScaledSize(QSize(500, 500))
            self.image.setMovie(self.movie)
            self.movie.start()
            self.textLabel.setText("铜锣烧最好吃啦！")

        # if action == settingAction:
        #     self.settings = Setting()


if __name__ == "__main__":
    # 清理WORK_DIR
    # shutil.rmtree(WORK_DIR,ignore_errors=True)
    # 创建了一个QApplication对象，对象名为app，带两个参数argc,argv
    # 所有的PyQt5应用必须创建一个应用（Application）对象。sys.argv参数是一个来自命令行的参数列表。
    app = QApplication(sys.argv)
    # 窗口组件初始化
    pet = DesktopPet()
    # 1. 进入时间循环；
    # 2. wait，直到响应app可能的输入；
    # 3. QT接收和处理用户及系统交代的事件（消息），并传递到各个窗口；
    # 4. 程序遇到exit()退出时，机会返回exec()的值。
    sys.exit(app.exec_())
