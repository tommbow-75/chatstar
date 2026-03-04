from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QApplication,
                             QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ui.reply_panel import ReplyPanel

class MainWindow(QMainWindow):
    start_selection = pyqtSignal()
    stop_scanner = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Chat Assistant")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedWidth(440)

        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; }
            QLabel#title { font-size: 18px; font-weight: bold; padding: 4px 0; }
            QLabel#subtitle { color: #6c7086; font-size: 11px; }
            QLabel#status_label { color: #a6e3a1; font-size: 12px; }
            QLabel#region_label {
                color: #89b4fa; font-size: 11px;
                padding: 6px 8px; background-color: #313244; border-radius: 6px;
            }
            QLineEdit#api_key_input {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                padding: 6px 10px; font-size: 12px;
            }
            QLineEdit#api_key_input:focus { border: 1px solid #89b4fa; }
            QPushButton#btn_select {
                background-color: #89b4fa; color: #1e1e2e;
                border: none; border-radius: 8px;
                font-size: 13px; font-weight: bold; padding: 10px 16px;
            }
            QPushButton#btn_select:hover { background-color: #b4d0fa; }
            QPushButton#btn_select:disabled { background-color: #45475a; color: #6c7086; }
            QPushButton#btn_stop {
                background-color: #f38ba8; color: #1e1e2e;
                border: none; border-radius: 8px;
                font-size: 13px; font-weight: bold; padding: 10px 16px;
            }
            QPushButton#btn_stop:hover { background-color: #f5a0b8; }
            QPushButton#btn_stop:disabled { background-color: #45475a; color: #6c7086; }
            QFrame#divider { background-color: #313244; }
            QComboBox#style_combo {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                padding: 3px 8px; font-size: 12px;
            }
            QComboBox#style_combo:hover { border: 1px solid #89b4fa; }
            QComboBox#style_combo::drop-down { border: none; width: 20px; }
            QComboBox#style_combo QAbstractItemView {
                background-color: #313244; color: #cdd6f4;
                selection-background-color: #45475a;
                border: 1px solid #45475a; border-radius: 4px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(10)

        # ── Header ──
        title = QLabel("🤖 AI Chat Assistant")
        title.setObjectName("title")
        layout.addWidget(title)
        subtitle = QLabel("Gemini Vision × 螢幕辨識回覆輔助")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        layout.addWidget(self._divider())

        # ── API Key 輸入 ──
        api_row = QHBoxLayout()
        api_label = QLabel("Gemini Key：")
        api_label.setStyleSheet("font-size: 12px; color: #6c7086;")
        api_label.setFixedWidth(80)
        self.api_key_input = QLineEdit()
        self.api_key_input.setObjectName("api_key_input")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("輸入您的 Gemini API Key")
        api_row.addWidget(api_label)
        api_row.addWidget(self.api_key_input)
        layout.addLayout(api_row)

        # ── 狀態 + 區域 ──
        status_row = QHBoxLayout()
        status_title = QLabel("狀態：")
        status_title.setStyleSheet("color: #6c7086; font-size: 12px;")
        self.status_label = QLabel("閒置中")
        self.status_label.setObjectName("status_label")
        status_row.addWidget(status_title)
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        layout.addLayout(status_row)

        self.region_label = QLabel("尚未選取任何區域")
        self.region_label.setObjectName("region_label")
        self.region_label.setWordWrap(True)
        layout.addWidget(self.region_label)

        # ── 按鈕 ──
        btn_row = QHBoxLayout()
        self.btn_select = QPushButton("📷  選取監聽區域")
        self.btn_select.setObjectName("btn_select")
        self.btn_select.clicked.connect(self._on_select_clicked)
        self.btn_stop = QPushButton("⏹  停止")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        btn_row.addWidget(self.btn_select)
        btn_row.addWidget(self.btn_stop)
        layout.addLayout(btn_row)

        layout.addWidget(self._divider())

        # ── 回覆建議面板 ──
        self.reply_panel = ReplyPanel()
        layout.addWidget(self.reply_panel)

        # ── 底部提示 ──
        hint = QLabel("提示：選取後切換到通訊軟體，有新訊息時 AI 會自動分析。")
        hint.setStyleSheet("color: #45475a; font-size: 10px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

    # ── helpers ──

    def _divider(self):
        d = QFrame()
        d.setObjectName("divider")
        d.setFrameShape(QFrame.Shape.HLine)
        d.setFixedHeight(1)
        return d

    def _on_select_clicked(self):
        if not self.api_key_input.text().strip():
            self.status_label.setText("⚠️ 請先輸入 Gemini API Key")
            self.status_label.setStyleSheet("color: #f38ba8; font-size: 12px;")
            return
        self.status_label.setText("等待選取...")
        self.status_label.setStyleSheet("color: #fab387; font-size: 12px;")
        self.btn_select.setEnabled(False)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(300, self.start_selection.emit)

    def _on_stop_clicked(self):
        self.stop_scanner.emit()
        self.status_label.setText("閒置中")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        self.btn_select.setText("📷  選取監聽區域")
        self.btn_select.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def get_api_key(self) -> str:
        return self.api_key_input.text().strip()

    def set_scanning(self, region: dict):
        region_str = f"Left:{region['left']} Top:{region['top']}  {region['width']}×{region['height']} px"
        self.region_label.setText(f"監聽區域：{region_str}")
        self.status_label.setText("監聽中 ●")
        self.status_label.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        # 掃描中也保持可選取，改變按鈕文字提示可重新框選
        self.btn_select.setText("🔄  重新框選")
        self.btn_select.setEnabled(True)
        self.btn_stop.setEnabled(True)

    def set_status(self, msg: str):
        self.status_label.setText(msg)

    def update_replies(self, replies: list):
        self.reply_panel.update_replies(replies)
