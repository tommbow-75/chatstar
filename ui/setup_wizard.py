"""ui/setup_wizard.py — 首次登入的設置嚮導（3 頁）。

Page 1: 基本資料（username + Gemini API Key）
Page 2: 興趣選擇（預設選項，最多 6 項）
Page 3: 近期話題（5 個輸入框）

UI 主題: 深色（#1e1e2e），字型: 微軟正黑體
"""

from PyQt6.QtWidgets import (
    QWizard, QWizardPage,
    QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QFrame,
    QPushButton, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# ── 預設興趣選項 ────────────────────────────────────────────────────────────────
INTEREST_OPTIONS = [
    "🎵 音樂",   "🎬 電影",   "📚 讀書",   "🎮 遊戲",   "🏀 籃球",
    "⚽ 足球",   "羽毛球",    "桌球",      "🍜 美食",   "✈️ 旅遊",
    "🎨 藝術",   "📸 攝影",   "🧘 健身",   "桌遊",      "爬山",
    "💻 科技",   "🌿 自然",   "🐾 貓",     "🐾 狗",     "🎭 影劇",
    "🛒 購物",   "酒精",      "🌏 時事",   "🎸 樂器",   "☕ 咖啡",
    "🧩 益智",   "軍事",      "歷史",
]

MAX_INTERESTS = 6   # 興趣最多可選幾項

# ── 全域字型（微軟正黑體） ──────────────────────────────────────────────────────
FONT_FAMILY = "Microsoft JhengHei"

# ── 樣式表 ─────────────────────────────────────────────────────────────────────
_STYLE = f"""
* {{
    font-family: "{FONT_FAMILY}", "微軟正黑體", sans-serif;
}}
QWizard, QWizardPage, QWidget {{
    background-color: #1e1e2e;
    color: #cdd6f4;
}}
QLabel {{
    color: #cdd6f4;
    font-size: 13px;
    background-color: transparent;
}}
QLabel#page_title {{
    font-size: 18px;
    font-weight: bold;
    color: #89b4fa;
}}
QLabel#page_desc {{
    color: #a6adc8;
    font-size: 12px;
    line-height: 1.8;
    background-color: #181825;
    border-radius: 6px;
    padding: 8px 10px;
}}
QLabel#field_label {{
    color: #cdd6f4;
    font-size: 12px;
    font-weight: bold;
}}
QLabel#counter {{
    color: #89b4fa;
    font-size: 11px;
    font-weight: bold;
}}
QLabel#over_limit {{
    color: #f38ba8;
    font-size: 11px;
    font-weight: bold;
}}
QLineEdit {{
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #585b70;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 13px;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}}
QLineEdit:focus {{
    border: 2px solid #89b4fa;
}}
QLineEdit:disabled {{
    background-color: #27293d;
    color: #585b70;
    border-color: #313244;
}}
QLineEdit::placeholder {{
    color: #6c7086;
}}
QPushButton#chip {{
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #585b70;
    border-radius: 14px;
    font-size: 12px;
    padding: 5px 12px;
}}
QPushButton#chip:hover {{
    border-color: #89b4fa;
    color: #89b4fa;
}}
QPushButton#chip[selected=true] {{
    background-color: #1c3a6e;
    border: 2px solid #89b4fa;
    color: #cdd6f4;
    font-weight: bold;
}}
QPushButton#chip[disabled_chip=true] {{
    background-color: #181825;
    border: 1px solid #313244;
    color: #45475a;
}}
QScrollArea {{
    background-color: transparent;
    border: none;
}}
QWidget#chips_container {{
    background-color: transparent;
}}
QFrame#divider {{
    background-color: #45475a;
}}
/* QWizard 內建導覽按鈕（Next / Finish） */
QWizard QPushButton {{
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 7px;
    font-family: "{FONT_FAMILY}", "微軟正黑體", sans-serif;
    font-size: 13px;
    font-weight: bold;
    padding: 8px 20px;
    min-width: 80px;
}}
QWizard QPushButton:hover  {{ background-color: #b4d0fa; }}
QWizard QPushButton:disabled {{ background-color: #45475a; color: #6c7086; }}
"""


def _divider() -> QFrame:
    d = QFrame()
    d.setObjectName("divider")
    d.setFrameShape(QFrame.Shape.HLine)
    d.setFixedHeight(1)
    return d


# ── Page 1: 基本資料 ───────────────────────────────────────────────────────────

class PageBasicInfo(QWizardPage):
    """顯示 user_id（確認用）+ 輸入名字。"""

    def __init__(self, user_id: str):
        super().__init__()
        self.setTitle("")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 12)
        layout.setSpacing(8)

        # 標題
        title = QLabel("👤  基本資料")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # 說明
        desc = QLabel(
            "歡迎使用 ChatStar！\n"
            "以下顯示您的 User ID，請確認後輸入您想使用的名字。\n"
            "名字會顯示於 AI 分析中，方便識別您的身份。"
        )
        desc.setObjectName("page_desc")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addWidget(_divider())
        layout.addSpacing(6)

        # User ID（唯讀顯示）
        id_label = QLabel("User ID")
        id_label.setObjectName("field_label")
        layout.addWidget(id_label)

        self.id_display = QLineEdit(user_id)
        self.id_display.setReadOnly(True)
        self.id_display.setStyleSheet(
            "QLineEdit {"
            "background-color: #181825;"
            "color: #89b4fa;"
            "border: 1px solid #313244;"
            "border-radius: 8px;"
            "padding: 9px 12px;"
            "font-size: 14px;"
            "font-weight: bold;"
            f"font-family: '{FONT_FAMILY}', '微軟正黑體', sans-serif;"
            "letter-spacing: 2px;"
            "}"
        )
        layout.addWidget(self.id_display)

        id_hint = QLabel("此為您的帳號識別碼，建立後無法更改")
        id_hint.setStyleSheet("color: #6c7086; font-size: 10px;")
        layout.addWidget(id_hint)
        layout.addSpacing(10)

        # 名字
        name_label = QLabel("名字 (Username)  *")
        name_label.setObjectName("field_label")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：小明、Amy、KennyLin…")
        self.name_input.setMaxLength(50)
        self.name_input.textChanged.connect(self.completeChanged.emit)
        layout.addWidget(self.name_input)

        name_hint = QLabel("最多 50 個字元，必填")
        name_hint.setStyleSheet("color: #6c7086; font-size: 10px;")
        layout.addWidget(name_hint)

        layout.addStretch()

        self.registerField("username*", self.name_input)

    def isComplete(self) -> bool:
        return len(self.name_input.text().strip()) > 0


