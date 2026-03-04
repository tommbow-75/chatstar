import sys
import os
from PyQt6.QtWidgets import QApplication
from dotenv import load_dotenv

from ui.main_window import MainWindow
from ui.selection_window import SelectionWindow
from ui.region_overlay import RegionOverlay
from core.ai_provider import GeminiProvider
from core.scanner import ScreenScanner
from core.memory_manager import MemoryManager
from core.backend_thread import BackendThread

load_dotenv()  # 讀取 .env 中的 GEMINI_API_KEY

# 保持全域參考，避免被 GC 回收
app = None
main_win = None
selection_win = None
scanner = None
region_overlay = None   # 螢幕上的藍色框線
memory_manager = None   # 工作記憶
backend_thread = None   # FastAPI 後端伺服器執行緒

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


def main():
    global app, main_win
    print("啟動 AI Chat Assistant (Gemini Vision + 工作記憶模式)...")
    app = QApplication(sys.argv)
    
    # 啟動 FastAPI 伺服器
    start_backend()

    main_win = MainWindow()

    # 若 .env 中有 API Key，自動填入欄位
    env_key = os.getenv("GEMINI_API_KEY", "")
    if env_key:
        main_win.api_key_input.setText(env_key)
        print("已從 .env 讀到 Gemini API Key")

    main_win.start_selection.connect(start_selection)
    main_win.stop_scanner.connect(on_stop_scanner)
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
