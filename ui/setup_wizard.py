"""ui/setup_wizard.py — 首次登入的設置嚮導（3 頁）。

Page 1: 基本資料（username）
Page 2: 興趣選擇（預設選項，多選）
Page 3: 近期話題（5 個輸入框）
"""

from PyQt6.QtWidgets import (
    QWizard, QWizardPage,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QFrame,
    QPushButton, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# ── 預設興趣選項 ────────────────────────────────────────────────────────────────
INTEREST_OPTIONS = [
    "🎵 音樂",  "🎬 電影",  "📚 讀書",  "🎮 遊戲",  "🏀 籃球", "⚽ 足球", "羽毛球", "桌球",
    "🍜 美食",  "✈️ 旅遊",  "🎨 藝術",  "📸 攝影",  "🧘 健身", "桌遊", "爬山",
    "💻 科技",  "🌿 自然",  "🐾 貓", "🐾 狗", "🎭 影劇",  "🛒 購物", "酒精",
    "🌏 時事",  "🎸 樂器",  "☕ 咖啡",  "🧩 益智", "軍事", "歷史"
]

_STYLE = """
QWizard, QWizardPage {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QLabel {
    color: #cdd6f4;
    font-size: 13px;
}
QLabel#page_title {
    font-size: 17px;
    font-weight: bold;
    color: #89b4fa;
    padding-bottom: 2px;
}
QLabel#page_desc {
    color: #6c7086;
    font-size: 11px;
    line-height: 1.6;
}
QLabel#field_label {
    color: #a6adc8;
    font-size: 12px;
    font-weight: bold;
}
QLineEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 13px;
}
QLineEdit:focus { border: 1px solid #89b4fa; }
QLineEdit:disabled { background-color: #27293d; color: #45475a; }
QPushButton#chip {
    background-color: #313244;
    color: #a6adc8;
    border: 1px solid #45475a;
    border-radius: 14px;
    font-size: 12px;
    padding: 5px 12px;
}
QPushButton#chip:hover  { border-color: #89b4fa; color: #89b4fa; }
QPushButton#chip[selected=true] {
    background-color: #1e3a5f;
    border: 2px solid #89b4fa;
    color: #89b4fa;
    font-weight: bold;
}
QScrollArea { background-color: transparent; border: none; }
QWidget#chips_container { background-color: transparent; }
QFrame#divider { background-color: #313244; }
QWizard QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 7px;
    font-size: 13px;
    font-weight: bold;
    padding: 8px 20px;
    min-width: 80px;
}
QWizard QPushButton:hover  { background-color: #b4d0fa; }
QWizard QPushButton[text="< 上一步"] {
    background-color: transparent;
    color: #6c7086;
    border: 1px solid #45475a;
}
QWizard QPushButton[text="< 上一步"]:hover { color: #cdd6f4; }
QWizard QPushButton[text="取消"] {
    background-color: transparent;
    color: #6c7086;
    border: 1px solid #45475a;
}
QWizard QPushButton[text="取消"]:hover { color: #f38ba8; border-color: #f38ba8; }
"""


def _divider():
    d = QFrame()
    d.setObjectName("divider")
    d.setFrameShape(QFrame.Shape.HLine)
    d.setFixedHeight(1)
    return d


# ── Page 1: 基本資料 ───────────────────────────────────────────────────────────

class PageBasicInfo(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 12)
        layout.setSpacing(10)

        # 標題
        title = QLabel("👤  基本資料")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # 說明文字（可自訂）
        desc = QLabel(
            "請輸入您想在 ChatStar 上使用的名字。\n"
            "此名字將用於 AI 回覆建議中識別您的身份，"
            "之後可在設定中修改。"
        )
        desc.setObjectName("page_desc")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addWidget(_divider())
        layout.addSpacing(8)

        # 欄位標籤
        name_label = QLabel("名字 (Username)")
        name_label.setObjectName("field_label")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：小明、Amy、KennyLin…")
        self.name_input.setMaxLength(50)
        layout.addWidget(self.name_input)

        hint = QLabel("最多 50 個字元")
        hint.setStyleSheet("color: #585b70; font-size: 10px;")
        layout.addWidget(hint)

        layout.addStretch()

        # 將欄位註冊給 Wizard（用於 isComplete 判斷）
        self.registerField("username*", self.name_input)

    def isComplete(self) -> bool:
        return len(self.name_input.text().strip()) > 0


# ── Page 2: 興趣選擇 ───────────────────────────────────────────────────────────

class PageInterests(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        self.selected: set[str] = set()
        self._chips: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 12)
        layout.setSpacing(10)

        # 標題 + 說明
        title = QLabel("🎯  選擇您的興趣")
        title.setObjectName("page_title")
        layout.addWidget(title)

        desc = QLabel(
            "選擇一個或多個您感興趣的主題。\n"
            "ChatStar 會根據這些興趣，讓 AI 更了解您的興趣，"
            "提供更符合您風格的回覆建議。"
        )
        desc.setObjectName("page_desc")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addWidget(_divider())

        # 選擇計數標籤
        self.count_label = QLabel("已選 0 項")
        self.count_label.setStyleSheet("color: #89b4fa; font-size: 11px;")
        layout.addWidget(self.count_label)

        # 可捲動的 chip 區域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container.setObjectName("chips_container")
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 4, 0, 4)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        cols = 4
        for i, label in enumerate(INTEREST_OPTIONS):
            btn = QPushButton(label)
            btn.setObjectName("chip")
            btn.setCheckable(False)
            btn.setProperty("selected", False)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, l=label, b=btn: self._toggle(l, b))
            grid.addWidget(btn, i // cols, i % cols)
            self._chips[label] = btn

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _toggle(self, label: str, btn: QPushButton):
        if label in self.selected:
            self.selected.remove(label)
            btn.setProperty("selected", False)
        else:
            self.selected.add(label)
            btn.setProperty("selected", True)
        # 強制重新套用 style（Qt property 變更需要這一步）
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        count = len(self.selected)
        self.count_label.setText(f"已選 {count} 項")
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        return len(self.selected) > 0

    def get_preferences(self) -> list[str]:
        """回傳純文字的興趣列表（去除 emoji 前綴）。"""
        result = []
        for s in self.selected:
            # emoji 佔 2 bytes，後面接一個空格，取空格後的字串
            parts = s.split(" ", 1)
            result.append(parts[1] if len(parts) == 2 else s)
        return result


# ── Page 3: 近期話題 ───────────────────────────────────────────────────────────

class PageTopics(QWizardPage):
    TOPIC_COUNT = 5

    def __init__(self):
        super().__init__()
        self.setTitle("")
        self._inputs: list[QLineEdit] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 12)
        layout.setSpacing(10)

        # 標題 + 說明
        title = QLabel("💬  近期話題")
        title.setObjectName("page_title")
        layout.addWidget(title)

        desc = QLabel(
            "輸入您最近在聊或感興趣的話題（至少填寫 1 項）。\n"
            "例如：最近看的電影、追的劇、聊過的事件…\n"
            "AI 會參考這些資訊，讓對話更有共鳴。"
        )
        desc.setObjectName("page_desc")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addWidget(_divider())
        layout.addSpacing(4)

        # 5 個輸入框
        for i in range(self.TOPIC_COUNT):
            row = QHBoxLayout()
            num = QLabel(f"{i + 1}.")
            num.setFixedWidth(22)
            num.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 13px;")
            row.addWidget(num)

            inp = QLineEdit()
            inp.setPlaceholderText(f"話題 {i + 1}（選填）" if i > 0 else "話題 1（必填）")
            inp.setMaxLength(100)
            inp.textChanged.connect(self.completeChanged.emit)
            row.addWidget(inp)
            layout.addLayout(row)
            self._inputs.append(inp)

        layout.addStretch()

    def isComplete(self) -> bool:
        return len(self._inputs[0].text().strip()) > 0

    def get_topics(self) -> list[str]:
        """回傳非空話題列表。"""
        return [inp.text().strip() for inp in self._inputs if inp.text().strip()]