# ── Page 2: 興趣選擇（最多 MAX_INTERESTS 項） ──────────────────────────────────

class PageInterests(QWizardPage):
    """多選 chip 選擇興趣，最多 MAX_INTERESTS 項。"""

    def __init__(self):
        super().__init__()
        self.setTitle("")
        self.selected: set[str] = set()
        self._chips: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 12)
        layout.setSpacing(8)

        # 標題
        title = QLabel("🎯  選擇您的興趣")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # 說明
        desc = QLabel(
            "選擇 1 至 6 項您感興趣的主題。\n"
            "ChatStar 會根據這些興趣，讓 AI 更了解您的偏好，\n"
            "提供更符合您風格的回覆建議。"
        )
        desc.setObjectName("page_desc")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addWidget(_divider())

        # 計數 + 提示
        self.count_label = QLabel(f"已選 0 / {MAX_INTERESTS} 項")
        self.count_label.setObjectName("counter")
        layout.addWidget(self.count_label)

        # Chip 網格（可捲動）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container.setObjectName("chips_container")
        from PyQt6.QtWidgets import QGridLayout
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 4, 0, 4)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        cols = 4
        for i, label in enumerate(INTEREST_OPTIONS):
            btn = QPushButton(label)
            btn.setObjectName("chip")
            btn.setProperty("selected", False)
            btn.setProperty("disabled_chip", False)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, l=label, b=btn: self._toggle(l, b))
            grid.addWidget(btn, i // cols, i % cols)
            self._chips[label] = btn

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _refresh_chip_style(self, btn: QPushButton):
        """重新套用 stylesheet（Qt property 變更需要 unpolish/polish）。"""
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def _toggle(self, label: str, btn: QPushButton):
        if label in self.selected:
            # 取消選取
            self.selected.remove(label)
            btn.setProperty("selected", False)
            btn.setProperty("disabled_chip", False)
            self._refresh_chip_style(btn)
            # 解鎖所有已鎖定的 chip
            for lb, b in self._chips.items():
                if lb not in self.selected:
                    b.setProperty("disabled_chip", False)
                    b.setEnabled(True)
                    self._refresh_chip_style(b)
        else:
            if len(self.selected) >= MAX_INTERESTS:
                return  # 已達上限，忽略
            self.selected.add(label)
            btn.setProperty("selected", True)
            btn.setProperty("disabled_chip", False)
            self._refresh_chip_style(btn)
            # 若已達上限，鎖定未選的 chip
            if len(self.selected) >= MAX_INTERESTS:
                for lb, b in self._chips.items():
                    if lb not in self.selected:
                        b.setProperty("disabled_chip", True)
                        b.setEnabled(False)
                        self._refresh_chip_style(b)

        count = len(self.selected)
        self.count_label.setText(f"已選 {count} / {MAX_INTERESTS} 項")
        self.count_label.setObjectName("counter")
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        return len(self.selected) > 0

    def get_preferences(self) -> list[str]:
        """回傳純文字興趣列表（去除 emoji 前綴）。"""
        result = []
        for s in self.selected:
            parts = s.split(" ", 1)
            result.append(parts[1] if len(parts) == 2 else s)
        return result


# ── Page 3: 近期話題 ───────────────────────────────────────────────────────────

class PageTopics(QWizardPage):
    """5 個獨立輸入框讓使用者分別輸入近期話題。"""

    TOPIC_COUNT = 5

    def __init__(self):
        super().__init__()
        self.setTitle("")
        self._inputs: list[QLineEdit] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 12)
        layout.setSpacing(8)

        # 標題
        title = QLabel("💬  近期話題")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # 說明
        desc = QLabel(
            "輸入您最近感興趣或聊過的話題（至少填寫第 1 項）。\n"
            "例如：最近看的電影、追的劇、聊過的事件、計畫出遊的地方…\n"
            "AI 會參考這些資訊，讓對話更有共鳴感。"
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
            num.setStyleSheet(
                f"color: #89b4fa; font-weight: bold; font-size: 14px;"
                f"font-family: '{FONT_FAMILY}', '微軟正黑體', sans-serif;"
                "background-color: transparent;"
            )
            row.addWidget(num)

            inp = QLineEdit()
            inp.setPlaceholderText(
                "話題 1（必填）" if i == 0 else f"話題 {i + 1}（選填）"
            )
            inp.setMaxLength(100)
            inp.textChanged.connect(self.completeChanged.emit)
            row.addWidget(inp)
            layout.addLayout(row)
            self._inputs.append(inp)

        layout.addStretch()

    def isComplete(self) -> bool:
        return len(self._inputs[0].text().strip()) > 0

    def get_topics(self) -> list[str]:
        return [inp.text().strip() for inp in self._inputs if inp.text().strip()]


# ── SetupWizard 主體 ──────────────────────────────────────────────────────────

class SetupWizard(QWizard):
    """
    首次登入設置嚮導（3 頁）。

    使用：
        wizard = SetupWizard(user_id, parent)
        if wizard.exec() == QWizard.DialogCode.Accepted:
            data = wizard.collect_data()
            # data = {user_id, username, gemini_api, preferences, topics}
    """

    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id

        self.setWindowTitle(f"ChatStar — 初始設置  (ID: {user_id})")
        # ClassicStyle 在 Windows 上導覽按鈕最穩定，避免 ModernStyle 的點擊事件問題
        self.setWizardStyle(QWizard.WizardStyle.ClassicStyle)
        self.setFixedSize(580, 560)
        self.setStyleSheet(_STYLE)

        # 第一頁隱藏「上一步」按鈕（明確設定，確保行為一致）
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)

        # 按鈕文字中文化
        self.setButtonText(QWizard.WizardButton.NextButton,   "下一步 >")
        self.setButtonText(QWizard.WizardButton.BackButton,   "< 上一步")
        self.setButtonText(QWizard.WizardButton.FinishButton, "完成 ✓")
        self.setButtonText(QWizard.WizardButton.CancelButton, "取消")

        # Next / Back / Finish：可執行時統一藍色（繼承 QWizard QPushButton 樣式）
        # ─ disabled 狀態已由 stylesheet 中的 :disabled 規則處理（灰色）
        # Cancel：保持灰框樣式（獨立設定）
        cancel_style = (
            "QPushButton {"
            "background-color: transparent;"
            "color: #a6adc8;"
            "border: 1px solid #585b70;"
            "border-radius: 7px;"
            f"font-family: '{FONT_FAMILY}', '微軟正黑體', sans-serif;"
            "font-size: 13px;"
            "padding: 8px 20px;"
            "min-width: 80px;"
            "}"
            "QPushButton:hover { color: #f38ba8; border-color: #f38ba8; }"
        )
        self.button(QWizard.WizardButton.CancelButton).setStyleSheet(cancel_style)

        self.page_basic    = PageBasicInfo(user_id)
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
