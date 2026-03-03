import sys
import os
from PyQt6.QtWidgets import QApplication
from dotenv import load_dotenv

from ui.main_window import MainWindow
from ui.selection_window import SelectionWindow
from ui.region_overlay import RegionOverlay
from core.ai_provider import GeminiProvider
from core.scanner import ScreenScanner

load_dotenv()  # 讀取 .env 中的 GEMINI_API_KEY

# 保持全域參考，避免被 GC 回收
app = None
main_win = None
selection_win = None
scanner = None
region_overlay = None   # 螢幕上的藍色框線


def start_selection():
    """由主視窗按鈕觸發：先停止舊掃描，再開啟選取視窗。"""
    global selection_win
    _stop_scanner()  # 重新框選時先停止舊的掃描
    selection_win = SelectionWindow()
    selection_win.region_selected.connect(on_region_selected)
    selection_win.showFullScreen()


def on_region_selected(region):
    """使用者完成選取後，顯示框線、初始化 AI、啟動掃描。"""
    global scanner, region_overlay

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

    main_win.set_scanning(region)

    scanner = ScreenScanner(region=region, ai_provider=ai_provider, interval=2.0)
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
    print("啟動 AI Chat Assistant (Gemini Vision 模式)...")
    app = QApplication(sys.argv)

    main_win = MainWindow()

    # 若 .env 中有 API Key，自動填入欄位
    env_key = os.getenv("GEMINI_API_KEY", "")
    if env_key:
        main_win.api_key_input.setText(env_key)
        print("已從 .env 讀到 Gemini API Key")

    main_win.start_selection.connect(start_selection)
    main_win.stop_scanner.connect(on_stop_scanner)
    main_win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
