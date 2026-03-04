"""
data_manager_window.py — 資料管理視窗（以登入使用者為範圍）

顯示目前登入使用者的個人資料、聊天對象列表，以及 AI 累積的話題記錄。
透過本地 FastAPI API（http://127.0.0.1:8000）進行資料存取。
"""

import requests
from datetime import datetime, timezone, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QTabWidget, QDialog, QFormLayout, QLineEdit,
    QLabel, QMessageBox, QHeaderView, QSplitter,
    QFrame, QAbstractItemView, QScrollArea, QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt

# API 基礎位址
API_BASE = "http://127.0.0.1:8000"

# 台灣時區（UTC+8），使用 timedelta 避免 Windows 缺少 tzdata 的問題
_TZ_LOCAL = timezone(timedelta(hours=8))

# 全域興趣選項（與 setup_wizard 一致）
INTEREST_OPTIONS = [
    "🎵 音樂",   "🎬 電影",   "📚 讀書",   "🎮 遊戲",   "🏀 籃球",
    "⚽ 足球",   "羽毛球",    "桌球",      "🍜 美食",   "✈️ 旅遊",
    "🎨 藝術",   "📸 攝影",   "🧘 健身",   "桌遊",      "爬山",
    "💻 科技",   "🌿 自然",   "🐾 貓",     "🐾 狗",     "🎭 影劇",
    "🛒 購物",   "酒精",      "🌏 時事",   "🎸 樂器",   "☕ 咖啡",
    "🧩 益智",   "軍事",      "歷史",
]
MAX_INTERESTS = 6

# ─────────────────────────────────────────────
# 通用樣式
# ─────────────────────────────────────────────
STYLE_WINDOW = """
    QWidget {
        background-color: #1a1a2e;
        color: #e0e0e0;
        font-family: 'Microsoft JhengHei UI', 'Segoe UI', Arial;
        font-size: 13px;
    }
    QTabWidget::pane {
        border: 1px solid #2d2d5b;
        background-color: #16213e;
        border-radius: 8px;
    }
    QTabBar::tab {
        background: #0f3460;
        color: #a0aec0;
        padding: 10px 28px;
        border-radius: 6px 6px 0 0;
        font-size: 13px;
        font-weight: 500;
    }
    QTabBar::tab:selected { background: #e94560; color: white; font-weight: 700; }
    QTabBar::tab:hover:!selected { background: #1a3a6c; color: white; }
    QTableWidget {
        background-color: #16213e;
        border: 1px solid #2d2d5b;
        border-radius: 6px;
        gridline-color: #2d2d5b;
        selection-background-color: #e94560;
        alternate-background-color: #1e2a4a;
        color: #e0e0e0;
    }
    QTableWidget::item { padding: 8px; }
    QHeaderView::section {
        background-color: #0f3460;
        color: #a0d8ef;
        font-weight: 700;
        padding: 10px 8px;
        border: none;
        border-right: 1px solid #2d2d5b;
    }
    QPushButton {
        background-color: #0f3460;
        color: #e0e0e0;
        border: 1px solid #2d2d5b;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 12px;
        font-weight: 500;
    }
    QPushButton:hover { background-color: #1a3a6c; border-color: #e94560; color: white; }
    QPushButton:pressed { background-color: #e94560; }
    QPushButton#btn_add { background-color: #0d7377; border-color: #14a085; color: white; font-weight: 700; }
    QPushButton#btn_add:hover { background-color: #14a085; }
    QPushButton#btn_delete { background-color: #7b2d2d; border-color: #c0392b; color: white; }
    QPushButton#btn_delete:hover { background-color: #c0392b; }
    QPushButton#btn_sm { padding: 4px 10px; font-size: 11px; min-width: 0; }
    QPushButton#btn_sm_del { padding: 4px 10px; font-size: 11px; min-width: 0;
        background-color: #7b2d2d; border-color: #c0392b; color: white; }
    QPushButton#btn_sm_del:hover { background-color: #c0392b; }
    QScrollBar:vertical { background: #16213e; width: 8px; border-radius: 4px; }
    QScrollBar::handle:vertical { background: #0f3460; border-radius: 4px; }
    QScrollBar::handle:vertical:hover { background: #e94560; }
    QGroupBox {
        border: 1px solid #2d2d5b;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 8px;
        font-weight: 700;
        color: #a0d8ef;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }
"""

