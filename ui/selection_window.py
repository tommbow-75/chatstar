from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

class SelectionWindow(QWidget):
    region_selected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        # 不使用 WA_TranslucentBackground，改用手動繪製方式避免 Windows 相容問題
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        # 這個做法 Windows 上最穩定：靠 paintEvent 的半透明黑色覆蓋
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        self.start_pos = None
        self.end_pos = None
        self.selecting = False
        
    def showFullScreen(self):
        screen = QApplication.primaryScreen()
        geo = screen.geometry()
        self.setGeometry(geo)
        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 繪製半透明黑色遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        
        # 如果正在選取，繪製選取框
        if self.selecting and self.start_pos and self.end_pos:
            rect = QRect(self.start_pos, self.end_pos).normalized()
            # 在選取區域內清除遮罩（讓使用者看到底下畫面）
            painter.fillRect(rect, QColor(0, 0, 0, 0))
            # 繪製藍色邊框
            pen = QPen(QColor(30, 144, 255), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.end_pos = event.pos()
            self.selecting = False
            
            rect = QRect(self.start_pos, self.end_pos).normalized()
            
            # 若選取太小則忽略
            if rect.width() < 10 or rect.height() < 10:
                print("選取的區域太小，請重新嘗試。")
                # 重置並繼續讓使用者選取
                self.start_pos = None
                self.end_pos = None
                self.update()
                return
            
            # 取得視窗在螢幕上的偏移量
            win_pos = self.pos()
            region = {
                "top": rect.y() + win_pos.y(),
                "left": rect.x() + win_pos.x(),
                "width": rect.width(),
                "height": rect.height()
            }
            
            print(f"選取完成: {region}")
            self.region_selected.emit(region)
            self.close()
    
    def keyPressEvent(self, event):
        # 按 ESC 可以離開選取模式
        if event.key() == Qt.Key.Key_Escape:
            print("使用者按下 ESC，取消選取。")
            self.close()