# ── SetupWizard 主體 ──────────────────────────────────────────────────────────

class SetupWizard(QWizard):
    """
    首次登入設置嚮導。

    使用方式：
        wizard = SetupWizard(user_id, parent)
        if wizard.exec() == QWizard.DialogCode.Accepted:
            data = wizard.collect_data()
            # data = {"user_id", "username", "preferences": [...], "topics": [...]}
    """

    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id

        self.setWindowTitle(f"ChatStar — 初始設置  (ID: {user_id})")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setFixedSize(560, 500)
        self.setStyleSheet(_STYLE)
        self.setButtonText(QWizard.WizardButton.NextButton, "下一步 >")
        self.setButtonText(QWizard.WizardButton.BackButton, "< 上一步")
        self.setButtonText(QWizard.WizardButton.FinishButton, "完成 ✓")
        self.setButtonText(QWizard.WizardButton.CancelButton, "取消")

        self.page_basic    = PageBasicInfo()
        self.page_interest = PageInterests()
        self.page_topics   = PageTopics()

        self.addPage(self.page_basic)
        self.addPage(self.page_interest)
        self.addPage(self.page_topics)

    def collect_data(self) -> dict:
        """完成後呼叫，收集所有頁面的輸入值。"""
        return {
            "user_id":     self.user_id,
            "username":    self.page_basic.name_input.text().strip(),
            "preferences": self.page_interest.get_preferences(),
            "topics":      self.page_topics.get_topics(),
        }