STYLE_DIALOG = """
    QDialog {
        background-color: #1a1a2e; color: #e0e0e0;
        font-family: 'Microsoft JhengHei UI', 'Segoe UI', Arial;
    }
    QLabel { color: #a0d8ef; font-weight: 600; }
    QLabel#hint { color: #6b7aa1; font-size: 11px; font-weight: 400; }
    QLineEdit {
        background-color: #16213e; color: #e0e0e0;
        border: 1px solid #2d2d5b; border-radius: 6px;
        padding: 8px 10px; font-size: 13px;
    }
    QLineEdit:focus { border-color: #e94560; }
    QPushButton {
        background-color: #0f3460; color: white;
        border: 1px solid #2d2d5b; border-radius: 6px;
        padding: 8px 20px; font-size: 13px; font-weight: 600; min-width: 80px;
    }
    QPushButton:hover { background-color: #1a3a6c; border-color: #e94560; }
    QPushButton#btn_confirm { background-color: #0d7377; border-color: #14a085; }
    QPushButton#btn_confirm:hover { background-color: #14a085; }
    QPushButton#chip {
        background-color: #1e2a4a;
        color: #a0aec0;
        border: 1px solid #2d2d5b;
        border-radius: 14px;
        font-size: 12px;
        padding: 5px 12px;
    }
    QPushButton#chip:hover { border-color: #e94560; color: #e0e0e0; }
    QPushButton#chip[selected=true] {
        background-color: #e94560;
        border: 2px solid #ff6b84;
        color: white;
        font-weight: bold;
    }
"""


# ─────────────────────────────────────────────
# 時區轉換
# ─────────────────────────────────────────────
def format_dt(dt_str: str) -> str:
    """
    將資料庫回傳的 UTC 時間字串轉為台灣時區（UTC+8）顯示格式。
    - Neon PostgreSQL 預設使用 UTC，回傳格式如 '2024-03-04T06:30:00'
    - 轉換後顯示為 '2024-03-04 14:30'（台灣時間）
    """
    if not dt_str:
        return ""
    try:
        s = dt_str.rstrip("Z")
        if "+" in s[10:]:
            dt = datetime.fromisoformat(s)
        else:
            dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
        dt_local = dt.astimezone(_TZ_LOCAL)
        return dt_local.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt_str[:16].replace("T", " ") if len(dt_str) >= 16 else dt_str


# ─────────────────────────────────────────────
# 工具函式
# ─────────────────────────────────────────────
def api_get(path):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def api_post(path, data=None, params=None):
    r = requests.post(f"{API_BASE}{path}", json=data, params=params, timeout=5)
    r.raise_for_status()
    return r.json()

def api_put(path, data):
    r = requests.put(f"{API_BASE}{path}", json=data, timeout=5)
    r.raise_for_status()
    return r.json()

def api_delete(path, params=None):
    r = requests.delete(f"{API_BASE}{path}", params=params, timeout=5)
    r.raise_for_status()
    return r.json()

def show_error(parent, title, message):
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setStyleSheet("QMessageBox{background:#1a1a2e;} QLabel{color:#e0e0e0;} QPushButton{background:#0f3460;color:white;border-radius:4px;padding:6px 14px;}")
    msg.exec()

def confirm_delete(parent, name) -> bool:
    msg = QMessageBox(parent)
    msg.setWindowTitle("確認刪除")
    msg.setText(f"確定要刪除「{name}」嗎？\n此操作無法復原。")
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg.setDefaultButton(QMessageBox.StandardButton.No)
    msg.setStyleSheet("QMessageBox{background:#1a1a2e;} QLabel{color:#ffd700;} QPushButton{background:#0f3460;color:white;border-radius:4px;padding:6px 14px;}")
    return msg.exec() == QMessageBox.StandardButton.Yes

def strip_emoji_prefix(label: str) -> str:
    parts = label.split(" ", 1)
    return parts[1] if len(parts) == 2 else label


