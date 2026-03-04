import mss
import time
import io
from PIL import Image, ImageChops
from PyQt6.QtCore import QThread, pyqtSignal
from .ai_provider import BaseAIProvider
from .memory_manager import MemoryManager

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

    def __init__(
        self,
        region: dict,
        ai_provider: BaseAIProvider,
        memory_manager: MemoryManager,
        interval: float = 2.0,
        user_id: str = "",
        partner_name: str = "",
    ):
        """
        Parameters
        ----------
        region : dict
            截圖區域，格式: {'top': y, 'left': x, 'width': w, 'height': h}
        user_id : str
            目前登入的使用者 ID（用於 Pinecone 長期記憶查詢）。
        partner_name : str
            當前選取的聊天對象名稱（用於 Pinecone 長期記憶查詢）。
        """
        super().__init__()
        self.region = region
        self.ai_provider = ai_provider
        self.memory = memory_manager
        self.interval = interval
        self.running = True
        self.last_image: Image.Image | None = None
        self.user_id = user_id
        self.partner_name = partner_name

    def _capture(self, sct) -> Image.Image:
        sct_img = sct.grab(self.region)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    def _get_long_term_context(self, query: str) -> str:
        """
        向 Pinecone 查詢與當前對話最相關的長期記憶。
        若未設定 user_id / partner_name，或查詢失敗，回傳空字串。
        """
        if not self.user_id or not self.partner_name:
            return ""
        try:
            from vector_db.search_service import search_long_term_context
            return search_long_term_context(
                user_id=self.user_id,
                partner_name=self.partner_name,
                query=query,
                top_k=5,
            )
        except Exception as e:
            print(f"[長期記憶] Pinecone 查詢失敗（不影響主流程）: {e}")
            return ""

    def run(self):
        print(f"開始監聽區域: {self.region}")
        if self.partner_name:
            print(f"[長期記憶] 啟用 - user={self.user_id}, partner={self.partner_name}")
        self.status_update.emit("監聽中，等待對話變化...")

        with mss.mss() as sct:
            first_run = True
            while self.running:
                try:
                    current_img = self._capture(sct)

                    if first_run:
                        # ── 首次截圖：全量提取 + 填充 memory ──
                        first_run = False
                        self.last_image = current_img
                        self.status_update.emit("初始掃描中，正在提取完整對話...")
                        print("首次框選，進行全量提取...")

                        messages = self.ai_provider.extract_all_messages(current_img)
                        self.memory.add_messages(messages)

                        # 用全量 context 生成建議，同時查詢 Pinecone 長期記憶
                        self.status_update.emit("初始分析中，正在生成建議...")
                        context = self.memory.get_context_prompt()
                        # 用最新一則訊息作為 Pinecone 查詢語句（若有）
                        query_text = messages[0] if messages else "聊天對話"
                        long_term = self._get_long_term_context(query_text)
                        replies = self.ai_provider.analyze_chat_image(
                            current_img, context, long_term_context=long_term
                        )
                        self.replies_ready.emit(replies)
                        self.status_update.emit("✅ 初始分析完成，持續監聽中...")

                    elif _images_differ(self.last_image, current_img):
                        # ── 後續截圖：增量提取 + 去重 append ──
                        self.last_image = current_img
                        self.status_update.emit("偵測到對話變化，正在提取新訊息...")
                        print("畫面有變化，進行增量提取...")

                        latest = self.ai_provider.extract_latest_message(current_img)
                        is_new = self.memory.add_latest(latest)

                        if is_new:
                            self.status_update.emit("新訊息已加入記憶，正在生成建議...")
                        else:
                            self.status_update.emit("畫面有小幅變化，重新生成建議...")

                        # 用最新訊息查詢 Pinecone，取得長期記憶補充
                        context = self.memory.get_context_prompt()
                        long_term = self._get_long_term_context(latest or "聊天對話")
                        replies = self.ai_provider.analyze_chat_image(
                            current_img, context, long_term_context=long_term
                        )
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
