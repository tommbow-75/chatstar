"""
data_manager_window.py — 資料管理視窗

提供使用者（User）與聊天對象（Buddy）的增刪改查（CRUD）功能。
資料僅包含雙方的興趣與特質，供 AI 系統產生回覆建議時參考。
透過本地 FastAPI API（http://127.0.0.1:8000）進行資料存取。
"""

import json
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QTabWidget, QDialog, QFormLayout, QLineEdit,
    QTextEdit, QLabel, QMessageBox, QComboBox, QHeaderView,
    QFrame, QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# API 基礎位址
API_BASE = "http://127.0.0.1:8000"

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
    QComboBox {
        background-color: #0f3460; color: #e0e0e0;
        border: 1px solid #2d2d5b; border-radius: 6px;
        padding: 6px 12px; min-width: 200px;
    }
    QComboBox:hover { border-color: #e94560; }
    QComboBox QAbstractItemView {
        background-color: #16213e; color: #e0e0e0;
        selection-background-color: #e94560;
    }
    QScrollBar:vertical { background: #16213e; width: 8px; border-radius: 4px; }
    QScrollBar::handle:vertical { background: #0f3460; border-radius: 4px; }
    QScrollBar::handle:vertical:hover { background: #e94560; }
"""

STYLE_DIALOG = """
    QDialog {
        background-color: #1a1a2e; color: #e0e0e0;
        font-family: 'Microsoft JhengHei UI', 'Segoe UI', Arial;
    }
    QLabel { color: #a0d8ef; font-weight: 600; }
    QLabel#hint { color: #6b7aa1; font-size: 11px; font-weight: 400; }
    QLineEdit, QTextEdit {
        background-color: #16213e; color: #e0e0e0;
        border: 1px solid #2d2d5b; border-radius: 6px;
        padding: 8px 10px; font-size: 13px;
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #e94560; }
    QPushButton {
        background-color: #0f3460; color: white;
        border: 1px solid #2d2d5b; border-radius: 6px;
        padding: 8px 20px; font-size: 13px; font-weight: 600; min-width: 80px;
    }
    QPushButton:hover { background-color: #1a3a6c; border-color: #e94560; }
    QPushButton#btn_confirm { background-color: #0d7377; border-color: #14a085; }
    QPushButton#btn_confirm:hover { background-color: #14a085; }
"""

# 預設興趣範本，方便使用者快速填入
INTERESTS_PLACEHOLDER = '''{
  "喜好": ["...", "..."],
  "個性": "...",
  "話題": ["...", "..."],
  "備註": "..."
}'''


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

def api_post(path, data):
    r = requests.post(f"{API_BASE}{path}", json=data, timeout=5)
    r.raise_for_status()
    return r.json()

def api_put(path, data):
    r = requests.put(f"{API_BASE}{path}", json=data, timeout=5)
    r.raise_for_status()
    return r.json()

def api_delete(path):
    r = requests.delete(f"{API_BASE}{path}", timeout=5)
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

def interests_summary(interests_dict) -> str:
    """將 interests dict 轉為易讀的單行摘要。"""
    if not interests_dict:
        return "（尚未設定）"
    parts = []
    for k, v in interests_dict.items():
        if isinstance(v, list):
            parts.append(f"{k}: {', '.join(str(i) for i in v)}")
        else:
            parts.append(f"{k}: {v}")
    result = " ｜ ".join(parts)
    return result[:80] + "..." if len(result) > 80 else result


# ─────────────────────────────────────────────
# 興趣編輯器元件（可重用）
# ─────────────────────────────────────────────
class InterestsEditor(QWidget):
    """
    興趣編輯器：左側 JSON 原始編輯，右側快速標籤輸入。
    """
    def __init__(self, parent=None, initial: dict = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        hint = QLabel("以 JSON 格式填寫（可直接修改下方內容）：")
        hint.setObjectName("hint")
        hint.setStyleSheet("color: #6b7aa1; font-size: 11px;")
        layout.addWidget(hint)

        self.editor = QTextEdit()
        self.editor.setMinimumHeight(130)
        self.editor.setMaximumHeight(200)
        self.editor.setPlaceholderText(INTERESTS_PLACEHOLDER)
        self.editor.setStyleSheet(
            "background-color: #16213e; color: #e0e0e0; border: 1px solid #2d2d5b;"
            "border-radius: 6px; padding: 8px; font-family: Consolas, monospace; font-size: 12px;"
        )
        if initial:
            self.editor.setPlainText(json.dumps(initial, ensure_ascii=False, indent=2))
        layout.addWidget(self.editor)

    def get_value(self) -> dict | None:
        """取得 JSON 值，格式錯誤會拋出 ValueError。"""
        text = self.editor.toPlainText().strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 格式錯誤：{e}")


# ─────────────────────────────────────────────
# 使用者對話框
# ─────────────────────────────────────────────
class UserDialog(QDialog):
    def __init__(self, parent=None, user_data: dict = None):
        super().__init__(parent)
        self.is_edit = user_data is not None
        self.setWindowTitle("編輯使用者" if self.is_edit else "新增使用者")
        self.setStyleSheet(STYLE_DIALOG)
        self.setMinimumWidth(480)
        self._build_ui(user_data or {})

    def _build_ui(self, data):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("👤 " + ("編輯使用者" if self.is_edit else "新增使用者"))
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #e94560;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # user_id
        self.input_id = QLineEdit(data.get("user_id", ""))
        if self.is_edit:
            self.input_id.setReadOnly(True)
            self.input_id.setStyleSheet("background:#0a1628; color:#6b7aa1; border:1px solid #2d2d5b; border-radius:6px; padding:8px;")
        form.addRow("使用者 ID *", self.input_id)

        # username
        self.input_name = QLineEdit(data.get("username", ""))
        self.input_name.setPlaceholderText("自己的名稱（如：小王）")
        form.addRow("顯示名稱 *", self.input_name)
        layout.addLayout(form)

        # interests
        interests_lbl = QLabel("我的興趣 / 個人特質")
        interests_lbl.setStyleSheet("color: #a0d8ef; font-weight: 600; margin-top: 4px;")
        layout.addWidget(interests_lbl)
        self.interests_editor = InterestsEditor(self, initial=data.get("interests"))
        layout.addWidget(self.interests_editor)

        # 按鈕
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
        uid = self.input_id.text().strip()
        name = self.input_name.text().strip()
        if not uid:
            show_error(self, "驗證失敗", "使用者 ID 不可為空！")
            return
        if not name:
            show_error(self, "驗證失敗", "顯示名稱不可為空！")
            return
        try:
            interests = self.interests_editor.get_value()
        except ValueError as e:
            show_error(self, "格式錯誤", str(e))
            return
        self.result_data = {"user_id": uid, "username": name, "interests": interests}
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

        # 所屬使用者（唯讀）
        lbl_user = QLabel(self.user_id)
        lbl_user.setStyleSheet("color: #a0d8ef;")
        form.addRow("所屬使用者", lbl_user)

        # buddy 名稱
        self.input_name = QLineEdit(data.get("dmbuddy", ""))
        self.input_name.setPlaceholderText("對方的名稱（如：小明）")
        form.addRow("對象名稱 *", self.input_name)
        layout.addLayout(form)

        # interests
        interests_lbl = QLabel("對方的興趣 / 個人特質")
        interests_lbl.setStyleSheet("color: #a0d8ef; font-weight: 600; margin-top: 4px;")
        layout.addWidget(interests_lbl)
        self.interests_editor = InterestsEditor(self, initial=data.get("interests"))
        layout.addWidget(self.interests_editor)

        # 按鈕
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
        try:
            interests = self.interests_editor.get_value()
        except ValueError as e:
            show_error(self, "格式錯誤", str(e))
            return
        self.result_data = {"user_id": self.user_id, "dmbuddy": name, "interests": interests}
        self.accept()

    def get_data(self) -> dict:
        return getattr(self, "result_data", {})


# ─────────────────────────────────────────────
# 使用者管理分頁
# ─────────────────────────────────────────────
class UserTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._users = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 標題與按鈕列
        header = QHBoxLayout()
        title = QLabel("👤 使用者管理")
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
        layout.addLayout(header)

        # 表格：ID、名稱、興趣摘要
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["使用者 ID", "顯示名稱", "興趣 / 個人特質"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_edit)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #6b7aa1; font-size: 11px;")
        layout.addWidget(self.status_label)

    def refresh(self):
        data = api_get("/users/")
        if data is None:
            self.status_label.setText("⚠️ 無法連線至後端 API，請確認應用程式正在運行。")
            self.status_label.setStyleSheet("color: #e94560; font-size: 11px;")
            return
        self._users = data
        self.table.setRowCount(len(data))
        for row, u in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(u.get("user_id", "")))
            self.table.setItem(row, 1, QTableWidgetItem(u.get("username", "")))
            self.table.setItem(row, 2, QTableWidgetItem(interests_summary(u.get("interests"))))
        self.status_label.setText(f"共 {len(data)} 位使用者")
        self.status_label.setStyleSheet("color: #6b7aa1; font-size: 11px;")

    def _selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._users):
            show_error(self, "未選擇", "請先在表格中選取一位使用者。")
            return None
        return self._users[row]

    def _on_add(self):
        dlg = UserDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                api_post("/users/", data)
                self.refresh()
                self._set_status(f"✅ 已新增：{data['user_id']}", ok=True)
            except Exception as e:
                show_error(self, "新增失敗", str(e))

    def _on_edit(self):
        u = self._selected()
        if u is None:
            return
        dlg = UserDialog(self, user_data=u)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            uid = data.pop("user_id")
            try:
                api_put(f"/users/{uid}", data)
                self.refresh()
                self._set_status(f"✅ 已更新：{uid}", ok=True)
            except Exception as e:
                show_error(self, "更新失敗", str(e))

    def _on_delete(self):
        u = self._selected()
        if u is None:
            return
        uid = u.get("user_id", "")
        name = u.get("username", "")
        if confirm_delete(self, f"{name}（{uid}）"):
            try:
                api_delete(f"/users/{uid}")
                self.refresh()
                self._set_status(f"🗑 已刪除：{uid}", ok=False)
            except Exception as e:
                show_error(self, "刪除失敗", str(e))

    def _set_status(self, msg, ok=True):
        color = "#0d7377" if ok else "#e94560"
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px;")


# ─────────────────────────────────────────────
# 聊天對象管理分頁
# ─────────────────────────────────────────────
class BuddyTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._buddies = []
        self._build_ui()
        self._load_users()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 使用者選擇列
        user_row = QHBoxLayout()
        user_lbl = QLabel("查看使用者：")
        user_lbl.setStyleSheet("color: #a0d8ef; font-weight: 600;")
        user_row.addWidget(user_lbl)
        self.user_combo = QComboBox()
        self.user_combo.currentIndexChanged.connect(self._refresh_buddies)
        user_row.addWidget(self.user_combo)
        user_row.addStretch()
        layout.addLayout(user_row)

        # 標題與按鈕列
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
        self.btn_refresh.clicked.connect(self._refresh_buddies)

        for btn in [self.btn_add, self.btn_edit, self.btn_delete, self.btn_refresh]:
            btn.setMinimumHeight(36)
            header.addWidget(btn)
        layout.addLayout(header)

        # 表格：ID、對象名稱、興趣摘要
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "對象名稱", "對方的興趣 / 特質"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_edit)
        layout.addWidget(self.table)

        self.status_label = QLabel("← 請先選擇使用者")
        self.status_label.setStyleSheet("color: #6b7aa1; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _load_users(self):
        self.user_combo.blockSignals(True)
        self.user_combo.clear()
        data = api_get("/users/")
        if data:
            for u in data:
                self.user_combo.addItem(f"{u['username']}（{u['user_id']}）", userData=u["user_id"])
        self.user_combo.blockSignals(False)
        if self.user_combo.count() > 0:
            self._refresh_buddies()
        else:
            self.status_label.setText("尚無使用者，請先至「使用者管理」分頁新增。")

    def _current_uid(self) -> str:
        return self.user_combo.currentData() or ""

    def _refresh_buddies(self):
        uid = self._current_uid()
        if not uid:
            return
        data = api_get(f"/buddies/users/{uid}")
        if data is None:
            self.status_label.setText("⚠️ 無法連線至後端 API。")
            self.status_label.setStyleSheet("color: #e94560; font-size: 11px;")
            return
        self._buddies = data
        self.table.setRowCount(len(data))
        for row, b in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(b.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("dmbuddy", "")))
            self.table.setItem(row, 2, QTableWidgetItem(interests_summary(b.get("interests"))))
        self.status_label.setText(f"共 {len(data)} 位聊天對象")
        self.status_label.setStyleSheet("color: #6b7aa1; font-size: 11px;")

    def _selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._buddies):
            show_error(self, "未選擇", "請先在表格中選取一位聊天對象。")
            return None
        return self._buddies[row]

    def _on_add(self):
        uid = self._current_uid()
        if not uid:
            show_error(self, "未選擇使用者", "請先在上方選擇一位使用者。")
            return
        dlg = BuddyDialog(self, user_id=uid)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                api_post("/buddies/", data)
                self._refresh_buddies()
                self._set_status(f"✅ 已新增：{data['dmbuddy']}", ok=True)
            except Exception as e:
                show_error(self, "新增失敗", str(e))

    def _on_edit(self):
        b = self._selected()
        if b is None:
            return
        dlg = BuddyDialog(self, buddy_data=b, user_id=self._current_uid())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                api_put(f"/buddies/{b['id']}", {"dmbuddy": data["dmbuddy"], "interests": data["interests"]})
                self._refresh_buddies()
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
                self._refresh_buddies()
                self._set_status(f"🗑 已刪除：{name}", ok=False)
            except Exception as e:
                show_error(self, "刪除失敗", str(e))

    def _set_status(self, msg, ok=True):
        color = "#0d7377" if ok else "#e94560"
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px;")

    def reload_users(self):
        """切換到本分頁時重新載入使用者列表。"""
        self._load_users()


# ─────────────────────────────────────────────
# 主資料管理視窗
# ─────────────────────────────────────────────
class DataManagerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 ChatStar 資料管理")
        self.setMinimumSize(820, 540)
        self.setStyleSheet(STYLE_WINDOW)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 頂部標題欄
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
        sub = QLabel("管理使用者與聊天對象的興趣資料，供 AI 產生更精準的回覆建議")
        sub.setStyleSheet("font-size: 11px; color: #a0d8ef;")
        hl.addWidget(sub)
        layout.addWidget(header)

        # 分頁
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 16, 16, 8)

        self.tabs = QTabWidget()
        self.user_tab = UserTab()
        self.buddy_tab = BuddyTab()
        self.tabs.addTab(self.user_tab, "👤  我的資料")
        self.tabs.addTab(self.buddy_tab, "💬  聊天對象")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        cl.addWidget(self.tabs)
        layout.addWidget(content)

    def _on_tab_changed(self, idx: int):
        if idx == 1:
            self.buddy_tab.reload_users()