# ─────────────────────────────────────────────
# 話題輸入對話框（新增 or 編輯）
# ─────────────────────────────────────────────
class TopicEditDialog(QDialog):
    """單行話題文字輸入框，用於新增或編輯話題。"""
    def __init__(self, parent=None, initial_text: str = "", title: str = "話題"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet(STYLE_DIALOG)
        self.setFixedWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        lbl = QLabel("話題內容：")
        layout.addWidget(lbl)

        self.input = QLineEdit(initial_text)
        self.input.setPlaceholderText("例如：最近在追的劇、計畫去旅遊的地方…")
        self.input.setMaxLength(200)
        self.input.returnPressed.connect(self._on_ok)
        layout.addWidget(self.input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("✓ 確認")
        btn_ok.setObjectName("btn_confirm")
        btn_ok.clicked.connect(self._on_ok)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _on_ok(self):
        text = self.input.text().strip()
        if not text:
            show_error(self, "驗證失敗", "話題內容不可為空！")
            return
        self.result_text = text
        self.accept()

    def get_text(self) -> str:
        return getattr(self, "result_text", "")


# ─────────────────────────────────────────────
# 興趣 Chip 選取器（可重用）
# ─────────────────────────────────────────────
class InterestChipSelector(QWidget):
    def __init__(self, parent=None, initial: list = None):
        super().__init__(parent)
        self._selected: set = set()
        self._chips: dict = {}
        self._build_ui(initial or [])

    def _build_ui(self, initial: list):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.count_label = QLabel(f"已選 0 / {MAX_INTERESTS} 項（點擊標籤切換）")
        self.count_label.setStyleSheet("color: #a0d8ef; font-size: 11px; font-weight: 600;")
        layout.addWidget(self.count_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(180)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: 1px solid #2d2d5b; border-radius: 6px; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        grid = QGridLayout(container)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        cols = 4
        for i, label in enumerate(INTEREST_OPTIONS):
            btn = QPushButton(label)
            btn.setObjectName("chip")
            btn.setProperty("selected", False)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, l=label, b=btn: self._toggle(l, b))
            grid.addWidget(btn, i // cols, i % cols)
            self._chips[label] = btn

        scroll.setWidget(container)
        layout.addWidget(scroll)

        for pref in initial:
            matched = None
            for opt in INTEREST_OPTIONS:
                if opt == pref or strip_emoji_prefix(opt) == pref:
                    matched = opt
                    break
            if matched and matched not in self._selected:
                self._selected.add(matched)
                btn = self._chips[matched]
                btn.setProperty("selected", True)
                self._refresh_chip(btn)
        self._update_count()

    def _refresh_chip(self, btn):
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def _toggle(self, label: str, btn):
        if label in self._selected:
            self._selected.remove(label)
            btn.setProperty("selected", False)
            for lb, b in self._chips.items():
                if lb not in self._selected:
                    b.setEnabled(True)
            self._refresh_chip(btn)
        else:
            if len(self._selected) >= MAX_INTERESTS:
                return
            self._selected.add(label)
            btn.setProperty("selected", True)
            self._refresh_chip(btn)
            if len(self._selected) >= MAX_INTERESTS:
                for lb, b in self._chips.items():
                    if lb not in self._selected:
                        b.setEnabled(False)
        self._update_count()

    def _update_count(self):
        n = len(self._selected)
        self.count_label.setText(f"已選 {n} / {MAX_INTERESTS} 項（點擊標籤切換）")

    def get_value(self) -> list:
        return [strip_emoji_prefix(s) for s in self._selected]


# ─────────────────────────────────────────────
# 話題記錄面板（可新增/編輯/刪除）
# ─────────────────────────────────────────────
class TopicsPanel(QGroupBox):
    """
    話題記錄面板，支援新增、編輯、刪除。
    - delete_api_path: DELETE API 路徑（加 ?topic=... query param）
    - add_api_path:    POST API 路徑（加 ?topic=... query param）
    """
    def __init__(self, title="話題記錄", parent=None,
                 delete_api_path: str = "", add_api_path: str = ""):
        super().__init__(title, parent)
        self._delete_api = delete_api_path
        self._add_api = add_api_path
        self._topics: list = []
        self._refresh_fn = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)

        # 按鈕列
        ctrl_row = QHBoxLayout()
        ctrl_row.addStretch()

        self.btn_add_topic = QPushButton("＋ 新增")
        self.btn_add_topic.setObjectName("btn_sm")
        self.btn_add_topic.setMinimumHeight(28)
        self.btn_add_topic.clicked.connect(self._on_add)
        ctrl_row.addWidget(self.btn_add_topic)

        self.btn_edit_topic = QPushButton("✏ 編輯")
        self.btn_edit_topic.setObjectName("btn_sm")
        self.btn_edit_topic.setMinimumHeight(28)
        self.btn_edit_topic.clicked.connect(self._on_edit)
        ctrl_row.addWidget(self.btn_edit_topic)

        self.btn_del_topic = QPushButton("✕ 刪除")
        self.btn_del_topic.setObjectName("btn_sm_del")
        self.btn_del_topic.setMinimumHeight(28)
        self.btn_del_topic.clicked.connect(self._on_delete)
        ctrl_row.addWidget(self.btn_del_topic)

        layout.addLayout(ctrl_row)

        # 根據是否有 API 路徑決定按鈕可用性
        self._update_btn_state()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["話題內容", "新增時間（台灣）"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(90)
        self.table.setMaximumHeight(170)
        layout.addWidget(self.table)

        self.status_label = QLabel("（尚無話題記錄）")
        self.status_label.setStyleSheet("color: #6b7aa1; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _update_btn_state(self):
        has_api = bool(self._add_api or self._delete_api)
        self.btn_add_topic.setEnabled(bool(self._add_api))
        self.btn_edit_topic.setEnabled(has_api)
        self.btn_del_topic.setEnabled(bool(self._delete_api))

    def set_apis(self, add_path: str, delete_path: str):
        """動態切換 API 路徑（供 BuddyTab 點選 buddy 後呼叫）。"""
        self._add_api = add_path
        self._delete_api = delete_path
        self._update_btn_state()

    def set_refresh_fn(self, fn):
        self._refresh_fn = fn

    def load(self, topics: list):
        self._topics = topics
        self.table.setRowCount(len(topics))
        for row, t in enumerate(topics):
            self.table.setItem(row, 0, QTableWidgetItem(t.get("topic", "")))
            self.table.setItem(row, 1, QTableWidgetItem(format_dt(t.get("created_at", ""))))
        self.status_label.setText(f"共 {len(topics)} 則話題" if topics else "（尚無話題記錄）")

    def _do_refresh(self):
        if self._refresh_fn:
            topics = self._refresh_fn() or []
            self.load(topics)

    def _selected_topic(self, silent=False) -> str | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._topics):
            if not silent:
                show_error(self, "未選擇", "請先在列表中選取一則話題。")
            return None
        return self._topics[row].get("topic", "")

    def _on_add(self):
        dlg = TopicEditDialog(self, title="新增話題")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        topic = dlg.get_text()
        try:
            api_post(self._add_api, params={"topic": topic})
            self._do_refresh()
            self.status_label.setText("✅ 已新增話題")
            self.status_label.setStyleSheet("color: #0d7377; font-size: 11px;")
        except Exception as e:
            show_error(self, "新增失敗", str(e))

    def _on_edit(self):
        """編輯 = 刪除舊話題 + 新增新話題。"""
        old_topic = self._selected_topic()
        if old_topic is None:
            return
        dlg = TopicEditDialog(self, initial_text=old_topic, title="編輯話題")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_topic = dlg.get_text()
        if new_topic == old_topic:
            return
        try:
            api_delete(self._delete_api, params={"topic": old_topic})
            api_post(self._add_api, params={"topic": new_topic})
            self._do_refresh()
            self.status_label.setText("✅ 已更新話題")
            self.status_label.setStyleSheet("color: #0d7377; font-size: 11px;")
        except Exception as e:
            show_error(self, "編輯失敗", str(e))

    def _on_delete(self):
        topic = self._selected_topic()
        if topic is None:
            return
        short = topic[:30] + "..." if len(topic) > 30 else topic
        if not confirm_delete(self, short):
            return
        try:
            api_delete(self._delete_api, params={"topic": topic})
            self._do_refresh()
            self.status_label.setText("🗑 已刪除話題")
            self.status_label.setStyleSheet("color: #e94560; font-size: 11px;")
        except Exception as e:
            show_error(self, "刪除失敗", str(e))


# ─────────────────────────────────────────────
# 使用者資料編輯對話框（Chip 選取器版）
# ─────────────────────────────────────────────
class UserEditDialog(QDialog):
    def __init__(self, parent=None, user_data: dict = None):
        super().__init__(parent)
        self.setWindowTitle("編輯個人資料")
        self.setStyleSheet(STYLE_DIALOG)
        self.setMinimumWidth(520)
        self.setMinimumHeight(480)
        self._build_ui(user_data or {})

    def _build_ui(self, data):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title_lbl = QLabel("👤 編輯個人資料")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #e94560;")
        layout.addWidget(title_lbl)

        form = QFormLayout()
        form.setSpacing(10)
        lbl_id = QLabel(data.get("user_id", ""))
        lbl_id.setStyleSheet("color: #6b7aa1;")
        form.addRow("使用者 ID", lbl_id)
        self.input_name = QLineEdit(data.get("username", ""))
        self.input_name.setPlaceholderText("自己的名稱（如：小王）")
        form.addRow("顯示名稱 *", self.input_name)
        layout.addLayout(form)

        int_lbl = QLabel("我的興趣（最多選 6 項）")
        int_lbl.setStyleSheet("color: #a0d8ef; font-weight: 600; margin-top: 4px;")
        layout.addWidget(int_lbl)

        current_prefs = data.get("preferences") or []
        self.chip_selector = InterestChipSelector(self, initial=current_prefs)
        self.chip_selector.setStyleSheet(STYLE_DIALOG)
        layout.addWidget(self.chip_selector)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("✓ 儲存")
        btn_ok.setObjectName("btn_confirm")
        btn_ok.clicked.connect(self._on_ok)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _on_ok(self):
        name = self.input_name.text().strip()
        if not name:
            show_error(self, "驗證失敗", "顯示名稱不可為空！")
            return
        self.result_data = {"username": name, "preferences": self.chip_selector.get_value()}
        self.accept()

    def get_data(self) -> dict:
        return getattr(self, "result_data", {})


# ─────────────────────────────────────────────
# 聊天對象對話框
# ─────────────────────────────────────────────
class BuddyDialog(QDialog):
    def __init__(self, parent=None, buddy_data: dict = None, user_id: str = ""):
        super().__init__(parent)
        self.is_edit = buddy_data is not None
        self.user_id = user_id
        self.setWindowTitle("編輯聊天對象" if self.is_edit else "新增聊天對象")
        self.setStyleSheet(STYLE_DIALOG)
        self.setMinimumWidth(480)
        self._build_ui(buddy_data or {})

    def _build_ui(self, data):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("💬 " + ("編輯聊天對象" if self.is_edit else "新增聊天對象"))
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #e94560;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        self.input_name = QLineEdit(data.get("dmbuddy", ""))
        self.input_name.setPlaceholderText("對方的名稱（如：小明）")
        if self.is_edit:
            self.input_name.setReadOnly(True)
            self.input_name.setStyleSheet("background:#0a1628; color:#6b7aa1; border:1px solid #2d2d5b; border-radius:6px; padding:8px;")
        form.addRow("對象名稱 *", self.input_name)
        layout.addLayout(form)

        int_lbl = QLabel("對方的興趣 / 特質")
        int_lbl.setStyleSheet("color: #a0d8ef; font-weight: 600; margin-top: 4px;")
        layout.addWidget(int_lbl)

        hint = QLabel("用半形逗號「,」分隔多項，例如：音樂, 旅遊, 喜歡喝咖啡")
        hint.setObjectName("hint")
        hint.setStyleSheet("color: #6b7aa1; font-size: 11px;")
        layout.addWidget(hint)

        existing = data.get("interests") or {}
        if isinstance(existing, dict):
            all_vals = []
            for v in existing.values():
                if isinstance(v, list):
                    all_vals.extend([str(i) for i in v])
                else:
                    all_vals.append(str(v))
            existing_text = ", ".join(all_vals)
        elif isinstance(existing, list):
            existing_text = ", ".join(str(i) for i in existing)
        else:
            existing_text = str(existing) if existing else ""

        self.input_interests = QLineEdit(existing_text)
        self.input_interests.setPlaceholderText("音樂, 旅遊, ...")
        layout.addWidget(self.input_interests)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("✓ 儲存")
        btn_ok.setObjectName("btn_confirm")
        btn_ok.clicked.connect(self._on_ok)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _on_ok(self):
        name = self.input_name.text().strip()
        if not name:
            show_error(self, "驗證失敗", "對象名稱不可為空！")
            return
        raw = self.input_interests.text().strip()
        tags = [t.strip() for t in raw.split(",") if t.strip()] if raw else []
        # 使用 list 而非 dict，避免 psycopg2 dict adapter 問題
        interests = tags if tags else []
        self.result_data = {"user_id": self.user_id, "dmbuddy": name, "interests": interests}
        self.accept()

    def get_data(self) -> dict:
        return getattr(self, "result_data", {})


# ─────────────────────────────────────────────
# 個人資料分頁
# ─────────────────────────────────────────────
class MyProfileTab(QWidget):
    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self._user_data = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("👤 我的資料")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #a0d8ef;")
        header.addWidget(title)
        header.addStretch()
        self.btn_edit = QPushButton("✏ 編輯")
        self.btn_edit.setMinimumHeight(36)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_refresh = QPushButton("⟳ 重新整理")
        self.btn_refresh.setMinimumHeight(36)
        self.btn_refresh.clicked.connect(self.refresh)
        header.addWidget(self.btn_edit)
        header.addWidget(self.btn_refresh)
        layout.addLayout(header)

        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #16213e; border: 1px solid #2d2d5b; border-radius: 10px; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(10)

        id_row = QHBoxLayout()
        id_lbl = QLabel("使用者 ID：")
        id_lbl.setStyleSheet("color: #a0d8ef; font-weight: 600;")
        id_lbl.setFixedWidth(90)
        self.lbl_user_id = QLabel(self._user_id)
        self.lbl_user_id.setStyleSheet("color: #6b7aa1;")
        id_row.addWidget(id_lbl)
        id_row.addWidget(self.lbl_user_id)
        id_row.addStretch()
        card_layout.addLayout(id_row)

        name_row = QHBoxLayout()
        name_lbl = QLabel("顯示名稱：")
        name_lbl.setStyleSheet("color: #a0d8ef; font-weight: 600;")
        name_lbl.setFixedWidth(90)
        self.lbl_username = QLabel("載入中...")
        self.lbl_username.setStyleSheet("color: #e0e0e0; font-size: 14px; font-weight: 700;")
        name_row.addWidget(name_lbl)
        name_row.addWidget(self.lbl_username)
        name_row.addStretch()
        card_layout.addLayout(name_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2d2d5b;")
        card_layout.addWidget(sep)

        int_header = QLabel("興趣標籤：")
        int_header.setStyleSheet("color: #a0d8ef; font-weight: 600;")
        card_layout.addWidget(int_header)

        self.tags_container = QWidget()
        self.tags_container.setStyleSheet("background: transparent;")
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(6)
        self.tags_layout.addWidget(QLabel("（尚未設定）"))
        self.tags_layout.addStretch()
        card_layout.addWidget(self.tags_container)
        layout.addWidget(card)

        # 個人話題面板（可新增/編輯/刪除）
        add_path = f"/topics/users/{self._user_id}/topic"
        del_path = f"/topics/users/{self._user_id}/topic"
        self.topics_panel = TopicsPanel(
            "🏷 個人話題記錄",
            add_api_path=add_path,
            delete_api_path=del_path,
        )
        self.topics_panel.set_refresh_fn(lambda: api_get(f"/topics/users/{self._user_id}") or [])
        layout.addWidget(self.topics_panel)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #6b7aa1; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _render_tags(self, preferences: list):
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if preferences:
            for tag in preferences:
                lbl = QLabel(tag)
                lbl.setStyleSheet(
                    "background-color: #1c3a6e; color: #a0d8ef; border: 1px solid #2d5b9e;"
                    "border-radius: 10px; padding: 3px 10px; font-size: 12px;"
                )
                self.tags_layout.addWidget(lbl)
        else:
            self.tags_layout.addWidget(QLabel("（尚未設定）"))
        self.tags_layout.addStretch()

    def refresh(self):
        data = api_get(f"/users/{self._user_id}")
        if data is None:
            self.status_label.setText("⚠️ 無法連線至後端 API，請確認應用程式正在運行。")
            self.status_label.setStyleSheet("color: #e94560; font-size: 11px;")
            return
        self._user_data = data
        self.lbl_username.setText(data.get("username", ""))
        prefs = data.get("preferences") or []
        self._render_tags(prefs)
        self.status_label.setText("")
        topics = api_get(f"/topics/users/{self._user_id}") or []
        self.topics_panel.load(topics)

    def _on_edit(self):
        dlg = UserEditDialog(self, user_data=self._user_data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                api_put(f"/users/{self._user_id}", data)
                self.refresh()
                self.status_label.setText("✅ 個人資料已更新")
                self.status_label.setStyleSheet("color: #0d7377; font-size: 11px;")
            except Exception as e:
                show_error(self, "更新失敗", str(e))


# ─────────────────────────────────────────────
# 聊天對象管理分頁
# ─────────────────────────────────────────────
class BuddyTab(QWidget):
    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self._buddies = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("💬 聊天對象管理")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #a0d8ef;")
        header.addWidget(title)
        header.addStretch()

        self.btn_add = QPushButton("＋ 新增")
        self.btn_add.setObjectName("btn_add")
        self.btn_edit = QPushButton("✏ 編輯")
        self.btn_delete = QPushButton("✕ 刪除")
        self.btn_delete.setObjectName("btn_delete")
        self.btn_refresh = QPushButton("⟳ 重新整理")

        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_refresh.clicked.connect(self.refresh)

        for btn in [self.btn_add, self.btn_edit, self.btn_delete, self.btn_refresh]:
            btn.setMinimumHeight(36)
            header.addWidget(btn)
        main_layout.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background: #2d2d5b; }")

        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(4)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "對象名稱", "興趣標籤"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_edit)
        self.table.clicked.connect(self._on_table_clicked)
        table_layout.addWidget(self.table)

        self.status_label = QLabel("載入中...")
        self.status_label.setStyleSheet("color: #6b7aa1; font-size: 11px;")
        table_layout.addWidget(self.status_label)
        splitter.addWidget(table_widget)

        # 話題面板（初始無 API，點選 buddy 後動態設定）
        self.topics_panel = TopicsPanel("🏷 聊天話題記錄（點選上方的聊天對象以載入）")
        splitter.addWidget(self.topics_panel)

        splitter.setSizes([300, 240])
        main_layout.addWidget(splitter)

    def _interests_text(self, interests) -> str:
        if not interests:
            return "（尚未設定）"
        if isinstance(interests, list):
            return ", ".join(str(i) for i in interests)
        if isinstance(interests, dict):
            all_vals = []
            for v in interests.values():
                if isinstance(v, list):
                    all_vals.extend([str(i) for i in v])
                else:
                    all_vals.append(str(v))
            return ", ".join(all_vals)
        return str(interests)

    def refresh(self):
        data = api_get(f"/buddies/users/{self._user_id}")
        if data is None:
            self.status_label.setText("⚠️ 無法連線至後端 API。")
            self.status_label.setStyleSheet("color: #e94560; font-size: 11px;")
            return
        self._buddies = data
        self.table.setRowCount(len(data))
        for row, b in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(b.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("dmbuddy", "")))
            self.table.setItem(row, 2, QTableWidgetItem(self._interests_text(b.get("interests"))))
        count = len(data)
        self.status_label.setText(f"共 {count} 位聊天對象" if count else "尚無聊天對象，點擊「＋ 新增」來添加。")
        self.status_label.setStyleSheet("color: #6b7aa1; font-size: 11px;")
        # 清空話題面板，回到無 API 狀態
        self.topics_panel.set_apis("", "")
        self.topics_panel.set_refresh_fn(None)
        self.topics_panel.load([])
        self.topics_panel.setTitle("🏷 聊天話題記錄（點選上方的聊天對象以載入）")

    def _on_table_clicked(self):
        b = self._selected(silent=True)
        if b is None:
            return
        dmbuddy = b.get("dmbuddy", "")
        uid = self._user_id

        add_path = f"/topics/users/{uid}/buddies/{dmbuddy}/topic"
        del_path = f"/topics/users/{uid}/buddies/{dmbuddy}/topic"
        self.topics_panel.set_apis(add_path, del_path)
        self.topics_panel.set_refresh_fn(
            lambda d=dmbuddy: api_get(f"/topics/users/{uid}/buddies/{d}") or []
        )
        self.topics_panel.setTitle(f"🏷 與「{dmbuddy}」的聊天話題記錄")
        topics = api_get(f"/topics/users/{uid}/buddies/{dmbuddy}") or []
        self.topics_panel.load(topics)

    def _selected(self, silent=False):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._buddies):
            if not silent:
                show_error(self, "未選擇", "請先在表格中選取一位聊天對象。")
            return None
        return self._buddies[row]

    def _on_add(self):
        dlg = BuddyDialog(self, user_id=self._user_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                api_post("/buddies/", data=data)
                self.refresh()
                self._set_status(f"✅ 已新增：{data['dmbuddy']}", ok=True)
            except Exception as e:
                show_error(self, "新增失敗", str(e))

    def _on_edit(self):
        b = self._selected()
        if b is None:
            return
        dlg = BuddyDialog(self, buddy_data=b, user_id=self._user_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                api_put(f"/buddies/{b['id']}", {"dmbuddy": data["dmbuddy"], "interests": data["interests"]})
                self.refresh()
                self._set_status(f"✅ 已更新：{data['dmbuddy']}", ok=True)
            except Exception as e:
                show_error(self, "更新失敗", str(e))

    def _on_delete(self):
        b = self._selected()
        if b is None:
            return
        name = b.get("dmbuddy", "")
        if confirm_delete(self, name):
            try:
                api_delete(f"/buddies/{b['id']}")
                self.refresh()
                self._set_status(f"🗑 已刪除：{name}", ok=False)
            except Exception as e:
                show_error(self, "刪除失敗", str(e))

    def _set_status(self, msg, ok=True):
        color = "#0d7377" if ok else "#e94560"
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px;")


# ─────────────────────────────────────────────
# 主資料管理視窗
# ─────────────────────────────────────────────
class DataManagerWindow(QWidget):
    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self.setWindowTitle("📊 ChatStar 資料管理")
        self.setMinimumSize(840, 600)
        self.setStyleSheet(STYLE_WINDOW)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0f3460, stop:1 #1a1a2e);
                border-bottom: 2px solid #e94560;
            }
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)
        title_lbl = QLabel("📊  ChatStar 資料管理")
        title_lbl.setStyleSheet("font-size: 17px; font-weight: 700; color: white; letter-spacing: 1px;")
        hl.addWidget(title_lbl)
        hl.addStretch()
        user_lbl = QLabel(f"👤  {self._user_id}")
        user_lbl.setStyleSheet(
            "font-size: 12px; color: #a0d8ef; padding: 4px 10px; "
            "background: rgba(14,52,96,0.6); border-radius: 12px; border: 1px solid #2d2d5b;"
        )
        hl.addWidget(user_lbl)
        layout.addWidget(header)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 16, 16, 8)

        self.tabs = QTabWidget()
        self.profile_tab = MyProfileTab(user_id=self._user_id)
        self.buddy_tab = BuddyTab(user_id=self._user_id)
        self.tabs.addTab(self.profile_tab, "👤  我的資料")
        self.tabs.addTab(self.buddy_tab, "💬  聊天對象")
        cl.addWidget(self.tabs)
        layout.addWidget(content)
