"""ui/login_dialog.py — 啟動時輸入 user_id 的登入對話框。"""

import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression

_STYLE = """
QDialog {
    background-color: #1e1e2e;
}
QLabel {
    color: #cdd6f4;
    font-size: 13px;
}
QLabel#title {
    font-size: 20px;
    font-weight: bold;
    color: #89b4fa;
}
QLabel#subtitle {
    color: #6c7086;
    font-size: 11px;
}
QLabel#hint {
    color: #585b70;
    font-size: 10px;
}
QLabel#error {
    color: #f38ba8;
    font-size: 11px;
}
QLineEdit#id_input {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 15px;
    letter-spacing: 2px;
}
QLineEdit#id_input:focus {
    border: 2px solid #89b4fa;
}
QPushButton#btn_ok {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: bold;
    padding: 10px 24px;
}
QPushButton#btn_ok:hover  { background-color: #b4d0fa; }
QPushButton#btn_ok:disabled { background-color: #45475a; color: #6c7086; }
QPushButton#btn_cancel {
    background-color: transparent;
    color: #6c7086;
    border: 1px solid #45475a;
    border-radius: 8px;
    font-size: 13px;
    padding: 10px 24px;
}
QPushButton#btn_cancel:hover { color: #cdd6f4; border-color: #cdd6f4; }
QFrame#divider { background-color: #313244; }
"""

# user_id 驗證：英文字母 + 數字，1–12 字元
_ID_PATTERN = QRegularExpression(r"^[A-Za-z0-9]{1,12}$")


class LoginDialog(QDialog):
    """
    啟動時彈出的 user_id 登入對話框。

    使用注意：
      - accepted() → self.user_id 取得輸入值
      - rejected() → 使用者取消，app 應結束
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_id: str | None = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("ChatStar — 登入")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setFixedSize(380, 300)
        self.setStyleSheet(_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 28)
        layout.setSpacing(12)

        # ── Header ──
        title = QLabel("🌟 ChatStar")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("輸入您的 User ID 以繼續")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # ── 分隔線 ──
        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.Shape.HLine)
        div.setFixedHeight(1)
        layout.addSpacing(4)
        layout.addWidget(div)
        layout.addSpacing(4)

        # ── 輸入欄 ──
        self.id_input = QLineEdit()
        self.id_input.setObjectName("id_input")
        self.id_input.setPlaceholderText("例如：John123")
        self.id_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.id_input.setMaxLength(12)
        # 只允許英數字
        validator = QRegularExpressionValidator(_ID_PATTERN, self.id_input)
        self.id_input.setValidator(validator)
        self.id_input.textChanged.connect(self._on_text_changed)
        self.id_input.returnPressed.connect(self._on_ok)
        layout.addWidget(self.id_input)

        # ── 提示 + 錯誤訊息 ──
        self.hint_label = QLabel("英文字母與數字，最多 12 個字元")
        self.hint_label.setObjectName("hint")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hint_label)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        layout.addStretch()

        # ── 按鈕 ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_ok = QPushButton("確認 →")
        self.btn_ok.setObjectName("btn_ok")
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self._on_ok)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_ok)
        layout.addLayout(btn_row)

    # ── slots ──

    def _on_text_changed(self, text: str):
        valid = bool(re.fullmatch(r"[A-Za-z0-9]{1,12}", text))
        self.btn_ok.setEnabled(valid)
        self.error_label.hide()

    def _on_ok(self):
        text = self.id_input.text().strip()
        if not re.fullmatch(r"[A-Za-z0-9]{1,12}", text):
            self.error_label.setText("⚠️ 格式錯誤：只允許英文與數字（最多 12 字元）")
            self.error_label.show()
            return
        self.user_id = text
        self.accept()
