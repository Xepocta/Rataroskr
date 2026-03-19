import sys
import os
import random

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QUrl, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QPixmap, QCursor, QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

from pynput import mouse


# 桥接类，用于将 pynput 的线程信号转到主线程
class MouseSignal(QObject):
    clicked = pyqtSignal(int, int, str)  # x, y, button_name
    scrolled = pyqtSignal(int)           # delta


class Ratatoskr(QWidget):
    def __init__(self, dirname__Rat):
        super().__init__()
        self.basepath__thisproject = os.path.dirname(__file__)

        # ---------- 资源缓存 ----------
        self.cache_pixmaps = {}      # 键: 完整路径, 值: QPixmap
        self.cache_media = {}         # 键: 完整路径, 值: QMediaContent

        # ---------- 加载动画帧 ----------
        self.frames = []
        path__Rat = os.path.join(self.basepath__thisproject, dirname__Rat)
        pngs = sorted([p for p in os.listdir(path__Rat) if p.lower().endswith(".png")])
        for p in pngs:
            pix = QPixmap(os.path.join(path__Rat, p))
            if not pix.isNull():
                self.frames.append(pix)

        if not self.frames:
            sys.exit()

        self.frame__current = 0
        frame__first = self.frames[0]
        self.resize(frame__first.width(), frame__first.height())
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # ---------- 状态变量 ----------
        self.pos__mouse = QCursor.pos()
        self.text__clipboard = ""
        self.index__clipboard = 0
        self.capacityPage__clipboard = 0
        self.active__clipboard = False

        self.effects = []        # 每个元素: {'pix': QPixmap, 'pos': QPoint, 'timer': int}
        self.players = []         # 存放正在播放的 QMediaPlayer

        # ---------- 鼠标信号桥接 ----------
        self.mouse_signals = MouseSignal()
        self.mouse_signals.clicked.connect(self.on_mouse_clicked)
        self.mouse_signals.scrolled.connect(self.on_mouse_scrolled)

        # ---------- 启动 pynput 监听器 ----------
        self.listener = mouse.Listener(on_click=self._on_pynput_click, on_scroll=self._on_pynput_scroll)
        self.listener.daemon = True
        self.listener.start()

        # ---------- 定时器（30 FPS） ----------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update__Ratposition)
        self.timer.start(33)

        self.show()

    # ---------- pynput 回调（运行在独立线程）----------
    def _on_pynput_click(self, x, y, button, pressed):
        if not pressed:
            return
        # 将事件通过信号发往主线程
        self.mouse_signals.clicked.emit(x, y, button.name)

    def _on_pynput_scroll(self, x, y, dx, dy):
        # dy 是滚轮垂直滚动量，正数向上，负数向下
        self.mouse_signals.scrolled.emit(dy)

    # ---------- 主线程处理鼠标事件 ----------
    def on_mouse_clicked(self, x, y, button_name):
        pos = QPoint(x, y)
        if button_name == "left":
            self.create_effect("ClickLeft", pos)
        elif button_name == "right":
            self.create_effect("ClickRight", pos)
        elif button_name == "middle":
            self.show__clipboard()

    def on_mouse_scrolled(self, dy):
        if dy > 0:  # 向上滚动
            self.frame__current = (self.frame__current + 1) % len(self.frames)
        else:        # 向下滚动
            self.frame__current = (self.frame__current - 1) % len(self.frames)
        # 如果新帧尺寸变化，调整窗口大小
        new_pix = self.frames[self.frame__current]
        if new_pix.size() != self.size():
            self.resize(new_pix.size())
        self.update()

    # ---------- 资源缓存获取 ----------
    def get_cached_pixmap(self, dirname, filename):
        """返回缓存中的 QPixmap，如果不存在则加载并缓存"""
        full_path = os.path.join(self.basepath__thisproject, dirname, filename)
        if full_path not in self.cache_pixmaps:
            pix = QPixmap(full_path)
            if not pix.isNull():
                self.cache_pixmaps[full_path] = pix
            else:
                return None
        return self.cache_pixmaps[full_path]

    def get_cached_media(self, dirname, filename):
        """返回缓存中的 QMediaContent，如果不存在则创建并缓存"""
        full_path = os.path.join(self.basepath__thisproject, dirname, filename)
        if full_path not in self.cache_media:
            url = QUrl.fromLocalFile(full_path)
            self.cache_media[full_path] = QMediaContent(url)
        return self.cache_media[full_path]

    # ---------- 创建点击效果 ----------
    def create_effect(self, dirname__click, pos):
        # 获取该目录下的所有文件
        path = os.path.join(self.basepath__thisproject, dirname__click)
        if not os.path.isdir(path):
            return

        files = os.listdir(path)
        pngs = [f for f in files if f.lower().endswith(".png")]
        mp3s = [f for f in files if f.lower().endswith(".mp3")]

        if pngs:
            # 随机选一张图片并缓存
            png_file = random.choice(pngs)
            pix = self.get_cached_pixmap(dirname__click, png_file)
            if pix:
                pos__effect = QPoint(
                    random.randint(0, max(0, self.width() - pix.width())),
                    random.randint(0, max(0, self.height() - pix.height()))
                )
                self.effects.append({'pix': pix, 'pos': pos__effect, 'timer': 500})

        if mp3s:
            mp3_file = random.choice(mp3s)
            self.play__sound(dirname__click, mp3_file)

    # ---------- 播放音频（带自动清理）----------
    def play__sound(self, dirname, mp3_file):
        media = self.get_cached_media(dirname, mp3_file)
        player = QMediaPlayer()
        player.setMedia(media)
        player.play()

        # 播放结束时自动移除并销毁
        def on_media_status_changed(status):
            if status == QMediaPlayer.EndOfMedia or status == QMediaPlayer.StoppedState:
                if player in self.players:
                    self.players.remove(player)
                player.deleteLater()

        player.mediaStatusChanged.connect(on_media_status_changed)
        self.players.append(player)

    # ---------- 主更新逻辑（仅移动和重绘）----------
    def update__Ratposition(self):
        new_pos = QCursor.pos()
        if new_pos != self.pos__mouse:
            self.pos__mouse = new_pos
            x = new_pos.x() + 12
            y = new_pos.y() + 20
            self.move(x, y)
            self.update()  # 触发重绘

        # 更新特效计时
        for effect in self.effects:
            effect['timer'] -= 33
        self.effects = [e for e in self.effects if e['timer'] > 0]

    # ---------- 绘制 ----------
    def paintEvent(self, e):
        painter = QPainter(self)
        # 绘制宠物本身
        pix = self.frames[self.frame__current]
        painter.drawPixmap(0, 0, pix)

        # 绘制点击特效
        for effect in self.effects:
            painter.drawPixmap(effect['pos'], effect['pix'])

        # 绘制剪贴板文本（优化后的简单绘制）
        if self.active__clipboard and self.text__clipboard:
            painter.setFont(QFont("Courier", 12))
            painter.setPen(Qt.black)
            margin = 6
            x, y = margin, margin
            # 此处可以继续细化，但建议将分页计算放在 show__clipboard 中，
            # paintEvent 只负责绘制预先分好的行。
            # 为简化，这里直接绘制全部文本（如果太长可能会卡，但通常剪贴板不会太长）
            painter.drawText(x, y, self.width() - 2*margin, self.height()//2,
                             Qt.TextWordWrap, self.text__clipboard)

    # ---------- 剪贴板显示 ----------
    def show__clipboard(self):
        text = QApplication.clipboard().text().strip()
        if not text:
            return

        if self.active__clipboard:
            # 翻下一页（简化：每次显示固定行数，实际可计算）
            self.index__clipboard += 500  # 假设每页500字符，粗略
            if self.index__clipboard >= len(self.text__clipboard):
                self.active__clipboard = False
                self.index__clipboard = 0
                self.text__clipboard = ""
            self.update()
            return

        self.text__clipboard = text
        self.index__clipboard = 0
        self.active__clipboard = True
        self.update()

    # ---------- 关闭清理 ----------
    def closeEvent(self, e):
        if hasattr(self, "listener"):
            self.listener.stop()
        # 清理所有播放器
        for player in self.players:
            player.stop()
            player.deleteLater()
        self.players.clear()
        super().closeEvent(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ratatoskr = Ratatoskr("Rat")
    sys.exit(app.exec_())
