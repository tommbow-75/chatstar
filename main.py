import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from dotenv import load_dotenv

from ui.main_window import MainWindow
from ui.selection_window import SelectionWindow
from ui.region_overlay import RegionOverlay
from ui.data_manager_window import DataManagerWindow
from ui.login_dialog import LoginDialog
from ui.setup_wizard import SetupWizard
from core.ai_provider import GeminiProvider
from core.scanner import ScreenScanner
from core.memory_manager import MemoryManager
from core.backend_thread import BackendThread
from backend.database import SessionLocal
from backend.crud import get_user
from backend.crud_setup import create_user_with_setup

load_dotenv()  # 讀取 .env 中的 GEMINI_API_KEY

# 保持全域參考，避免被 GC 回收
app = None
main_win = None
selection_win = None
scanner = None
region_overlay = None   # 螢幕上的藍色框線
memory_manager = None   # 工作記憶
backend_thread = None   # FastAPI 後端伺服器執行緒
data_manager_win = None  # 資料管理視窗

def start_backend():
    """啟動 FastAPI 背景伺服器"""
    global backend_thread
    if backend_thread is None:
        backend_thread = BackendThread(host="127.0.0.1", port=8000)
        backend_thread.started_signal.connect(lambda: print("🌟 FastAPI 後端伺服器已在 http://127.0.0.1:8000 啟動"))
        backend_thread.start()


def start_selection():
    """由主視窗按鈕觸發：先停止舊掃描，再開啟選取視窗。"""
    global selection_win
    _stop_scanner()  # 重新框選時先停止舊的掃描
    selection_win = SelectionWindow()
    selection_win.region_selected.connect(on_region_selected)
    selection_win.showFullScreen()


def on_region_selected(region):
    """使用者完成選取後，顯示框線、初始化 AI 與記憶、啟動掃描。"""
    global scanner, region_overlay, memory_manager

    # 更新螢幕上的區域框線
    if region_overlay is not None:
        region_overlay.close()
    region_overlay = RegionOverlay(region)

    api_key = main_win.get_api_key()
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        main_win.set_status("⚠️ 找不到 Gemini API Key，請在輸入欄中填入")
        main_win._on_stop_clicked()
        return

    try:
        ai_provider = GeminiProvider(api_key=api_key)
    except Exception as e:
        main_win.set_status(f"⚠️ AI 初始化失敗：{e}")
        main_win._on_stop_clicked()
        return

    # 重置工作記憶（每次重新框選都清空舊記憶）
    if memory_manager is None:
        memory_manager = MemoryManager(max_window=8)
    else:
        memory_manager.reset()

    main_win.set_scanning(region)

    scanner = ScreenScanner(
        region=region,
        ai_provider=ai_provider,
        memory_manager=memory_manager,
        interval=2.0,
    )
    scanner.replies_ready.connect(main_win.update_replies)
    scanner.status_update.connect(main_win.set_status)
    scanner.start()


def _stop_scanner():
    """停止背景掃描與螢幕框線。"""
    global scanner, region_overlay
    if scanner and scanner.isRunning():
        scanner.stop()
        scanner = None
    if region_overlay is not None:
        region_overlay.close()
        region_overlay = None


def on_stop_scanner():
    """由停止按鈕觸發。"""
    _stop_scanner()


def open_data_manager(user_id: str = ""):
    """開啟資料管理視窗（若已開啟則喚起到前景）。"""
    global data_manager_win
    if data_manager_win is None or not data_manager_win.isVisible():
        data_manager_win = DataManagerWindow(user_id=user_id)
        data_manager_win.show()
    else:
        data_manager_win.raise_()
        data_manager_win.activateWindow()


def main():
    global app, main_win
    print("啟動 AI Chat Assistant (Gemini Vision + 工作記憶模式)...")
    app = QApplication(sys.argv)

    # ── 啟動 FastAPI 伺服器 ──
    start_backend()

    # ─────────────────────────────────────────────────────────────────
    # 登入迴圈：LoginDialog → DB 查詢 → (新用戶) SetupWizard
    # 嚮導任一頁按「取消」→ continue 回到 LoginDialog
    # LoginDialog 按「取消」→ 結束程式
    # ─────────────────────────────────────────────────────────────────
    while True:
        # Step 1: 登入對話框
        login = LoginDialog()
        if login.exec() != LoginDialog.DialogCode.Accepted:
            print("使用者取消登入，結束程式。")
            sys.exit(0)

        current_user_id = login.user_id
        print(f"登入 user_id: {current_user_id}")

        # Step 2: 查詢資料庫
        db = SessionLocal()
        try:
            user = get_user(db, current_user_id)
        except Exception as e:
            import traceback
            print(f"[DB ERROR]\n{traceback.format_exc()}")
            QMessageBox.critical(
                None,
                "資料庫連線失敗",
                f"錯誤類型：{type(e).__name__}\n\n{e}\n\n"
                "請確認：\n"
                "1. .env 中的 DATABASE_URL 已正確設定\n"
                "2. 網路可連線到資料庫伺服器"
            )
            db.close()
            sys.exit(1)

        if user is None:
            # 新使用者 → 開啟設置嚮導
            print(f"user_id '{current_user_id}' 不存在，啟動初始設置嚮導...")
            wizard = SetupWizard(current_user_id)
            if wizard.exec() != SetupWizard.DialogCode.Accepted:
                # 任一頁按「取消」→ 回到登入畫面
                print("使用者取消設置，回到登入畫面。")
                db.close()
                continue

            data = wizard.collect_data()
            try:
                create_user_with_setup(
                    db=db,
                    user_id=data["user_id"],
                    username=data["username"],
                    preferences=data["preferences"],
                    topics=data["topics"],
                )
                print(f"✅ 使用者 '{current_user_id}' 已建立：{data['username']}")
            except Exception as e:
                QMessageBox.critical(None, "儲存失敗", f"無法儲存使用者資料：\n{e}")
                db.close()
                sys.exit(1)
        else:
            print(f"✅ 已找到使用者：{user.username} (id={current_user_id})")

        db.close()
        break  # 登入 / 設置完成，進入主視窗


    # ──────────────────────────────────────────────────
    # Step 3: 開啟主視窗
    # ──────────────────────────────────────────────────
    main_win = MainWindow()

    # 自動從 .env 填入 Gemini API Key
    env_key = os.getenv("GEMINI_API_KEY", "")
    if env_key:
        main_win.api_key_input.setText(env_key)
        print("已從 .env 讀到 Gemini API Key")

    main_win.start_selection.connect(start_selection)
    main_win.stop_scanner.connect(on_stop_scanner)
    main_win.open_data_manager.connect(lambda: open_data_manager(current_user_id))
    main_win.show()

    # 執行事件迴圈
    exit_code = app.exec()

    # 關閉視窗後，停止背景的 FastAPI 伺服器
    global backend_thread
    if backend_thread:
        print("正在關閉 FastAPI 後端伺服器...")
        backend_thread.stop()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
