import pyperclip
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt, QTimer

STYLES = [
    ("正式", "#a6e3a1", "#1e1e2e"),   # 綠
    ("輕鬆", "#89b4fa", "#1e1e2e"),   # 藍
    ("簡短", "#f9e2af", "#1e1e2e"),   # 黃
]

CARD_STYLE = """
    QFrame#reply_card_{idx} {{
        background-color: {bg};
        border-radius: 10px;
        padding: 4px;
    }}
"""

class ReplyCard(QFrame):
    def __init__(self, style_name: str, color: str, text_color: str, idx: int):
        super().__init__()
        self.setObjectName(f"reply_card_{idx}")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
            }}
            QLabel {{
                color: {text_color};
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # 風格標籤
        tag = QLabel(f"【{style_name}】")
        tag.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {text_color}; opacity: 0.7;")
        layout.addWidget(tag)

        # 回覆文字
        self.text_label = QLabel("—")
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet(f"font-size: 13px; color: {text_color};")
        layout.addWidget(self.text_label)

        # 複製按鈕
        self.copy_btn = QPushButton("📋 一鍵複製")
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,0,0,0.15);
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background: rgba(0,0,0,0.25); }}
        """)
        self.copy_btn.clicked.connect(self._copy)
        layout.addWidget(self.copy_btn)

        self._text = ""

    def set_reply(self, text: str):
        self._text = text
        self.text_label.setText(text if text else "—")

    def _copy(self):
        if self._text:
            try:
                pyperclip.copy(self._text)
            except Exception:
                pass
            original = self.copy_btn.text()
            self.copy_btn.setText("✅ 已複製！")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText(original))


class ReplyPanel(QWidget):
    """顯示 3 張回覆建議卡片的面板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QLabel("💬 AI 回覆建議")
        header.setStyleSheet("color: #cdd6f4; font-size: 13px; font-weight: bold;")
        layout.addWidget(header)

        self.cards: list[ReplyCard] = []
        for idx, (name, color, text_color) in enumerate(STYLES):
            card = ReplyCard(name, color, text_color, idx)
            layout.addWidget(card)
            self.cards.append(card)

    def update_replies(self, replies: list):
        """接收 3 個回覆字串並更新卡片。"""
        for i, card in enumerate(self.cards):
            card.set_reply(replies[i] if i < len(replies) else "")
