import mss
import time
import io
from PIL import Image, ImageChops
from PyQt6.QtCore import QThread, pyqtSignal
from .ai_provider import BaseAIProvider

def _images_differ(img1: Image.Image, img2: Image.Image, threshold: float = 0.5) -> bool:
    """
    比較兩張圖片的差異率（百分比）。
    threshold: 超過此比例的像素有變化，就視為有新訊息（預設 0.5%）
    """
    if img1.size != img2.size:
        return True
    diff = ImageChops.difference(img1.convert("RGB"), img2.convert("RGB"))
    total_pixels = img1.width * img1.height
    changed = sum(1 for r, g, b in diff.getdata() if r + g + b > 30)
    return (changed / total_pixels) * 100 > threshold


class ScreenScanner(QThread):
    replies_ready = pyqtSignal(list)   # payload: List[str]，3 種回覆建議
    status_update = pyqtSignal(str)    # 狀態訊息給 UI

    def __init__(self, region: dict, ai_provider: BaseAIProvider, interval: float = 2.0):
        """
        region 格式: {'top': y, 'left': x, 'width': w, 'height': h}
        """
        super().__init__()
        self.region = region
        self.ai_provider = ai_provider
        self.interval = interval
        self.running = True
        self.last_image: Image.Image | None = None

    def _capture(self, sct) -> Image.Image:
        sct_img = sct.grab(self.region)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    def run(self):
        print(f"開始監聽區域: {self.region}")
        self.status_update.emit("監聽中，等待對話變化...")

        with mss.mss() as sct:
            first_run = True
            while self.running:
                try:
                    current_img = self._capture(sct)

                    if first_run:
                        # 第一次截圖，直接送 AI 分析（不需要等變動）
                        first_run = False
                        self.last_image = current_img
                        self.status_update.emit("初始掃描中，正在分析當前對話...")
                        print("首次框選，立即送圖給 Gemini...")
                        replies = self.ai_provider.analyze_chat_image(current_img)
                        self.replies_ready.emit(replies)
                        self.status_update.emit("✅ 初始分析完成，持續監聽中...")

                    elif _images_differ(self.last_image, current_img):
                        # 畫面有變化 → 送給 AI 分析
                        self.last_image = current_img
                        self.status_update.emit("偵測到對話變化，正在分析中...")
                        print("畫面有變化，送圖給 Gemini...")
                        replies = self.ai_provider.analyze_chat_image(current_img)
                        self.replies_ready.emit(replies)
                        self.status_update.emit("✅ 分析完成！監聽中...")

                except Exception as e:
                    err_msg = str(e)
                    print(f"Scanner Error: {err_msg}")
                    self.status_update.emit(f"⚠️ 錯誤：{err_msg[:80]}")

                time.sleep(self.interval)


    def stop(self):
        self.running = False
        self.wait()
