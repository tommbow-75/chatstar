from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen

class RegionOverlay(QWidget):
    """
    在螢幕上顯示一個彩色虛線框，標示目前的監聽區域。
    此視窗無邊框、透明背景、置頂，僅繪製邊框。
    """

    def __init__(self, region: dict):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput  # 滑鼠穿透，不阻擋操作
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # ── 物理像素 → 邏輯像素（Qt 繪圖用邏輯像素）──
        from PyQt6.QtWidgets import QApplication
        dpr = QApplication.primaryScreen().devicePixelRatio()

        border = 3  # 邊框留白（邏輯像素）
        self.setGeometry(
            int(region["left"]   / dpr) - border,
            int(region["top"]    / dpr) - border,
            int(region["width"]  / dpr) + border * 2,
            int(region["height"] / dpr) + border * 2,
        )
        self.show()


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 外圈：半透明藍色填充（極淡）
        painter.fillRect(self.rect(), QColor(89, 180, 250, 12))

        # 邊框：亮藍色實線
        pen = QPen(QColor(89, 180, 250), 2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

        # 四個角落加粗顯示（讓框更明顯）
        corner_len = 14
        pen2 = QPen(QColor(30, 180, 255), 4)
        painter.setPen(pen2)
        r = self.rect().adjusted(1, 1, -1, -1)
        # 左上
        painter.drawLine(r.topLeft(), r.topLeft() + r.topLeft().__class__(corner_len, 0))
        painter.drawLine(r.topLeft(), r.topLeft() + r.topLeft().__class__(0, corner_len))
        # 右上
        painter.drawLine(r.topRight(), r.topRight() + r.topRight().__class__(-corner_len, 0))
        painter.drawLine(r.topRight(), r.topRight() + r.topRight().__class__(0, corner_len))
        # 左下
        painter.drawLine(r.bottomLeft(), r.bottomLeft() + r.bottomLeft().__class__(corner_len, 0))
        painter.drawLine(r.bottomLeft(), r.bottomLeft() + r.bottomLeft().__class__(0, -corner_len))
        # 右下
        painter.drawLine(r.bottomRight(), r.bottomRight() + r.bottomRight().__class__(-corner_len, 0))
        painter.drawLine(r.bottomRight(), r.bottomRight() + r.bottomRight().__class__(0, -corner_len))
