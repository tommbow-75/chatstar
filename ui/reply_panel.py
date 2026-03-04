import pyperclip
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QComboBox)
from PyQt6.QtCore import Qt, QTimer

STYLES = [
    ("正式", "#a6e3a1", "#1e1e2e"),   # 綠
    ("輕鬆", "#89b4fa", "#1e1e2e"),   # 藍
    ("簡短", "#f9e2af", "#1e1e2e"),   # 黃
]

# 下拉選單的對應 key 順序需與 STYLES 一致
STYLE_KEYS = ["formal", "casual", "brief"]


class ReplyPanel(QWidget):
    """顯示下拉選單風格選擇 + 單一回覆建議卡片的面板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── 標題 + 下拉選單（同一行）──
        header_row = QHBoxLayout()
        header = QLabel("💬 AI 回覆建議")
        header.setStyleSheet("color: #cdd6f4; font-size: 13px; font-weight: bold;")
        header_row.addWidget(header)
        header_row.addStretch()

        self.style_combo = QComboBox()
        self.style_combo.setObjectName("style_combo")
        for name, _, _ in STYLES:
            self.style_combo.addItem(name)
        self.style_combo.setFixedWidth(90)
        self.style_combo.currentIndexChanged.connect(self._on_style_changed)
        header_row.addWidget(self.style_combo)
        layout.addLayout(header_row)

        # ── 回覆卡片 ──
        self._replies: list[str] = ["", "", ""]
        self._current_idx = 0

        name, color, text_color = STYLES[0]
        self._card_color = color
        self._card_text_color = text_color

        self.card_frame = QFrame()
        self.card_frame.setObjectName("reply_card")
        self._apply_card_style(color)

        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        # 風格標籤
        self.style_tag = QLabel(f"【{name}】")
        self.style_tag.setStyleSheet(
            f"font-size: 11px; font-weight: bold; color: {text_color};"
        )
        card_layout.addWidget(self.style_tag)

        # 回覆文字
        self.text_label = QLabel("—")
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet(f"font-size: 13px; color: {text_color};")
        card_layout.addWidget(self.text_label)

        # 複製按鈕
        self.copy_btn = QPushButton("📋 一鍵複製")
        self.copy_btn.setObjectName("copy_btn")
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
        card_layout.addWidget(self.copy_btn)

        layout.addWidget(self.card_frame)

    # ── helpers ──

    def _apply_card_style(self, color: str):
        self.card_frame.setStyleSheet(f"""
            QFrame#reply_card {{
                background-color: {color};
                border-radius: 10px;
            }}
            QLabel {{
                color: {self._card_text_color};
                background: transparent;
            }}
        """)

    def _on_style_changed(self, idx: int):
        self._current_idx = idx
        name, color, text_color = STYLES[idx]
        self._card_color = color
        self._card_text_color = text_color

        self._apply_card_style(color)
        self.style_tag.setText(f"【{name}】")
        self.style_tag.setStyleSheet(
            f"font-size: 11px; font-weight: bold; color: {text_color};"
        )
        self.text_label.setStyleSheet(f"font-size: 13px; color: {text_color};")
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
        # 更新顯示文字
        text = self._replies[idx] if idx < len(self._replies) else ""
        self.text_label.setText(text if text else "—")

    def update_replies(self, replies: list):
        """接收 3 個回覆字串並更新；顯示目前選中風格的結果。"""
        self._replies = list(replies) + [""] * max(0, 3 - len(replies))
        idx = self._current_idx
        text = self._replies[idx] if idx < len(self._replies) else ""
        self.text_label.setText(text if text else "—")

    def _copy(self):
        idx = self._current_idx
        text = self._replies[idx] if idx < len(self._replies) else ""
        if text:
            try:
                pyperclip.copy(text)
            except Exception:
                pass
            original = self.copy_btn.text()
            self.copy_btn.setText("✅ 已複製！")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText(original))
